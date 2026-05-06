import sqlite3
# just to clear pedning email jobs

conn = sqlite3.connect("students.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM email_jobs WHERE status = 'Pending'")

conn.commit()
conn.close()

print("Cleared pending email jobs.")

# run: python clear_email_jobs.py