# FIRST DRAFT OF OUR WAITLIST HAHAHA
from datetime import datetime   #imports datatime to generate timestamps

# Create an empty list to store students
waitlist = []

print("Priority Queue Waitlist System (COnsole Mockup)")
print("Type a student name to add them to the waitlist.")
print("Type 'quit' to stop.\n")

while True:
    # Get User Input
    name = input("Enter Student Name: ")

    # Exit Condition
    if name.lower() == "quit":
        break

    # time stats/ timestamp from waitlist added.
    timestamp = datetime.now()

    formatted_time = timestamp.strftime('%H:%M:%S')


    student = {
        "name": name,
        "timestamp": timestamp
    }

    # Append Student to the waitist.
    waitlist.append(student)

    # Display confirmation
    print(f"{student['name']} added at {timestamp.strftime('%H:%M:%S')}")
    print(f"Current position in the Queue: {len(waitlist)}\n")

    # Final Wailist (Consolde)
    print("\n Final Waitlist: \n")
    for index, student in enumerate(waitlist, start=1):
        print(f"{index}. {student['name']} - {student['timestamp'].strftime('%H:%M:%S')}")

print("\nSuccessfully exited the waitlist system. Goodbye!")


