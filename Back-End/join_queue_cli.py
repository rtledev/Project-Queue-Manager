"""
join_queue_cli.py

Terminal-based interface for joining the Ps & Qs meeting queue.

This file connects:
    - the student database (students.db)
    - the queue manager (Priority_Queue.py)

Flow:
    1. Student enters CWID
    2. System validates that CWID exists in the database
    3. If first-time student, prompt for profile info and store it
    4. If returning student, verify school email
    5. Prompt for meeting topic
    6. Create a MeetingRequest
    7. Add the request to the queue
    8. Show queue position

- Loads SMTP values from .env through notification_service.py
- Supports multiple queues / professors
- Supports active office-hours sessions
- Uses one PersistentMeetingQueueManager per queue/session
- Adds persistent professor notes
- Adds queue reset per session
- Queues join/near-front/now-serving/reminder emails
- Starts a background email worker
"""
# loads environment variables form .env into the preocss environment during local development.
# from dotenv import load_dotenv

# after this runs, os.getenv("SMTP_HOST"), etc. can read values from .env
# load_dotenv()

from datetime import datetime, timedelta
from typing import Optional, Tuple

# Import the queue engine pieces.
from Priority_Queue import MeetingQueueManager, MeetingRequest, AlreadyWaitingError
from persistent_queue_manager import PersistMeetingQueueManager

# Import database helper functions.
from student_db import (
    create_students_table,
    cwid_exists,
    get_student_by_cwid,
    profile_is_complete,
    school_email_matches_cwid,
    update_student_info,
)
from queue_db import (
    initialize_queue_storage,
    seed_default_queues_if_empty,
    list_active_queues,
    get_active_session_for_queue,
    create_session,
    end_session,
)
from notification_service import (
    EmailNotifier,
    start_email_worker,
)


def is_valid_email(email: str) -> bool:
    """
    Very basic email validation.

    For now, we only check that:
        - it contains '@'
        - it contains '.'

    Later this could be replaced with stronger validation or regex.
    """
    return "@" in email and "." in email


def is_valid_phone(phone: str) -> bool:
    """
    Basic phone validation for the format:
        +1(###)-###-####

    Since you said phone is optional and not needed right now,
    this is included mainly as a placeholder for future use.
    """

    # Blank is allowed because phone number is optional for now.
    if phone == "":
        return True

    # Very simple exact-length pattern check.
    # Example valid format: +1(555)-123-4567
    if len(phone) != 16:
        return False

    # Check exact symbol positions.
    if phone[0:3] != "+1(":
        return False
    if phone[6:8] != ")-":
        return False
    if phone[11] != "-":
        return False

    # Extract the numeric pieces and ensure they are digits.
    area = phone[3:6]
    first = phone[8:11]
    second = phone[12:16]

    return area.isdigit() and first.isdigit() and second.isdigit()


def prompt_non_empty(prompt_text: str) -> str:
    """
    Repeatedly prompts until the user enters a non-empty string.
    """
    while True:
        value = input(prompt_text).strip()
        if value != "":
            return value
        print("This field cannot be blank. Please try again.")


def prompt_optional(prompt_text: str) -> str:
    """
    Prompts once and returns the stripped value.
    Blank input is allowed.
    """
    return input(prompt_text).strip()


def prompt_yes_no(prompt_text: str) -> bool:
    """
    Prompts for yes/no input and returns True/False.
    """
    while True:
        value = input(prompt_text).strip().lower()

        if value in ("yes", "y"):
            return True
        if value in ("no", "n"):
            return False

        print("Please enter yes or no.")


def prompt_email(prompt_text: str) -> str:
    """
    Repeatedly prompts until a valid-looking email is entered.
    """
    while True:
        email = input(prompt_text).strip().lower()
        if is_valid_email(email):
            return email
        print("Invalid email format. Please include '@' and '.'")


def prompt_phone_optional(prompt_text: str) -> str:
    """
    Prompts for an optional phone number.

    Accepts:
        - blank
        - +1(###)-###-####
    """
    while True:
        phone = input(prompt_text).strip()
        if is_valid_phone(phone):
            return phone
        print("Invalid phone format. Use +1(###)-###-#### or leave blank.")


def prompt_dsl_status() -> bool:
    """
    Prompts the user for DSL status.

    Note:
        In a real system, this should ideally come from an official
        verified source rather than self-entry.
        For your current project phase, user entry is acceptable.
    """
    while True:
        value = input("Are you a DSL student? (true/false): ").strip().lower()

        if value in ("true", "t", "yes", "y", "1"):
            return True
        if value in ("false", "f", "no", "n", "0"):
            return False

        print("Please enter true or false.")


def build_full_name(first_name: str, middle_initial: str, last_name: str) -> str:
    """
    Builds a clean display name.

    If middle initial exists:
        First M Last
    Otherwise:
        First Last
    """
    if middle_initial.strip():
        return f"{first_name} {middle_initial} {last_name}"
    return f"{first_name} {last_name}"

# -------------------------------------------------------------------
# Queue/session selection helpers
# -------------------------------------------------------------------

def select_active_queue() -> Optional[dict]:
    """
    Displays all active queues and lets the user choose one.

    Returns:
        queue dictionary if selected
        None if the user cancels or no queues exist
    """
    queues = list_active_queues()

    if not queues:
        print("No active queues are available.")
        return None

    print("\nAvailable Queues:")
    for index, q in enumerate(queues, start=1):
        print(
            f"{index}. {q['queue_name']} | "
            f"{q['professor_name']} | "
            f"{q['location']}"
        )

    while True:
        choice = input("Choose a queue number (or press Enter to cancel): ").strip()

        if choice == "":
            return None

        try:
            index = int(choice)
            if 1 <= index <= len(queues):
                return queues[index - 1]
        except ValueError:
            pass

        print("Invalid choice. Please try again.")


def get_manager_for_active_session(queue_id: int) -> Optional[Tuple[dict, PersistMeetingQueueManager]]:
    """
    Gets the active session for the selected queue and returns:

        (session_dict, queue_manager)

    Why this exists:
    - each queue can have its own active office-hours session
    - each queue/session pair gets its own persistent queue manager
    """
    session = get_active_session_for_queue(queue_id)
    if session is None:
        return None

    manager = PersistMeetingQueueManager(queue_id=queue_id, session_id=session["session_id"])
    return session, manager


# -------------------------------------------------------------------
# Student profile flows
# -------------------------------------------------------------------


def first_time_setup(cwid: int) -> dict:
    """
    Handles the first-time profile completion flow for a student
    whose CWID exists but whose profile fields are still blank.

    After collecting the data, it updates the database and
    returns the completed student record.
    """

    print("\nFirst-time student setup.")
    print("Please complete your profile information.\n")

    # Collect required name fields.
    first_name = prompt_non_empty("First name: ")
    middle_initial = prompt_optional("Middle initial (leave blank if none): ")
    last_name = prompt_non_empty("Last name: ")

    # Collect and validate school email.
    school_email = prompt_email("School email: ")

    # Ask whether contact email should match school email.
    use_same_contact = prompt_yes_no(
        "Use the same email for contact/reminders? (yes/no): "
    )

    # Set contact email based on the user's choice.
    if use_same_contact:
        contact_email = school_email
    else:
        contact_email = prompt_email("Contact email: ")

    # Phone is optional for now, but we store it if provided.
    phone_number = prompt_phone_optional(
        "Phone number in format +1(###)-###-#### (optional): "
    )

    # Collect DSL status for current prototype behavior.
    dsl_status = prompt_dsl_status()

    # Save all of the entered information into the database.
    update_student_info(
        cwid=cwid,
        first_name=first_name,
        middle_initial=middle_initial,
        last_name=last_name,
        school_email=school_email,
        contact_email=contact_email,
        phone_number=phone_number,
        dsl_status=dsl_status,
    )

    # return updated recird from the database to ensure we have the latest info.
    updated_student = get_student_by_cwid(cwid)

    # Should exist if the update was successful, but we can add a fallback just in case.
    if updated_student is None:
        raise Exception("Unexpected error: Student record not found after update.")
    
    return updated_student

def returning_student_flow(student: dict) -> bool:
    """
    Handles the flow for a returning student whose profile is complete.

    Verifies that the school email they enter matches the one on file.

    Returns True if verification is successful, False otherwise.
    """
    print("\nWelcome back! Please verify your identity.")

    # Prompt for school email and verify it matches the database record.
    entered_email = prompt_email("Enter your school email for verification: ")

    if school_email_matches_cwid(entered_email, student["cwid"] ):
        print("Email verified successfully.")
        return True
    else:
        print("Email verification failed. The entered email does not match our records.")
        return False

# -------------------------------------------------------------------
# Queue display helpers
# -------------------------------------------------------------------

def print_queue_view(qm: MeetingQueueManager) -> None:
    """
    Displays the current merged queue in a readable terminal format.
    """
    merged = qm.merged_queue()

    print("\nCurrent Queue View:")
    print("-" * 70)

    if not merged:
        print("No students are currently waiting.")
        print("-" * 70)
        return

    for index, req in enumerate(merged, start=1):
        tier = "DSL" if req.is_dsl_queue else "Non-DSL"
        print(
            f"{index}. "
            f"{req.student_name} | "
            f"CWID: {req.student_id} | "
            f"{tier} | "
            f"Topic: {req.title} | "
            f"Joined: {req.formatted_time}"
        )

    print("-" * 70)

def notify_students_near_front(qm: PersistMeetingQueueManager, notifier: EmailNotifier, threshold: int = 2) -> None:
    """
    Queues one-time near-front emails for students near the front.

    Students are notified only if:
    - they are within the threshold
    - they opted into notifications
    - they have not already been notified
    """
    merged = qm.merged_queue()

    for position, req in enumerate(merged, start=1):
        if position > threshold:
            continue
        if not req.notification_ok:
            continue
        if req.near_front_notified:
            continue

        notifier.queue_near_front_notification(req, position)


# -------------------------------------------------------------------
# Student queue actions
# -------------------------------------------------------------------
def join_queue_flow(notifier: EmailNotifier) -> None:
    """
    Main flow for a student to join the queue.

    Handles both first-time and returning students, validates inputs,
    creates a MeetingRequest, and adds it to the queue.
    Steps:
    1. Choose a queue
    2. Confirm that queue has an active session
    3. Validate student CWID
    4. Run first-time or returning-student flow
    5. Create a MeetingRequest
    6. Enqueue request
    7. Queue confirmation/reminder emails
    """
    selected_queue = select_active_queue()
    if selected_queue is None:
        return

    session_and_manager = get_manager_for_active_session(selected_queue["queue_id"])
    if session_and_manager is None:
        print("That queue does not currently have an active office-hours session.")
        return

    session, qm = session_and_manager

    print("Welcome to the Ps & Qs Meeting Queue System!\n")

    # Step 1: Prompt for CWID and validate it exists in the database.
    while True:
        try:
            cwid_input = input("Please enter your CWID (or type 'quit' to exit): ").strip()
            if cwid_input.lower() == "quit":
                print("Exiting the queue system. Goodbye!")
                return

            cwid = int(cwid_input)

            if not cwid_exists(cwid):
                print("CWID not found in our records. Please try again.")
                continue

            break
        except ValueError:
            print("Invalid input. Please enter a numeric CWID.")

    # Step 2: Check if the student's profile is complete.
    student = get_student_by_cwid(cwid)

    if student is None:
        print("Unexpected error: Student record not found after CWID validation.")
        return

    if not profile_is_complete(student):
        # First-time setup flow.
        student = first_time_setup(cwid)
    
    else:
        # Returning student flow with email verification.
        if not returning_student_flow(student):
            return

    # Step 3: Prompt for meeting topic & notifications.
    topic = prompt_non_empty("\nEnter the topic you want help with: ")

    # Ask whether the sutdent wants to receive notifications when they are near the front of the queue.
    notification_ok = prompt_yes_no("Would you like to receive a notification when you are near the front of the queue? (yes/no): ")

    # Ask whether group help is okay.
    group_ok = prompt_yes_no("Is it okay if we group you with other students who have similar questions? (yes/no): ")

    # Step 4: Build a display name from the student record
    full_name = build_full_name(
        student["first_name"],
        student["middle_initial"],
        student["last_name"]
    )

    # Step 4: Create a MeetingRequest and add it to the queue.
    request = MeetingRequest(
        student_id=student["cwid"],
        student_name=full_name,
        email=student["contact_email"],
        title=topic,
        notification_ok=notification_ok,
        group_ok=group_ok,
        is_dsl_queue=student["dsl_status"],
    )

    try:
        qm.enqueue(request)
        print(f"\nSuccessfully added to the queue! Your current position will be shown in the next queue view.")
    except AlreadyWaitingError:
        print("\nYou are already in the queue. Please wait for your turn or contact support if you need assistance.")
        return

    position = qm.get_position(request.student_id)
    # Show confirmation details.
    print("\nStudent successfully added to the queue.")
    print(f"Name: {request.student_name}")
    print(f"CWID: {request.student_id}")
    print(f"Queue: {selected_queue['queue_name']}")
    print(f"Session: {session['title']}")
    print(f"Topic: {request.title}")
    print(f"Joined at: {request.formatted_time}")
    print(f"Position in queue: {position}")

    if request.notification_ok and position is not None:
        notifier.queue_join_confirmation(request, position)
        notifier.queue_waiting_reminder(request, delay_minutes=10)

    notify_students_near_front(qm, notifier)

def serve_next_flow(qm: MeetingQueueManager, notifier: EmailNotifier) -> None:
    """
    Handles the flow for serving the next student in the queue.

    This is a placeholder function to demonstrate how the queue manager
    would be used to serve students. In a real application, this would
    likely be triggered by a tutor action rather than being part of the
    same CLI as joining the queue.
    """
    print("\nServing the next student in the queue...")
    next_request = qm.dequeue_next()

    if next_request is None:
        print("No students are currently waiting.")
        return

    print(f"Now serving: {next_request.student_name} (CWID: {next_request.student_id})")
    print(f"Topic: {next_request.title}")
    print(f"Joined at: {next_request.formatted_time}")
    print(f"Status: {next_request.status}")

def cancel_flow(notifier: EmailNotifier) -> None:
        """
        Handles the flow for a student to cancel their queue request.

        This is a placeholder function to demonstrate how cancellation would work.
        In a real application, this would likely be triggered by the student
        rather than being part of the same CLI as joining the queue.
        Important note:
        even though this function has a qm parameter in its signature,
        we re-select the queue and active session inside this function
        so that cancellation happens in the correct queue/session context.

        Because of that, the passed-in qm is not actually used here.
        It is kept only to preserve your preferred function shape/name.
        """
        selected_queue = select_active_queue()
        if selected_queue is None:
            return

        session_and_manager = get_manager_for_active_session(selected_queue["queue_id"])
        if session_and_manager is None:
            print("That queue does not currently have an active office-hours session.")
            return

        # We only need the queue manager here.
        # The session object is returned too, but is not needed in this function.
        _, qm = session_and_manager         # _ would be session
        print("\nCancelling your queue request...")

        cwid_input = input("Please enter your CWID to confirm cancellation: ").strip()
        try:
            cwid = int(cwid_input)
        except ValueError:
            print("Invalid input. Cancellation aborted.")
            return
        
        success = qm.cancel_by_student(cwid)

        if success:
            print("Your request has been successfully cancelled.")
            # After a cancellation, someone else may now be near the front,
            # so we check whether a near-front email should be queued.
            notify_students_near_front(qm, notifier)
        else:
            print("You do not have an active request in the queue to cancel.")

def student_view_queue_flow() -> None:
    """
    Lets the user choose a queue and view the current merged queue for its active session.
    """
    selected_queue = select_active_queue()

    if selected_queue is None:
        return

    session_and_manager = get_manager_for_active_session(selected_queue["queue_id"])

    if session_and_manager is None:
        print("That queue does not currently have an active office-hours session.")
        return

    _, qm = session_and_manager
    print_queue_view(qm)

def staff_peek_next_flow() -> None:
    """
    Lets staff see who will be served next without removing them.
    """
    selected_queue = select_active_queue()

    if selected_queue is None:
        return

    session_and_manager = get_manager_for_active_session(selected_queue["queue_id"])

    if session_and_manager is None:
        print("No active session for that queue.")
        return

    _, qm = session_and_manager
    next_req = qm.peek_next()

    if next_req is None:
        print("No students are currently waiting.")
        return

    tier = "DSL" if next_req.is_dsl_queue else "Non-DSL"

    print(f"\nNext student: {next_req.student_name}")
    print(f"CWID: {next_req.student_id}")
    print(f"Tier: {tier}")
    print(f"Topic: {next_req.title}")
    print(f"Joined: {next_req.formatted_time}")


def staff_serve_next_flow(notifier: EmailNotifier) -> None:
    """
    Lets staff serve the next student in the queue.

    Side effects:
    - request status becomes Completed
    - now-serving email can be queued
    - near-front notifications may need to be updated for remaining students
    """
    selected_queue = select_active_queue()

    if selected_queue is None:
        return

    session_and_manager = get_manager_for_active_session(selected_queue["queue_id"])

    if session_and_manager is None:
        print("No active session for that queue.")
        return

    _, qm = session_and_manager

    print("\nServing the next student...")
    next_request = qm.dequeue_next()

    if next_request is None:
        print("No students are currently waiting.")
        return

    print(f"Now serving: {next_request.student_name} (CWID: {next_request.student_id})")
    print(f"Topic: {next_request.title}")
    print(f"Joined at: {next_request.formatted_time}")
    print(f"Status: {next_request.status}")

    # If the student opted in, queue an email that it is now their turn
    if next_request.notification_ok:
        notifier.queue_now_serving_email(next_request)

    # After serving one student, someone else may now be near the front
    notify_students_near_front(qm, notifier)


def staff_add_notes_flow() -> None:
    """
    Allows staff to add or update notes for an active request.
    """
    selected_queue = select_active_queue()

    if selected_queue is None:
        return

    session_and_manager = get_manager_for_active_session(selected_queue["queue_id"])

    if session_and_manager is None:
        print("No active session for that queue.")
        return

    _, qm = session_and_manager

    cwid_input = input("Enter the student's CWID: ").strip()

    try:
        cwid = str(int(cwid_input))
    except ValueError:
        print("Invalid CWID.")
        return

    notes = input("Enter professor/TA notes: ").strip()

    success = qm.add_notes_by_student(cwid, notes)

    if success:
        print("Notes updated successfully.")
    else:
        print("That student does not currently have an active request in this queue/session.")


def staff_queue_counts_flow() -> None:
    """
    Displays DSL, Non-DSL, and total counts for the selected queue/session.
    """
    selected_queue = select_active_queue()

    if selected_queue is None:
        return

    session_and_manager = get_manager_for_active_session(selected_queue["queue_id"])

    if session_and_manager is None:
        print("No active session for that queue.")
        return

    _, qm = session_and_manager
    counts = qm.queue_counts()

    print("\nCurrent queue counts:")
    print(f"DSL Queue: {counts['DSL']}")
    print(f"Non-DSL Queue: {counts['Non-DSL']}")
    print(f"Total: {counts['Total']}")


def staff_start_session_flow() -> None:
    """
    Lets staff create a new active office-hours session for a queue.

    Current default behavior:
    - session starts now
    - session ends 2 hours later

    Later:
    this can be expanded to allow custom date/time input.
    """
    selected_queue = select_active_queue()

    if selected_queue is None:
        return

    title = prompt_non_empty("Session title: ")

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=2)

    session_id = create_session(
        queue_id=selected_queue["queue_id"],
        title=title,
        start_time=start_time,
        end_time=end_time,
    )

    print(f"Created new session with ID {session_id} for queue '{selected_queue['queue_name']}'.")


def staff_reset_session_flow() -> None:
    """
    Resets the current active session for a selected queue.

    Current behavior:
    - all waiting requests in that session are cancelled
    - the session is marked inactive

    This preserves request history instead of deleting rows.
    """
    selected_queue = select_active_queue()

    if selected_queue is None:
        return

    session = get_active_session_for_queue(selected_queue["queue_id"])

    if session is None:
        print("No active session for that queue.")
        return

    qm = PersistMeetingQueueManager(
        queue_id=selected_queue["queue_id"],
        session_id=session["session_id"]
    )

    confirm = prompt_yes_no(
        f"Reset current session '{session['title']}' for queue '{selected_queue['queue_name']}'? (yes/no): "
    )

    if not confirm:
        print("Reset cancelled.")
        return

    qm.reset_current_session()
    end_session(session["session_id"])

    print("Session reset complete. Waiting requests were cancelled and the session was ended.")


# ------------------------------------------------------------
# Staff Action=and views
# ------------------------------------------------------------

def main() -> None:
    """
    Main terminal loop for the queue manager demo.
    Startup tasks:
    - create student table if needed
    - create queue/session/request/email tables if needed
    - seed starter queues if queue table is empty
    - start the background email worker
    """
    create_students_table()
    initialize_queue_storage()
    seed_default_queues_if_empty()

    # Create email notifier and start background processing for pending email jobs
    notifier = EmailNotifier()
    start_email_worker(notifier, poll_seconds=10)

    # Dummy placeholder queue manager kept so cancel_flow signature can stay as requested.
    # It is not used directly by cancel_flow because cancel_flow selects the correct queue/session itself.
    # taken off

    while True:
        print("\n========================================")
        print("Ps & Qs Meeting Queue Manager")
        print("========================================")
        print("1. Student: Join queue")
        print("2. Student: View queue")
        print("3. Student: Cancel my request")
        print("4. Staff: Peek next student")
        print("5. Staff: Serve next student")
        print("6. Staff: Add notes to active request")
        print("7. Staff: View queue counts")
        print("8. Staff: Start new office-hours session")
        print("9. Staff: Reset current session")
        print("10. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            join_queue_flow(notifier)

        elif choice == "2":
            student_view_queue_flow()

        elif choice == "3":
            cancel_flow(notifier)

        elif choice == "4":
            staff_peek_next_flow()

        elif choice == "5":
            staff_serve_next_flow(notifier)

        elif choice == "6":
            staff_add_notes_flow()

        elif choice == "7":
            staff_queue_counts_flow()

        elif choice == "8":
            staff_start_session_flow()

        elif choice == "9":
            staff_reset_session_flow()

        elif choice == "10":
            print("Exiting the queue system. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number from 1 to 10.")


# Start the terminal application only if this file is run directly.
if __name__ == "__main__":
    main()