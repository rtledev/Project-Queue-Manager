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
        )
    """)
    
    conn.commit()       #save changes
    conn.close()

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
            creation_time,
            join_seq,
            status,
            notes,
            near_front_notified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        req.request_id,                 # unique ID
        str(req.student_id),            # ensures consistency (type)
        req.student_name,
        req.email,
        req.title,
        req.creation_time.isoformat(),   # datetime -> string
        json.dumps(req.keywords),       # convert list -> string
        int(req.group_ok),
        int(req.notification_ok),
        int(req.is_dsl_queue),
        req.join_seq,
        req.status,
        req.notes,
        int(req.near_front_notified),

    ))

    conn.commit()
    conn.close()

def get_waiting_requests() -> List[MeetingRequest]:
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
        WHERE status = 'Waiting'
        ORDER BY join_seq ASC
        -- ensures correct FCFS order
""")
    
    rows = cursor.fetchall()
    conn.close()

    requests = []

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
            creation_time=datetime.fromisoformat(row[9]),
            join_seq=row[10],
            status=row[11],
            notes=row[12],
            near_front_notified=bool(row[13])
        )

        requests.append(req)

    return requests
