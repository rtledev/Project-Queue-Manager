"""
seed_student.py

Creates the students table and inserts 40 placeholder valid CWIDs.

Use this file once before running join_queue_cli.py
to ensure it can rerun it safely because of the "IF NOT EXISTS" and "INSERT OR IGNORE" statements.
"""

# Import the database functions from student_db.py
from student_db import create_students_table, insert_placeholder_student

# These are our dummy CWIDs for testing. In a real scenario, these would be actual student CWIDs.
# Made them 4-digit numbers to avoid confusion with real CWIDs, which are typically 8-digit numbers.
# and because im lazy and don't want to type 8-digit numbers 40 times.
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
    Creates the table and seeds all placeholder students into the database.
    """
    # Step 1: Create the students table if it doesn't exist already before insterting any data.
    create_students_table()
    
    # Step 2: Insert placeholder students for each CWID in DUMMY_CWIDS
    for cwid in DUMMY_CWIDS:
        insert_placeholder_student(cwid)

        
    print("student_db.py should have created the students table if it didn't exist, and then inserted 40 placeholder students with CWIDs from DUMMY_CWIDS.")
    print(f"Inserted {len(DUMMY_CWIDS)} placeholder students into the database (or already existed).")

# Run the seeding process only if this file is executed directly (not imported as a module)
if __name__ == "__main__":
    main()