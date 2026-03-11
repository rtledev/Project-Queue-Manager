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


