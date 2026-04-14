"""
queue_db.py

Handles persistent storage for meeting queue requests.
This keeps the queue alive even if the program closes and restarts.
"""

import json
from datetime import datetime
from typing import List, Optional

from student_db import get_connection
from Priority_Queue import MeetingRequest

# ------------------------------------------------------------
# Table creation functions
# ------------------------------------------------------------
def create_queues_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queues (
            queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_name TEXT NOT NULL,
            professor_name TEXT NOT NULL,
            professor_email TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


def create_sessions_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS office_hours_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (queue_id) REFERENCES queues(queue_id)
        )
    """)

    conn.commit()
    conn.close()


def create_meeting_requests_table() -> None:
    """
    Creates the meeting_requests table if it does not already exists.

    Table persists of:
    - waiting students
    -completed students
    - cancelled students

    So even after restart, we still ahve history + active queue
    """
    conn = get_connection() # Opens DB connection
    cursor = conn.cursor    # create curose to run SQL

    cursor.execute(
        """
        CREATE TABLE IF NO EXISTS meeting_requests (
            request_id TEXT PRIMARY KEY,
            -- unique ID for each request (UUID)

            student_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            email TEXT NOT NULL,
            title TEXT NOT NULL,
            keywords TEXT NOT NULL DEFAULT '[]',
            group_ok INTEGER NOT NULL DEFAULT 0,
            notification_ok INTEGER NOT NULL DEFAULT 0,
            is_dsl_queue INTEGER NOT NULL DEFAULT 0,
            creation_time TEXT NOT NULL,
            join_seq INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Waiting',
            notes TEXT NOT NULL DEFAULT '',
            near_front_notified INTEGER NOT NULL DEFAULT 0
            FOREIGN KEY (queue_id) REFERENCES queues(queue_id),
            FOREIGN KEY (session_id) REFERENCES office_hours_sessions(session_id)
        )
    """)
    
    conn.commit()       #save changes
    conn.close()

def create_email_jobs_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            sent_at TEXT,
            scheduled_for TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES meeting_requests(request_id)
        )
    """)

    conn.commit()
    conn.close()

def initialize_queue_storage() -> None:
    """
    Creates all required queue-related tables.
    """
    create_queues_table()
    create_sessions_table()
    create_meeting_requests_table()
    create_email_jobs_table()

# ------------------------------------------------------------
# Queue definitions (multiple professors / multiple queues)
# ------------------------------------------------------------
def create_queue(queue_name: str, professor_name: str, professor_email: str, location: str = "") -> int:
    """
    Creates a new professor/TA queue and returns its queue_id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO queues (queue_name, professor_name, professor_email, location, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (queue_name, professor_name, professor_email, location))

    conn.commit()
    queue_id = cursor.lastrowid
    conn.close()
    return queue_id


def list_active_queues() -> List[Dict]:
    """
    Returns all currently active queues.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT queue_id, queue_name, professor_name, professor_email, location, is_active
        FROM queues
        WHERE is_active = 1
        ORDER BY professor_name, queue_name
    """)

    rows = cursor.fetchall()
    conn.close()

    out = []
    for row in rows:
        out.append({
            "queue_id": row[0],
            "queue_name": row[1],
            "professor_name": row[2],
            "professor_email": row[3],
            "location": row[4],
            "is_active": bool(row[5]),
        })
    return out


def seed_default_queues_if_empty() -> None:
    """
    CHANGED:
    Creates a couple of starter queues only if the table is empty.

    You can edit or remove these later.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM queues")
    count = cursor.fetchone()[0]

    conn.close()

    if count == 0:
        create_queue(
            queue_name="Professor Office Hours",
            professor_name="Professor Default",
            professor_email="professor@example.com",
            location="Room TBD"
        )
        create_queue(
            queue_name="TA Help Queue",
            professor_name="TA Default",
            professor_email="ta@example.com",
            location="Lab TBD"
        )


# -------------------------------------------------------------------
# Session helpers
# -------------------------------------------------------------------

def create_session(queue_id: int, title: str, start_time: datetime, end_time: datetime) -> int:
    """
    Creates a new office-hours session for a specific queue.

    Important:
    before creating a new active session, we deactivate older active sessions for that queue.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Make sure only one active session exists per queue.
    cursor.execute("""
        UPDATE office_hours_sessions
        SET is_active = 0
        WHERE queue_id = ? AND is_active = 1
    """, (queue_id,))

    cursor.execute("""
        INSERT INTO office_hours_sessions (queue_id, title, start_time, end_time, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (
        queue_id,
        title,
        start_time.isoformat(),
        end_time.isoformat(),
    ))

    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def get_active_session_for_queue(queue_id: int) -> Optional[Dict]:
    """
    Returns the active session for a queue, if one exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT session_id, queue_id, title, start_time, end_time, is_active
        FROM office_hours_sessions
        WHERE queue_id = ? AND is_active = 1
        ORDER BY session_id DESC
        LIMIT 1
    """, (queue_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "session_id": row[0],
        "queue_id": row[1],
        "title": row[2],
        "start_time": row[3],
        "end_time": row[4],
        "is_active": bool(row[5]),
    }


def end_session(session_id: int) -> None:
    """
    Marks a session inactive.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE office_hours_sessions
        SET is_active = 0
        WHERE session_id = ?
    """, (session_id,))

    conn.commit()
    conn.close()


def expire_waiting_requests_for_session(session_id: int) -> None:
    """
    CHANGED:
    Queue reset per office-hours session.

    Instead of deleting waiting rows, we cancel them and preserve history.
    """
    now_iso = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meeting_requests
        SET
            status = 'Cancelled',
            cancelled_at = ?
        WHERE session_id = ?
          AND status = 'Waiting'
    """, (now_iso, session_id))

    conn.commit()
    conn.close()


# -------------------------------------------------------------------
# Meeting request persistence
# -------------------------------------------------------------------

def insert_meeting_requests(req: MeetingRequest) -> None:
    """
    Inserts a NEW request into the database.

    This is called whenever a student join the queue.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # Convert Python fields -> DB-safe value
    cursor.execute("""
        INSERT INTO meeting_requests (
            request_id,
            student_id,
            student_name,
            email,
            title,
            keywords,
            group_ok,
            notification_ok,
            is_dsl_queue,
            queue_id,
            session_id,
            creation_time,
            join_seq,
            status,
            notes,
            served_at,
            cancelled_at,
            near_front_notified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        req.request_id,
        str(req.student_id),
        req.student_name,
        req.email,
        req.title,
        json.dumps(req.keywords),
        int(req.group_ok),
        int(req.notification_ok),
        int(req.is_dsl_queue),
        req.queue_id,
        req.session_id,
        req.creation_time.isoformat(),
        req.join_seq,
        req.status,
        req.notes,
        req.served_at.isoformat() if req.served_at else None,
        req.cancelled_at.isoformat() if req.cancelled_at else None,
        int(req.near_front_notified),
    ))

    conn.commit()
    conn.close()


def get_waiting_requests(queue_id: int, session_id: int) -> List[MeetingRequest]:
    """
    Loads ALL requests that are still "waiting".

    This is used when the app startes to revuild the queue.
    """

    conn = get_connection() # Opens DB connection
    cursor = conn.cursor    # create curose to run SQL

    # Only load waiting requests (active queue)
    cursor.execute("""
        SELECT *
        FROM meeting_requests
        WHERE queue_id = ?
        AND session_id = ?
        AND status = 'Waiting'
        ORDER BY join_seq ASC
    """, (queue_id, session_id))
    
    rows = cursor.fetchall()
    conn.close()

    requests: List[MeetingRequest] = []

    # Convert each DB row -> MR object
    for row in rows:
        req = MeetingRequest(
            student_id=row[1],
            student_name=row[2],
            email=row[3],
            title=row[4],

            # Convert JSON string -> Python list
            keywords=json.loads(row[5]) if row[5] else [],

            group_ok=bool(row[6]),
            notification_ok=bool(row[7]),
            is_dsl_queue=bool(row[8]),

            request_id=row[0],

            # converts ISO string -> datetime object
            queue_id=row[9],
            session_id=row[10],
            creation_time=datetime.fromisoformat(row[11]),
            join_seq=row[12],
            status=row[13],
            notes=row[14],
            served_at=datetime.fromisoformat(row[15]) if row[15] else None,
            cancelled_at=datetime.fromisoformat(row[16]) if row[16] else None,
            near_front_notified=bool(row[17]),
        )

        requests.append(req)

    return requests

def get_request_by_id(request_id: str) -> Optional[MeetingRequest]:
    """
    Loads a single request by ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            request_id,
            student_id,
            student_name,
            email,
            title,
            keywords,
            group_ok,
            notification_ok,
            is_dsl_queue,
            queue_id,
            session_id,
            creation_time,
            join_seq,
            status,
            notes,
            served_at,
            cancelled_at,
            near_front_notified
        FROM meeting_requests
        WHERE request_id = ?
    """, (request_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return MeetingRequest(
        request_id=row[0],
        student_id=str(row[1]),
        student_name=row[2],
        email=row[3],
        title=row[4],
        keywords=json.loads(row[5]) if row[5] else [],
        group_ok=bool(row[6]),
        notification_ok=bool(row[7]),
        is_dsl_queue=bool(row[8]),
        queue_id=row[9],
        session_id=row[10],
        creation_time=datetime.fromisoformat(row[11]),
        join_seq=row[12],
        status=row[13],
        notes=row[14],
        served_at=datetime.fromisoformat(row[15]) if row[15] else None,
        cancelled_at=datetime.fromisoformat(row[16]) if row[16] else None,
        near_front_notified=bool(row[17]),
    )


def update_request_status(
    request_id: str,
    status: str,
    served_at: Optional[datetime] = None,
    cancelled_at: Optional[datetime] = None
) -> None:
    """
    Updates request lifecycle status and timestamps.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meeting_requests
        SET
            status = ?,
            served_at = ?,
            cancelled_at = ?
        WHERE request_id = ?
    """, (
        status,
        served_at.isoformat() if served_at else None,
        cancelled_at.isoformat() if cancelled_at else None,
        request_id,
    ))

    conn.commit()
    conn.close()


def update_request_notes(request_id: str, notes: str) -> None:
    """
    CHANGED:
    Persists professor/TA notes for a request.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meeting_requests
        SET notes = ?
        WHERE request_id = ?
    """, (notes, request_id))

    conn.commit()
    conn.close()


def update_near_front_notified(request_id: str, notified: bool) -> None:
    """
    Updates whether the request has already received a near-front email.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meeting_requests
        SET near_front_notified = ?
        WHERE request_id = ?
    """, (int(notified), request_id))

    conn.commit()
    conn.close()


# -------------------------------------------------------------------
# Email job persistence for retry / background / scheduling
# -------------------------------------------------------------------

def queue_email_job(
    recipient: str,
    subject: str,
    body: str,
    request_id: Optional[str] = None,
    scheduled_for: Optional[datetime] = None
) -> int:
    """
    CHANGED:
    Stores an email job instead of requiring immediate sending.

    This allows:
    - retry on failure
    - background processing
    - scheduled reminders
    """
    if scheduled_for is None:
        scheduled_for = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO email_jobs (
            request_id,
            recipient,
            subject,
            body,
            status,
            attempt_count,
            last_error,
            created_at,
            sent_at,
            scheduled_for
        )
        VALUES (?, ?, ?, ?, 'Pending', 0, '', ?, NULL, ?)
    """, (
        request_id,
        recipient,
        subject,
        body,
        datetime.now().isoformat(),
        scheduled_for.isoformat(),
    ))

    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id


def get_due_email_jobs(limit: int = 10) -> List[Dict]:
    """
    Returns pending email jobs whose scheduled time is now or earlier.
    """
    now_iso = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT job_id, request_id, recipient, subject, body, status,
               attempt_count, last_error, created_at, sent_at, scheduled_for
        FROM email_jobs
        WHERE status = 'Pending'
          AND scheduled_for <= ?
        ORDER BY scheduled_for ASC, job_id ASC
        LIMIT ?
    """, (now_iso, limit))

    rows = cursor.fetchall()
    conn.close()

    jobs = []
    for row in rows:
        jobs.append({
            "job_id": row[0],
            "request_id": row[1],
            "recipient": row[2],
            "subject": row[3],
            "body": row[4],
            "status": row[5],
            "attempt_count": row[6],
            "last_error": row[7],
            "created_at": row[8],
            "sent_at": row[9],
            "scheduled_for": row[10],
        })
    return jobs


def mark_email_job_sent(job_id: int) -> None:
    """
    Marks an email job as sent.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE email_jobs
        SET
            status = 'Sent',
            sent_at = ?
        WHERE job_id = ?
    """, (datetime.now().isoformat(), job_id))

    conn.commit()
    conn.close()


def mark_email_job_failed(job_id: int, error_message: str, retry_delay_seconds: int = 60) -> None:
    """
    CHANGED:
    Marks an email job as still pending but increments attempt count
    and pushes the next attempt into the future.
    """
    next_try = datetime.now() + timedelta(seconds=retry_delay_seconds)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE email_jobs
        SET
            attempt_count = attempt_count + 1,
            last_error = ?,
            scheduled_for = ?
        WHERE job_id = ?
    """, (error_message, next_try.isoformat(), job_id))

    conn.commit()
    conn.close()