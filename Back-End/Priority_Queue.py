"""
queue_engine.py

Core backend logic for the Ps & Qs Meeting Queue Manager.

Implements a two-tier priority queue system:
    - DSL students (priority tier 1)
    - Non-DSL students (priority tier 2)
Within each tier: First-Come, First-Serve (FCFS)

No database. No GUI. Pure logic engine.
"""

#imports 
from __future__ import annotations # Allows foward type references (refrence a type prior to its initialization)

from dataclasses import dataclass, field 
# dataclass:
# Generates constructors automatically (__init__), __repr__, etc/
# Great for structured data objects (MeetingRequest in our case)
#
# field:
# Allows for the customization of default values (especially in lists and dynamic defaults)

from datetime import datetime
# Used to create a timestamp of when a meeting request was created.
# Essential for FCFS logic.

from typing import Deque, Dict, List, Optional
# These are type hints
# They help with readability and IDE auto-completion.
# 
# Deque[str] -> queue storing request IDs
# Dict[str, MeetingRequest] -> maps ID to object
# List[str] -> list of keywords
# Optional[T] -> Value may be T or None

from collections import deque
# deque = "double-eneded queue"
# Fast append/pop from both directions
# Ideal for a FIFO queue like ours.

import uuid
# Generates unique IDs.
# We use this to create unique request IDs automatically.


#------------------------------------- Custom Errors ------------------------------------- #

class QueueError(Exception):
    """Base exception for queue engine errors"""
    # All custom queue errors inherit from this
    pass

class NotFoundError(QueueError):
    """Raised when a request or student is not found in the system."""
    pass
class AlreadyWaitingError(QueueError):
    """Raised when a student already has an active waiting request."""
    pass

#------------------------------------- Data Model ------------------------------------- #

@dataclass
class MeetingRequest:
    """
    Stores akk information about one meeting request.
    THis object represents one student waiting in the system.
    """

    student_id: str       # Unique studen identifier (In our case CWID)
    student_name: str     # Student's full name
    email: str            # Email for notification purposes.
    title: str            # Topic title
    
    # default_factory=list prevents ALL objects sharing the same list

    keywords: List[str] = field(default_factory=list) # Avoid shared list across objects
    group_ok: bool = False          # Whether student allows grouping
    notification_ok:bool = False    # Student's full name
    is_dsl_queue: bool = False            # Wether student is in DSL priority tier

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    # Automatically generates a unique ID string when created.
    @property
    # Returns a formatted time (HH:MM:SS) for display purposes.
    # This is computed dynamically and always accurate (I hope).
    def formatted_time(self) -> str:
        return self.creation_time.strftime('%H:%M:%S')
    #creation_time: datetime = field(default_factory= datetime.now)
    #Timestamp of when a request was created.

    # Sequence number for FCFS ordering across both queues
    # (Engine will assign this when equeue is called)
    join_seq: int = 0

    status: str = "Waiting"
    # Default status, other values include: Completed and Cancelled
    
    notes: str = ""
    # For Professors and TA's to add custom notes.

class MeetingQueueManager:
    """
    Two-tier FCFS queue:
        - DSL queue served first
        - Non-DSL queue served second
        - FCFS perserved within each tier

    Internally:
        - Only request ID's will be stored
        - Actual reqeuest data will be stored in dictionary.
    """
    def __init__(self) -> None:     
        # These will store request_IDs in order
        self._dsl_queue: Deque[str] = deque()
        self._non_dsl_queue: Deque[str] = deque()
        
        # Fast Lookup Tables
        self.requests_by_id: Dict[str, MeetingRequest] = {} # request_id -> MeetingRequest
        self._active_requests_by_student: Dict[str, str] = {} # student_id -> request_id (only active requests)

        # GLobal counter for join order (used for later merging)
        self._join_counter: int = 0

    # Helper Methods (Internal Use Only)
    def _tier(self, req: MeetingRequest) -> Deque[str]:
        """Helper method to determine the tier of a request."""
        return self._dsl_queue if req.is_dsl_queue else self._non_dsl_queue
        
    def _remove_from_queue(self, dq: Deque[str], request_id: str) -> bool:
        """
        Helper method to remove a request ID from a given deque.
        Returns True if removed, False if not found.
        """
        try:
            dq.remove(request_id)
            return True
        except ValueError:
            return False

#------------------------------------- Data Model ------------------------------------- #
    def enqueue(self, req: MeetingRequest) -> str:
        """
        Add a new request into:
        - the correct tier queue (DSL vs Non-DSL)
        - the merged queue (arrival order)
        """
        # Check if student already has an active request
        # 1. Prevent duplicate active requests
        if req.student_id in self._active_requests_by_student:
            raise AlreadyWaitingError(f"Student '{req.student_id}' already has an active request.")
        
        # 2. Assign join sequence number (FCFS tracking)
        self._join_counter += 1
        req.join_seq = self._join_counter

        # 3. Store request data
        self.requests_by_id[req.request_id] = req
        self._active_requests_by_student[req.student_id] = req.request_id

        # 4. Add to correct tier queue
        queue = self._tier(req)
        queue.append(req.request_id)
        
        return req.request_id

    def peek_next(self) -> Optional[MeetingRequest]:
        """
        View the next request to be served without removing it from the queue.
        Returns None if no requests are waiting.
        """
        if self._dsl_queue:
            return self.requests_by_id[self._dsl_queue[0]] 
        elif self._non_dsl_queue:
            return self.requests_by_id[self._non_dsl_queue[0]]
        else:
            return None

    def dequeue_next(self) -> Optional[MeetingRequest]:
        """
        Remove and return the next request to be served.
        Returns None if no requests are waiting.
        """
        if self._dsl_queue:
            request_id = self._dsl_queue.popleft()
        elif self._non_dsl_queue:
            request_id = self._non_dsl_queue.popleft()
        else:
            return None

        req = self.requests_by_id[request_id]
        req.status = "Completed" # Update status to Completed
        self._active_requests_by_student.pop(req.student_id, None) # Remove from active tracking
        
        return req

    def cancel_by_student(self, student_id: str) -> bool:
        """
        Cancel a request by student ID.
        Returns True if a request was cancelled, False if no active request found.
        """
        
        # Step 1: Make sure the request exists
        request_id = self._active_requests_by_student.get(student_id)
        if request_id is None:
            return False # No active request for this student

        # Step 2: Remove from correct tier queue and active tracking
        # determine which queue request belongs to
        req = self.requests_by_id.get(request_id)
        if req is None:
            return False
        
        # Step 3: Remove from the correct tier queue
        queue = self._tier(req)
        removed = self._remove_from_queue(queue, request_id)
        if not removed:
            return False
        
        # Step 4: Remove the lookup tables / active tracking
        self.requests_by_id.pop(request_id, None)
        self._active_requests_by_student.pop(student_id, None)

        # Step 5: Updating le status zu Cancelled
        req.status = "Cancelled"
        
        return True
    
    #------------------------------------- Utility Methods ------------------------------------- #

    def get_position(self, student_id: str) -> Optional[int]:
        """
        Get the current position of a student's request in the merged queue.
        (Dsl students are ahead of non-DSL, but FCFS is preserved within each tier)
        Returns none if the student has no active request.
        """
        # Step 1: Get the student's active request
        request_id = self._active_requests_by_student.get(student_id)
        if not request_id:
            return None # No active request for this student

        # Step 2: Get the merged queue
        merged = self.merged_queue()

        # Step 3: Find the position of the student's request in the merged queue
        for index, req in enumerate(merged, start=1): # Start counting positions from 1
            if req.request_id == request_id:
                return index
        return None # Should never happen if data is consistent, but return None if not found

    def merged_queue(self) -> List[MeetingRequest]:
        """Shows Professors and TA's the merged queue in FCFS order (DSL first, then Non-DSL)"""
        out: List[MeetingRequest] = []
        # Add DSL requests first
        for request_id in self._dsl_queue:
            req = self.requests_by_id.get(request_id)
            if req and req.status == "Waiting":
                out.append(req)
        # Add Non-DSL requests next
        for request_id in self._non_dsl_queue:
            req = self.requests_by_id.get(request_id)
            if req and req.status == "Waiting":
                out.append(req)

        return out
