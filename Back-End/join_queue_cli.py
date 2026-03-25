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
"""

# Import the queue engine pieces.
from Priority_Queue import MeetingQueueManager, MeetingRequest, AlreadyWaitingError

# Import database helper functions.
from student_db import (
    cwid_exists,
    get_student_by_cwid,
    profile_is_complete,
    school_email_matches_cwid,
    update_student_info,
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
        email = input(prompt_text).strip()
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


def print_queue_view(qm: MeetingQueueManager) -> None:
    """
    Displays the current merged queue in a readable terminal format.
    """
    merged = qm.merged_queue()

    print("\nCurrent Queue View:")
    print("-" * 70)

    if not merged:
        print("No students are currently waiting.")
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
    
def join_queue_flow(qm: MeetingQueueManager) -> None:
    """
    Main flow for a student to join the queue.

    Handles both first-time and returning students, validates inputs,
    creates a MeetingRequest, and adds it to the queue.
    """
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


    # Show confirmation details.
    print("\nStudent successfully added to the queue.")
    print(f"Name: {request.student_name}")
    print(f"CWID: {request.student_id}")
    print(f"Topic: {request.title}")
    print(f"Joined at: {request.formatted_time}")
    print(f"Position in queue: {qm.get_position(request.student_id)}")


def serve_next_flow(qm: MeetingQueueManager) -> None:
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

def cancel_flow(qm: MeetingQueueManager) -> None:
        """
        Handles the flow for a student to cancel their queue request.

        This is a placeholder function to demonstrate how cancellation would work.
        In a real application, this would likely be triggered by the student
        rather than being part of the same CLI as joining the queue.
        """
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
        else:
            print("You do not have an active request in the queue to cancel.")

def main() -> None:
    """
    Main terminal loop for the queue manager demo.
    """

    # Create a queue manager instance for this terminal session.
    qm = MeetingQueueManager()

    while True:
        print("\n==============================")
        print("Ps & Qs Meeting Queue Manager")
        print("==============================")
        print("1. Join the queue")
        print("2. View current queue")
        print("3. Peek next student")
        print("4. Serve next student")
        print("5. Cancel a request by CWID")
        print("6. Queue counts")
        print("7. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            join_queue_flow(qm)

        elif choice == "2":
            print_queue_view(qm)

        elif choice == "3":
            next_req = qm.peek_next()
            if next_req:
                print(f"\nNext student in line: {next_req.student_name} (CWID: {next_req.student_id}) - Topic: {next_req.title}")
                tier = "DSL" if next_req.is_dsl_queue else "Non-DSL"
                print(f"Tier: {tier}")
                print(f"Joined at: {next_req.formatted_time}")
            else:
                print("\nNo students are currently waiting.")

        elif choice == "4":
            serve_next_flow(qm)

        elif choice == "5":
            cancel_flow(qm)

        elif choice == "6":
            counts = qm.queue_counts()
            print(f"\nCurrent queue counts:")
            print(f"DSL Queue: {counts['DSL']}")
            print(f"Non-DSL Queue: {counts['Non_DSL']}")
            print(f"Total: {counts['Total']}")

        elif choice == "7":
            print("Exiting the queue system. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter a number from 1 to 7.")

# Start the terminal application only if this file is run directly.
if __name__ == "__main__":
    main()