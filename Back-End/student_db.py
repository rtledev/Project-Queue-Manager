# sqlite3 is Python's built-in library for working with SQLite databases.
import sqlite3

# Optional type hint used for values that may be missing
from typing import Optional

# The name of the SQLite database file.
DB_NAME = 'students.db'

def get_connection():
    """
    Establishes and returns a connection to the SQLite database.
    DB file name stays centralized and other database functions can reuse 
    this function to get a connection without hardcoding the DB name multiple times.
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
    """
    # Open a connection to the database.
    conn = get_connection()
    # Create a cursor object to run SQL commands.
    cursor = conn.cursor()
    
    # SQL command to create the students table
    cursor.execute('''
         CREATE TABLE IF NOT EXISTS students (
            cwid INTEGER PRIMARY KEY,
            first_name TEXT,
            middle_initial TEXT,
            last_name TEXT,
            school_email TEXT,
            contact_email TEXT,
            phone_number TEXT,
            dsl_status INTEGER NOT NULL DEFAULT 0
        )
    ''')
    
    conn.commit()   # saves the changes to the database
    conn.close()

def insert_placeholder_student(cwid: int) -> None:
    """
    Inserts a placeholder student row for a CWID.

    This is used for your initial seed database where only the CWID
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
            dsl_status
        )
        VALUES (?, '', '', '', '', '', '', 0)
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

    """
    # We only need to know if at least one row exists with the given CWID, 
    so we can select a constant value (like 1) instead of all columns.
    """
    cursor.execute("SELECT 1 FROM students WHERE cwid = ?", (cwid,))
    result = cursor.fetchone()  # fetchone() returns None if no rows are found

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
            dsl_status
        FROM students
        WHERE cwid = ?
    """, (cwid,))
    
    row = cursor.fetchone()  # fetchone() returns None if no rows are found
    conn.close()

    # Converts the row tuple into a dic foreasier readability/use.
    if row:
        return {
            'cwid': row[0],
            'first_name': row[1],
            'middle_initial': row[2],
            'last_name': row[3],
            'school_email': row[4],
            'contact_email': row[5],
            'phone_number': row[6],
            'dsl_status': bool(row[7])  # Convert integer to boolean
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
            dsl_status: bool) -> bool:
        """
        Updates a student's information in the database after CWID has been validated
        
        This is used when:
        - A student's information needs to be updated in the database
        - a first-time student completes their profile after CWID validation
        Returns True if the update was successful (i.e., student exists), False otherwise.
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE students
            SET
                first_name = ?,
                middle_initial = ?,
                last_name = ?,
                school_email = ?,
                contact_email = ?,
                phone_number = ?,
                dsl_status = ?
            WHERE cwid = ?
        """, (
            first_name, 
            middle_initial, 
            last_name, 
            school_email, 
            contact_email, 
            phone_number, 
            int(dsl_status), # Cionvert True/False to 1/0 for storage (SQLite does not have a native boolean type). 
            cwid))
        conn.commit()
        updated_rows = cursor.rowcount  # number of rows updated
        conn.close()
        return updated_rows > 0  # True if at least one row was updated, False otherwise
    
def school_email_matches_cwid(school_email: str, cwid: int) -> bool:
    """
    Checks if the provided school email matches the CWID in the database.
    Returns True if it matches, False otherwise.

    This supports returning-student flow 
    (if a student provides their CWID and school email, we can verify that they match before allowing them to update their profile or access services).
    Also on web based if they have filled out the form previously.
    Since we have their DATA - LETS SELL IT ALL AHAHHAHAHAHA
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM students 
        WHERE cwid = ? AND school_email = ?
    """, (cwid, school_email))
    
    result = cursor.fetchone()  # fetchone() returns None if no rows are found
    conn.close()
    
    return result is not None

def profile_is_complete(student: dict) -> bool:
    """
    Checks whether the student has completed their profile 
    by verifying that all required fields are filled out.

    For current prototype, we consider a profile complete if:
    - first_name, last_name, school_email, and contact_email are not empty

    THerefore if blank, we treat them as first-time setup.
    """
    
    required_fields = ['first_name', 'last_name', 'school_email', 'contact_email']
    return all(student.get(field, "").strip() for field in required_fields) # to strip whitespace and check if non-empty
