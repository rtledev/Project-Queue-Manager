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
    school_email_matches,
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




# Start the terminal application only if this file is run directly.
if __name__ == "__main__":
    main()