"""
persistent_queue_manager.py

This extends that in-memory queue manager so that:
EVERY opeation is also saved to the database.

Think of this as a sort brige between: Queue logic & Database
"""

from Priority_Queue import MeetingQueueManager, MeetingRequest

# DB functions
from queue_db import (
    create_meeting_requests_table,
    get_waiting_requests,
    insert_meeting_request,
    update_request_status,
)

class PersistMeetingQueueManager(MeetingQueueManager):
    """
    Extends MeetingQueueManger with persistence in storing Queues

    Key ideas:
    - base class that handles logic
    - This class adds storage
    """

    def __init__(self) -> None:
        # Initialize normal queue logic first
        super().__init__()

        # Ensures DB table exists
        create_meeting_requests_table()

        # Load existing waiting requests into memory
        waiting_requests = get_waiting_requests()

        # reubuild in-memory queue from DB
        self.load_waiting_requests(waiting_requests)
    
    def enqueue(self, req: MeetingQueueManager) -> str:
        """
        Adds a requests:
        - to memory (queue logic)
        - to database (persistence)
        """

        # Step 1: Add in-memory queue
        request_id = super().enqueue(req)

        # Step 2: Save into the DB
        insert_meeting_request(req)

        return request_id
    
    def dequeue_next(self):
        """
        Removes next student AND updates DB
        """

        # Step 1: Remove from memory
        req = super().dequeue_next()

        if req is not None:
            #Step 2: Mark as complted in DB
            update_request_status(req.request_id, "Completed")

        return req
    
    def cancel_by_student(self, student_id) -> bool:
        """
        Cancels request AND updates DB
        """

        student_id = str(student_id)        # keeps consistent as string in queue logic

        # Get request_id BEFORE we remove it
        request_id = self._active_requests_by_student(student_id)

        if request_id is None:
            return False
        
        # Step 1: Cancel in memory
        success = super(). cancel_by_student(student_id)

        if success:
        # Step 2: Update DB
            update_request_status(request_id, "Cancelled")


        return success
