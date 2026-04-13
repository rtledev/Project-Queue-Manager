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


# Temporary mock data for office hours sessions.
# Right now this is hardcoded.
# Later, this will come from a database.
OFFICE_HOURS = [
    {
        "id": 1,
        "name": "Professor Jones",
        "role": "Professor",
        "subtitle": "Office Hours",
        "status": "Open"
    },
    {
        "id": 2,
        "name": "TA Smith",
        "role": "TA",
        "subtitle": "Lab Help",
        "status": "Open"
    }
]


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

    # If successful, return confirmation data.
    return jsonify({
        "message": "Joined queue successfully.",
        "request_id": request_obj.request_id,   # unique ID for this request
        "position": qm.get_position(str(data["student_id"])),  # current queue position
        "joined_at": request_obj.formatted_time  # timestamp of join
    }), 201  # 201 = Created


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
# GET: /api/dashboard/queue-counts
# -------------------------------
# This endpoint returns the current queue counts for dashboard display.
@app.get("/api/dashboard/queue-counts")
def dashboard_queue_counts():
    return jsonify(qm.queue_counts())


# -------------------------------
# GET: /api/dashboard/queue
# -------------------------------
# This endpoint returns the current merged queue in service order.
@app.get("/api/dashboard/queue")
def dashboard_queue():
    merged = qm.merged_queue()

    data = []
    for req in merged:
        data.append({
            "request_id": req.request_id,
            "student_id": req.student_id,
            "student_name": req.student_name,
            "email": req.email,
            "title": req.title,
            "is_dsl_queue": req.is_dsl_queue,
            "status": req.status,
            "joined_at": req.formatted_time,
        })

    return jsonify(data)


# -------------------------------
# GET: /api/dashboard/next-student
# -------------------------------
# This endpoint returns the next student who would be served.
@app.get("/api/dashboard/next-student")
def dashboard_next_student():
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
    served_request = qm.dequeue_next()

    if served_request is None:
        return jsonify({"error": "No students are currently waiting."}), 404

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
    app.run(debug=True)