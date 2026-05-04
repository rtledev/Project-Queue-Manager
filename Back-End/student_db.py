# sqlite3 is Python's built-in library for working with SQLite databases.
import sqlite3

# Optional type hint used for values that may be missing.
from typing import Optional

# Werkzeug helpers for password hashing and verification.
# generate_password_hash stores a safe hash instead of a plain-text password.
# check_password_hash verifies a plain-text password against the stored hash.
from werkzeug.security import generate_password_hash, check_password_hash

from pathlib import Path

# The name of the SQLite database file.
DB_NAME = str(Path(__file__).resolve().parent / "students.db")


def get_connection():
    """
    Establishes and returns a connection to the SQLite database.

    The database file name stays centralized here so other functions
    can reuse this helper instead of hardcoding the DB name repeatedly.
    """
    return sqlite3.connect(DB_NAME)


def create_students_table():
    """
    Creates the 'students' table in the database if it doesn't already exist.

    Table design:
        cwid           -> primary key
        first_name     -> student's first name
        middle_initial -> optional middle initial
        last_name      -> student's last name
        school_email   -> official school email
        contact_email  -> preferred email for reminders/contact
        phone_number   -> optional phone number
        dsl_status     -> 1 for True, 0 for False
        role           -> student / teacher
    """
    # Open a connection to the database.
    conn = get_connection()

    # Create a cursor object to run SQL commands.
    cursor = conn.cursor()

    # SQL command to create the students table.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            cwid INTEGER PRIMARY KEY,
            first_name TEXT,
            middle_initial TEXT,
            last_name TEXT,
            school_email TEXT,
            contact_email TEXT,
            phone_number TEXT,
            dsl_status INTEGER NOT NULL DEFAULT 0,
            role TEXT NOT NULL DEFAULT 'student'
        )
    """)

    conn.commit()   # Save the changes to the database.
    conn.close()


def ensure_auth_columns() -> None:
    """
    Ensures the students table includes authentication-related columns
    needed for login/signup.

    Since the database may already exist from earlier development,
    we inspect the current schema first before trying to add new columns.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(students)")
    columns = [row[1] for row in cursor.fetchall()]

    # Add password_hash only if it does not already exist.
    if "password_hash" not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN password_hash TEXT")

     # Add role only if it does not already exist.
    if "role" not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")
    conn.commit()
    conn.close()


def initialize_student_db() -> None:
    """
    Initializes the student database for the current version of the project.

    This:
    1. creates the students table if it does not exist
    2. ensures newer authentication columns exist
    """
    create_students_table()
    ensure_auth_columns()


def insert_placeholder_student(cwid: int) -> None:
    """
    Inserts a placeholder student row for a CWID.

    This is used for the initial seed database where only the CWID
    is considered valid at first, and all other fields are blank.

    INSERT OR IGNORE means:
        - if the CWID already exists, do nothing
        - if it does not exist, insert it
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO students (
            cwid,
            first_name,
            middle_initial,
            last_name,
            school_email,
            contact_email,
            phone_number,
            dsl_status,
            role
        )
        VALUES (?, '', '', '', '', '', '', 0, 'student')
    """, (cwid,))

    conn.commit()
    conn.close()


def cwid_exists(cwid: int) -> bool:
    """
    Checks if a given CWID exists in the students table.

    Returns True if it exists, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # We only need to know whether at least one row exists with this CWID,
    # so selecting a constant value like 1 is sufficient.
    cursor.execute("SELECT 1 FROM students WHERE cwid = ?", (cwid,))
    result = cursor.fetchone()

    conn.close()
    return result is not None


def get_student_by_cwid(cwid: int) -> Optional[dict]:
    """
    Retrieves a student's information by their CWID.

    Returns a dictionary of student info if found, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cwid,
            first_name,
            middle_initial,
            last_name,
            school_email,
            contact_email,
            phone_number,
            dsl_status,
            role
        FROM students
        WHERE cwid = ?
    """, (cwid,))

    row = cursor.fetchone()
    conn.close()

    # Convert the row tuple into a dictionary for easier readability/use.
    if row:
        return {
            "cwid": row[0],
            "first_name": row[1],
            "middle_initial": row[2],
            "last_name": row[3],
            "school_email": row[4],
            "contact_email": row[5],
            "phone_number": row[6],
            "dsl_status": bool(row[7]),  # Convert integer to boolean.
            "role": row[8],
        }
    else:
        return None


def update_student_info(
    cwid: int,
    first_name: str,
    middle_initial: str,
    last_name: str,
    school_email: str,
    contact_email: str,
    phone_number: str,
    dsl_status: bool,
    role: str = "student",
) -> bool:
    """
    Updates a student's information in the database after CWID has been validated.

    This is used when:
    - a student's information needs to be updated in the database
    - a first-time student completes their profile after CWID validation

    Returns True if the update was successful (student exists), False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Normalize emails to lowercase before storing them.
    # This keeps email values consistent and avoids case-sensitive mismatches later.
    school_email = school_email.strip().lower()
    contact_email = contact_email.strip().lower()

    cursor.execute("""
        UPDATE students
        SET
            first_name = ?,
            middle_initial = ?,
            last_name = ?,
            school_email = ?,
            contact_email = ?,
            phone_number = ?,
            dsl_status = ?,
            role = ?
        WHERE cwid = ?
    """, (
        first_name,
        middle_initial,
        last_name,
        school_email,
        contact_email,
        phone_number,
        int(dsl_status),  # Convert True/False to 1/0 for SQLite storage.
        role,
        cwid,
    ))

    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()

    return updated_rows > 0


def school_email_matches_cwid(school_email: str, cwid: int) -> bool:
    """
    Checks if the provided school email matches the CWID in the database.

    Returns True if it matches, False otherwise.

    Comparison is case-insensitive so that:
    Bob@gmail.com
    bob@gmail.com
    BOB@gmail.com
    are all treated as the same email.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM students
        WHERE cwid = ?
          AND LOWER(school_email) = LOWER(?)
    """, (cwid, school_email.strip()))

    result = cursor.fetchone()
    conn.close()

    return result is not None


def set_student_password(cwid: int, password: str) -> bool:
    """
    Stores a hashed password for the given student CWID.

    Returns True if the update succeeded, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()

    password_hash = generate_password_hash(password)

    cursor.execute("""
        UPDATE students
        SET password_hash = ?
        WHERE cwid = ?
    """, (password_hash, cwid))

    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()

    return updated_rows > 0


def get_password_hash_by_cwid(cwid: int) -> Optional[str]:
    """
    Returns the stored password hash for a student CWID,
    or None if the student does not exist or has not set a password yet.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password_hash
        FROM students
        WHERE cwid = ?
    """, (cwid,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    return None


def student_has_password(cwid: int) -> bool:
    """
    Checks whether the student already has a stored password.

    This is useful for deciding whether a placeholder CWID has already
    been turned into a real account.
    """
    stored_hash = get_password_hash_by_cwid(cwid)
    return stored_hash is not None and stored_hash.strip() != ""


def profile_is_complete(student: dict) -> bool:
    """
    Checks whether the student has completed their profile
    by verifying that all required fields are filled out.

    For the current prototype, we consider a profile complete if:
    - first_name, last_name, school_email, and contact_email are not empty

    Therefore, if they are blank, we treat the student as first-time setup.
    """
    required_fields = ["first_name", "last_name", "school_email", "contact_email"]
    return all(student.get(field, "").strip() for field in required_fields)


def student_account_is_ready(cwid: int) -> bool:
    """
    Checks whether a student account is fully ready for normal login.

    For the current project, that means:
    - the CWID exists
    - the profile is complete
    - a password has been set

    This is useful for demo logic and testing flows with dummy CWIDs.
    """
    student = get_student_by_cwid(cwid)

    if student is None:
        return False

    return profile_is_complete(student) and student_has_password(cwid)


def create_student_account(
    cwid: int,
    first_name: str,
    middle_initial: str,
    last_name: str,
    school_email: str,
    contact_email: str,
    phone_number: str,
    dsl_status: bool,
    password: str,
    role: str = "student",
) -> Optional[dict]:
    """
    Creates or completes a student account using an existing valid CWID.

    Current project behavior:
    - CWID must already exist in the database
    - profile fields are updated
    - password is hashed and stored

    This matches the dummy-CWID demo workflow:
    1. seed valid CWIDs first
    2. allow signup only for those valid CWIDs
    3. store account/profile info for later login

    Returns the updated student dictionary if successful, or None otherwise.
    """
    # For this project, signup only works for CWIDs that were already seeded.
    if not cwid_exists(cwid):
        return None

    updated = update_student_info(
        cwid=cwid,
        first_name=first_name,
        middle_initial=middle_initial,
        last_name=last_name,
        school_email=school_email,
        contact_email=contact_email,
        phone_number=phone_number,
        dsl_status=dsl_status,
    )

    if not updated:
        return None

    password_set = set_student_password(cwid, password)

    if not password_set:
        return None

    return get_student_by_cwid(cwid)


def authenticate_student(cwid: int, school_email: str, password: str) -> Optional[dict]:
    """
    Authenticates a student using:
    - CWID
    - school email
    - password

    Returns the student dictionary if authentication succeeds,
    or None if authentication fails.
    """
    student = get_student_by_cwid(cwid)

    if student is None:
        return None

    # Compare emails case-insensitively for convenience.
    if student["school_email"].strip().lower() != school_email.strip().lower():
        return None

    stored_hash = get_password_hash_by_cwid(cwid)

    if not stored_hash:
        return None

    if not check_password_hash(stored_hash, password):
        return None

    return student

# Professor account helper functions. 

def get_next_professor_id() -> int:
    """
    Generates the next available negative ID for professor accounts.

    Student demo CWIDs are positive numbers, so using negative values keeps
    professor IDs separate without requiring a real CWID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MIN(cwid) FROM students")
    row = cursor.fetchone()
    conn.close()

    min_id = row[0] if row and row[0] is not None else 0

    if min_id >= 0:
        return -1

    return min_id - 1


def create_professor_account(
    first_name: str,
    middle_initial: str,
    last_name: str,
    school_email: str,
    contact_email: str,
    phone_number: str,
    password: str,
) -> Optional[dict]:
    """
    Creates a professor account without requiring a CWID.

    For the current prototype, professor accounts use internally generated
    negative IDs instead of real employee/university identifiers.
    """
    cwid = get_next_professor_id()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO students (
            cwid,
            first_name,
            middle_initial,
            last_name,
            school_email,
            contact_email,
            phone_number,
            dsl_status,
            role
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cwid,
        first_name,
        middle_initial,
        last_name,
        school_email,
        contact_email,
        phone_number,
        0,
        "professor",
    ))

    conn.commit()
    conn.close()

    password_set = set_student_password(cwid, password)

    if not password_set:
        return None

    return get_student_by_cwid(cwid)