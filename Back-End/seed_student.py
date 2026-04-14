"""
seed_student.py

Creates the students table and inserts 40 placeholder valid CWIDs.

Use this file once before running the app so the demo database
contains valid dummy CWIDs for signup/login testing.
"""

# Import the database functions from student_db.py
# initialize_student_db creates the table and ensures auth columns exist
# insert_placeholder_student adds each dummy CWID as a placeholder account
from student_db import initialize_student_db, insert_placeholder_student

# These are our dummy CWIDs for testing.
# In a real scenario, these would be actual student CWIDs.
# We made them 4-digit numbers to avoid confusion with real CWIDs,
# which are typically 8-digit numbers.
DUMMY_CWIDS = [
    1024, 1437, 1872, 2146, 2389,
    2510, 2674, 2891, 3015, 3188,
    3321, 3479, 3590, 3714, 3862,
    4017, 4183, 4295, 4471, 4588,
    4720, 4893, 5034, 5189, 5342,
    5487, 5611, 5796, 5930, 6084,
    6247, 6391, 6528, 6710, 6845,
    7012, 7186, 7324, 7459, 7683
]

def main() -> None:
    """
    Creates the table, ensures auth columns exist,
    and seeds all placeholder students into the database.
    """
    # Step 1: Create/update the database schema before inserting any data.
    initialize_student_db()

    # Step 2: Insert placeholder students for each CWID in DUMMY_CWIDS.
    for cwid in DUMMY_CWIDS:
        insert_placeholder_student(cwid)

    print("Initialized the student database and ensured auth columns exist.")
    print(f"Inserted {len(DUMMY_CWIDS)} placeholder students into the database (or they already existed).")

# Run the seeding process only if this file is executed directly.
if __name__ == "__main__":
    main()