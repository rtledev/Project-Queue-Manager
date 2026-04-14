"""
persistent_queue_manager.py

This extends that in-memory queue manager so that:
EVERY opeation is also saved to the database.

Think of this as a sort brige between: Queue logic & Database
- One manager instance now represents one queue_id + session_id
- Loads waiting requests only for that queue/session
- Persists completed/cancelled timestamps
- Persists notes changes
- Supports queue reset for the current session
"""
from datetime import datetime
from typing import Optional

from Priority_Queue import MeetingQueueManager, MeetingRequest

# DB functions
from queue_db import (
    get_waiting_requests,
    insert_meeting_request,
    update_request_status,
    update_request_notes,
    expire_waiting_requests_for_session,
)

class PersistMeetingQueueManager(MeetingQueueManager):
    """
    Extends MeetingQueueManger with persistence in storing Queues

    Key ideas:
    - base class that handles logic
    - This class adds storage
    Important:
    this manager operates on exactly one queue and one session.
    """

    def __init__(self, queue_id: int, session_id: int) -> None:
        # Initialize normal queue logic first
        super().__init__()

        # Store which queue and session this manager belongs to.
        self.queue_id = queue_id
        self.session_id = session_id

        # Load only waiting requests for this queue/session.
        waiting_requests = get_waiting_requests(queue_id=self.queue_id, session_id=self.session_id)
        self.load_waiting_requests(waiting_requests)
        '''

        # Ensures DB table exists
        create_meeting_requests_table()

        # Load existing waiting requests into memory
        waiting_requests = get_waiting_requests()

        # reubuild in-memory queue from DB
        self.load_waiting_requests(waiting_requests)
        '''
    def enqueue(self, req: MeetingRequest) -> str:
        """
        Adds a requests:
        - to memory (queue logic)
        - to database (persistence)

        queue_id/session_id are assigned here so the request always belongs
        to the current professor queue and active office-hours session.
        """

        # Step 1: Assign queue_id and session_id to the request so it's always associated with the correct queue/session.
        req.queue_id = self.queue_id
        req.session_id = self.session_id

        # Step 2: Add in-memory queue
        request_id = super().enqueue(req)

        # Step 3: Save into the DB
        insert_meeting_request(req)

        return request_id
    
    def dequeue_next(self) -> Optional[MeetingRequest]:
        """
        Removes next student AND updates DB
        """

        # Step 1: Remove from memory
        req = super().dequeue_next()

        if req is not None:
            #Step 2: Mark as complted in DB
            update_request_status(
                request_id=req.request_id,
                status="Completed",
                served_at=req.served_at,
                cancelled_at=req.cancelled_at,
            )

        return req
    
    def cancel_by_student(self, student_id: str, req: MeetingRequest = None) -> bool:
        """
        Cancels request AND updates DB
        """
        student_id = str(student_id)        # keeps consistent as string in queue logic

        # Get request_id BEFORE we remove it
        request_id = self._active_requests_by_student.get(student_id)

        if request_id is None:
            return False
        
        # Step 1: Cancel in memory
        success = super(). cancel_by_student(student_id)

        if success:
        # Step 2: Update DB
            update_request_status(
                request_id=req.request_id,
                status="Cancelled",
                served_at=req.served_at,
                cancelled_at=req.cancelled_at,
            )

        return success

    def add_notes_by_student(self, student_id: str, notes: str) -> bool:
        """
        Adds or updates professor/TA notes for an active request.
        """
        req = self.get_active_request_by_student(str(student_id))
        if req is None:
            return False

        req.notes = notes
        update_request_notes(req.request_id, notes)
        return True

    def reset_current_session(self) -> None:
        """
        Resets only the current session's waiting queue.

        Behavior:
        - waiting requests are marked Cancelled in DB
        - in-memory queue is cleared
        """
        expire_waiting_requests_for_session(self.session_id)

        self._dsl_queue.clear()
        self._non_dsl_queue.clear()
        self.requests_by_id.clear()
        self._active_requests_by_student.clear()