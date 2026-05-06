# Import Flask core components:
# Flask -> main web app framework
# jsonify -> converts Python data (dict/list) into JSON responses
# request -> allows us to access incoming HTTP request data (like JSON body)
from flask import Flask, jsonify, request

# Import CORS support so our React frontend (running on a different port)
# can make requests to this backend without being blocked by a browser
from flask_cors import CORS

# Import queue system logic from the backend engine.
# MeetingQueueManager -> manages the queue
# MeetingRequest -> represents one student request
# AlreadyWaitingError -> custom error if a student is already in queue
from Priority_Queue import MeetingQueueManager, MeetingRequest, AlreadyWaitingError

from wait_time_estimator import build_wait_time_estimates

from notification_service import EmailNotifier, start_email_worker

from queue_db import initialize_queue_storage

from datetime import datetime, timedelta


# Initialize the student database schema needed for account creation/login
from student_db import (
    initialize_student_db,
    create_student_account,
    create_professor_account,
    authenticate_student,
)

# Create the Flask application instance.
# __name__ tells Flask where this file is located.
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS).
# This allows the React frontend
# to communicate with this backend.
CORS(app)


# Create an in-memory queue manager instance.
# This means all queue data is stored in RAM temporarily.
# If the server restarts, the queue will reset.
qm = MeetingQueueManager()

# Initialize The student database needed for account creation/login
from seed_student import seed_dummy_students
initialize_student_db()
seed_dummy_students()
initialize_queue_storage()

qm = MeetingQueueManager()

# Create the email notifier service.
notifier = EmailNotifier()

# Start the background worker that processes queued email jobs.
start_email_worker(notifier)

# Temporary mock data for office hours sessions.
# Right now this is hardcoded.
# Later, this will come from a database.
OFFICE_HOURS = [
    {
        "id": 1,
        "name": "Professor Jones",
        "role": "Professor",
        "subtitle": "Office Hours",
        "status": "Open",
        "time": "Mon / Wed • 2:00 PM - 4:00 PM",
        "location": "CS Building Room 201",
        "meetingType": "General course questions",
        "description": "Get help with lectures, assignments, and general course concepts."
    },
    {
        "id": 2,
        "name": "TA Smith",
        "role": "TA",
        "subtitle": "Lab Help",
        "status": "Open",
        "time": "Tue / Thu • 1:00 PM - 3:00 PM",
        "location": "Zoom / Lab Support",
        "meetingType": "Lab and coding help",
        "description": "Best for implementation questions, debugging, and lab assignment support."
    }
]
# Dashboard helper function
def dashboard_access_allowed(request_data) -> bool:
    """
    Checks whether the provided request payload belongs to a professor account.

    For this prototype, the frontend sends the current signed-in account role.
    """
    if not request_data:
        return False

    return str(request_data.get("role", "")).strip().lower() == "professor"

# Helper function for email functionality
def check_near_front_notifications():
    """
    Looks at all waiting requests and queues near-front emails
    for students who have reached positions 1 through 3.

    Prevents duplicate emails from being sent repeatedly
    within a short cooldown window.
    """

    merged = qm.merged_queue()

    for index, req in enumerate(merged, start=1):

        # Only notify students near the front
        if index <= 3 and req.notification_ok:
            now = datetime.now()

            # Check whether a near-front email was recently sent
            last_sent = getattr(req, "last_near_front_email_time", None)

            if last_sent is not None:
                cooldown = timedelta(seconds=10)

                # Skip if still inside cooldown window
                if now - last_sent < cooldown:
                    continue

            # Queue the email
            notifier.queue_near_front_notification(req, index)

            # Save timestamp of this notification
            req.last_near_front_email_time = now

# -------------------------------
# GET: /api/office-hours
# -------------------------------
# This endpoint returns a list of available office hours sessions
# along with how many students are currently waiting in the queue.
@app.get("/api/office-hours")
def get_office_hours():

    # Get current queue counts from the queue manager.
    counts = qm.queue_counts()

    # Extract total number of students waiting.
    total_waiting = counts["Total"]

    # Build response list.
    data = []

    # Loop through each office-hours session.
    for session in OFFICE_HOURS:

        # Create a copy of the session dictionary
        # so the original data is not modified directly.
        item = dict(session)

        # Add dynamic queue info to each session.
        # For now, all cards show the same total queue count because
        # the current prototype uses one shared queue.
        item["studentsWaiting"] = total_waiting

        # Add this updated session to the response list.
        data.append(item)

    # Return the list as a JSON response.
    return jsonify(data)

# -------------------------------
# POST: /api/dashboard/office-hours
# -------------------------------
# This endpoint returns a list of available office hours sessions
# and sends it to the professors dashboard for management.
@app.post("/api/dashboard/office-hours")
def dashboard_office_hours():
    data = request.get_json()

    if not dashboard_access_allowed(data):
        return jsonify({"error": "Professor access required."}), 403

    created_by = data.get("created_by")

    sessions = []
    for session in OFFICE_HOURS:
        if session.get("created_by") == created_by:
            sessions.append(session)

    return jsonify(sessions), 200

# ------------------------------------------- 
# DELETE: /api/dashboard/delete-office-hours
# -------------------------------------------
# This endpoint deletes the specified office hours session.
@app.post("/api/dashboard/delete-office-hours")
def delete_office_hours():
    data = request.get_json()

    if not dashboard_access_allowed(data):
        return jsonify({"error": "Professor access required."}), 403

    session_id = data.get("session_id")
    created_by = data.get("created_by")

    if session_id is None:
        return jsonify({"error": "Missing required field: session_id"}), 400

    for i, session in enumerate(OFFICE_HOURS):
        if session.get("id") == session_id and session.get("created_by") == created_by:
            deleted_session = OFFICE_HOURS.pop(i)
            return jsonify({
                "message": "Office hours session deleted successfully.",
                "session": deleted_session
            }), 200

    return jsonify({"error": "Session not found or not owned by this professor."}), 404

# -------------------------------
# POST: /api/auth/signup
# -------------------------------
# This endpoint creates either:
# - a student account using a valid dummy CWID
# - a professor account using a generated internal ID
@app.post("/api/auth/signup")
def auth_signup():

    # Extract JSON data sent from the frontend.
    data = request.get_json()

    # Role defaults to student if not provided.
    role = str(data.get("role", "student")).strip().lower()

    # Shared required fields for all account types.
    common_required_fields = [
        "first_name",
        "last_name",
        "school_email",
        "password",
    ]

    for field in common_required_fields:
        if field not in data or str(data[field]).strip() == "":
            return jsonify({"error": f"Missing required field: {field}"}), 400

    contact_email = str(data.get("contact_email", "")).strip()
    if contact_email == "":
        contact_email = data["school_email"]

    # Professor account flow.
    if role == "professor":
        account = create_professor_account(
            first_name=data["first_name"].strip(),
            middle_initial=str(data.get("middle_initial", "")).strip(),
            last_name=data["last_name"].strip(),
            school_email=data["school_email"].strip(),
            contact_email=contact_email,
            phone_number=str(data.get("phone_number", "")).strip(),
            password=data["password"],
        )

        if account is None:
            return jsonify({"error": "Unable to create professor account."}), 400

        return jsonify({
            "message": "Professor account created successfully.",
            "student": account
        }), 201

    # Student account flow.
    if "cwid" not in data or str(data["cwid"]).strip() == "":
        return jsonify({"error": "Missing required field: cwid"}), 400

    try:
        cwid = int(data["cwid"])
    except ValueError:
        return jsonify({"error": "CWID must be numeric."}), 400

    account = create_student_account(
        cwid=cwid,
        first_name=data["first_name"].strip(),
        middle_initial=str(data.get("middle_initial", "")).strip(),
        last_name=data["last_name"].strip(),
        school_email=data["school_email"].strip(),
        contact_email=contact_email,
        phone_number=str(data.get("phone_number", "")).strip(),
        dsl_status=bool(data.get("dsl_status", False)),
        password=data["password"],
        role="student",
    )

    if account is None:
        return jsonify({
            "error": "Unable to create account. Make sure the CWID exists in the system."
        }), 400

    return jsonify({
        "message": "Account created successfully.",
        "student": account
    }), 201


# -------------------------------
# POST: /api/auth/login
# -------------------------------
# This endpoint authenticates a student account.
@app.post("/api/auth/login")
def auth_login():

    # Extract JSON data sent from the frontend.
    data = request.get_json()

    # Required fields for login.
    required_fields = ["cwid", "school_email", "password"]

    # Validate required fields.
    for field in required_fields:
        if field not in data or str(data[field]).strip() == "":
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        cwid = int(data["cwid"])
    except ValueError:
        return jsonify({"error": "CWID must be numeric."}), 400

    student = authenticate_student(
        cwid=cwid,
        school_email=data["school_email"].strip(),
        password=data["password"],
    )

    if student is None:
        return jsonify({"error": "Invalid CWID, school email, or password."}), 401

    return jsonify({
        "message": "Login successful.",
        "student": student
    }), 200

# -------------------------------
# GET: /api/profile/<cwid>
# -------------------------------
# This endpoint returns one account's saved profile information.
# cwid is accepted as a string first so professor accounts using
# generated negative IDs can still be handled correctly.
@app.get("/api/profile/<cwid>")
def get_profile(cwid):
    from student_db import get_student_by_cwid

    try:
        cwid_value = int(cwid)
    except ValueError:
        return jsonify({"error": "Invalid account ID."}), 400

    student = get_student_by_cwid(cwid_value)

    if student is None:
        return jsonify({"error": "Student not found."}), 404

    return jsonify(student), 200


# -------------------------------
# POST: /api/profile/update
# -------------------------------
# This endpoint updates editable student profile fields.
@app.post("/api/profile/update")
def update_profile():
    from student_db import update_student_info, get_student_by_cwid

    data = request.get_json()

    required_fields = [
        "cwid",
        "first_name",
        "middle_initial",
        "last_name",
        "school_email",
        "contact_email",
        "phone_number",
        "dsl_status",
        "role",
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        cwid = int(data["cwid"])
    except ValueError:
        return jsonify({"error": "CWID must be numeric."}), 400

    updated = update_student_info(
        cwid=cwid,
        first_name=str(data["first_name"]).strip(),
        middle_initial=str(data["middle_initial"]).strip(),
        last_name=str(data["last_name"]).strip(),
        school_email=str(data["school_email"]).strip(),
        contact_email=str(data["contact_email"]).strip(),
        phone_number=str(data["phone_number"]).strip(),
        dsl_status=bool(data["dsl_status"]),
        role=str(data.get("role", "student")).strip().lower(),
    )

    if not updated:
        return jsonify({"error": "Unable to update profile."}), 400

    student = get_student_by_cwid(cwid)
    return jsonify({
        "message": "Profile updated successfully.",
        "student": student
    }), 200

# -------------------------------
# POST: /api/dashboard/create-office-hours
# -------------------------------
# This endpoint allows professor accounts to create a new office-hours session.
@app.post("/api/dashboard/create-office-hours")
def create_office_hours():
    data = request.get_json()

    if not dashboard_access_allowed(data):
        return jsonify({"error": "Professor access required."}), 403

    required_fields = [
        "name",
        "hostRole",
        "subtitle",
        "time",
        "location",
        "meetingType",
        "description",
    ]

    for field in required_fields:
        if field not in data or str(data[field]).strip() == "":
            return jsonify({"error": f"Missing required field: {field}"}), 400

    new_session = {
        "id": len(OFFICE_HOURS) + 1,
        "name": str(data["name"]).strip(),
        "role": str(data["hostRole"]).strip(),
        "subtitle": str(data["subtitle"]).strip(),
        "status": "Open",
        "time": str(data["time"]).strip(),
        "location": str(data["location"]).strip(),
        "meetingType": str(data["meetingType"]).strip(),
        "description": str(data["description"]).strip(),
        "created_by": data.get("created_by"),
    }

    OFFICE_HOURS.append(new_session)

    return jsonify({
        "message": "Office hours session created successfully.",
        "session": new_session
    }), 201

# -------------------------------
# POST: /api/join-queue
# -------------------------------
# This endpoint allows a student to join the queue.
@app.post("/api/join-queue")
def join_queue():

    # Extract JSON data sent from the frontend (React).
    data = request.get_json()

    # Define required fields that must be present in the request.
    required_fields = ["student_id", "student_name", "email", "title"]

    # Validate that all required fields exist and are not empty.
    for field in required_fields:
        if field not in data or str(data[field]).strip() == "":

            # If missing, return a 400 Bad Request error.
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Create a new MeetingRequest object using incoming data.
    # This object represents one student in the queue.
    request_obj = MeetingRequest(
        student_id=str(data["student_id"]),  # ensure ID is string
        student_name=data["student_name"],
        email=data["email"],
        title=data["title"],

        # Optional fields (default to False if not provided)
        notification_ok=bool(data.get("notification_ok", False)),
        group_ok=bool(data.get("group_ok", False)),
        is_dsl_queue=bool(data.get("is_dsl_queue", False)),
    )

    try:
        # Try to add the request to the queue.
        qm.enqueue(request_obj)

    except AlreadyWaitingError:
        # If student is already in queue, return 409 Conflict error.
        return jsonify({"error": "Student already has an active request."}), 409

    
    # Get the student's current queue position after joining.
    position = qm.get_position(str(data["student_id"]))

    merged = qm.merged_queue()
    estimates = build_wait_time_estimates(merged)
    estimated_minutes = estimates.get(request_obj.request_id)

    if request_obj.notification_ok:
        notifier.queue_join_confirmation(
        request_obj,
        position,
        estimated_minutes
    )

    if request_obj.notification_ok:
        print("Attempting to queue reminder email...")
        reminder_result = notifier.queue_waiting_reminder(request_obj, delay_minutes=10)
        print("queue_waiting_reminder result:", reminder_result)

    # After the queue changes, check whether anyone is now near the front.
    check_near_front_notifications()

    # If successful, return confirmation data.
    return jsonify({
        "message": "Joined queue successfully.",
        "request_id": request_obj.request_id,
        "position": position,
        "joined_at": request_obj.formatted_time,
        "estimated_wait_minutes": estimated_minutes
}), 201 # 201 = Created


# -------------------------------
# POST: /api/cancel-queue
# -------------------------------
# This endpoint allows a student to cancel their active queue request.
@app.post("/api/cancel-queue")
def cancel_queue():

    # Extract JSON data sent from the frontend.
    data = request.get_json()

    # Read the student ID from the request body.
    # We convert it to a clean string because the queue manager
    # expects student IDs in string form.
    student_id = str(data.get("student_id", "")).strip()

    # Validate that a student ID was actually provided.
    if student_id == "":
        return jsonify({"error": "Missing required field: student_id"}), 400

    # Ask the queue manager to cancel this student's active request.
    success = qm.cancel_by_student(student_id)

    # If the queue manager returns False, the student was not actively waiting.
    if not success:
        return jsonify({"error": "No active request found for this student."}), 404

    # After the queue changes, check whetehr anyone is now near the front,
    check_near_front_notifications()

    # If cancellation succeeds, return a confirmation response.
    return jsonify({
        "message": "Queue request cancelled successfully.",
        "student_id": student_id
    }), 200


# -------------------------------
# GET: /api/queue/<student_id>/position
# -------------------------------
# This endpoint returns the current position of a student in the queue.
@app.get("/api/queue/<student_id>/position")
def get_position(student_id):

    # Get the student's position in the queue.
    position = qm.get_position(str(student_id))

    # If the student is not in the queue, return 404 Not Found.
    if position is None:
        return jsonify({"error": "No active request found for this student."}), 404

    # Otherwise, return their position.
    return jsonify({
        "student_id": student_id,
        "position": position
    })


# -------------------------------
# POST: /api/dashboard/queue-counts
# -------------------------------
# This endpoint returns the current queue counts for dashboard display.
@app.post("/api/dashboard/queue-counts")
def dashboard_queue_counts():
    data = request.get_json()

    if not dashboard_access_allowed(data):
        return jsonify({"error": "Professor access required."}), 403

    return jsonify(qm.queue_counts())

# -------------------------------
# POST: /api/dashboard/queue
# -------------------------------
# This endpoint returns the current merged queue in service order.
@app.post("/api/dashboard/queue")
def dashboard_queue():
    data = request.get_json()

    if not dashboard_access_allowed(data):
        return jsonify({"error": "Professor access required."}), 403

    merged = qm.merged_queue()

    data_out = []
    for req in merged:
        data_out.append({
            "request_id": req.request_id,
            "student_id": req.student_id,
            "student_name": req.student_name,
            "email": req.email,
            "title": req.title,
            "is_dsl_queue": req.is_dsl_queue,
            "status": req.status,
            "joined_at": req.formatted_time,
        })

    return jsonify(data_out)


# -------------------------------
# POST: /api/dashboard/next-student
# -------------------------------
# This endpoint returns the next student who would be served.
@app.post("/api/dashboard/next-student")
def dashboard_next_student():
    data = request.get_json()

    if not dashboard_access_allowed(data):
        return jsonify({"error": "Professor access required."}), 403

    next_request = qm.peek_next()

    if next_request is None:
        return jsonify({"message": "No students are currently waiting."}), 404

    return jsonify({
        "request_id": next_request.request_id,
        "student_id": next_request.student_id,
        "student_name": next_request.student_name,
        "email": next_request.email,
        "title": next_request.title,
        "is_dsl_queue": next_request.is_dsl_queue,
        "status": next_request.status,
        "joined_at": next_request.formatted_time,
    })

# -------------------------------
# POST: /api/dashboard/serve-next
# -------------------------------
# This endpoint removes and returns the next student in the queue.
@app.post("/api/dashboard/serve-next")
def dashboard_serve_next():
    data = request.get_json()

    if not dashboard_access_allowed(data):
        return jsonify({"error": "Professor access required."}), 403

    served_request = qm.dequeue_next()

    if served_request is None:
        return jsonify({"error": "No students are currently waiting."}), 404

    # Queue a now-serving email for the student if notifications are allowed.
    if served_request.notification_ok:
        notifier.queue_now_serving_email(served_request)



    return jsonify({
        "message": "Next student served successfully.",
        "request_id": served_request.request_id,
        "student_id": served_request.student_id,
        "student_name": served_request.student_name,
        "email": served_request.email,
        "title": served_request.title,
        "is_dsl_queue": served_request.is_dsl_queue,
        "status": served_request.status,
        "joined_at": served_request.formatted_time,
    }), 200



# -------------------------------
# Entry point
# -------------------------------
# This ensures the Flask app only runs when this file is executed directly
# and not when imported as a module.
if __name__ == "__main__":

    # Run the Flask development server.
    # debug=True enables:
    # - auto-reload when code changes
    # - detailed error messages in browser
    app.run(debug=True, use_reloader=False)