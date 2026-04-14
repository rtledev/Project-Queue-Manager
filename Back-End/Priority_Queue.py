"""
queue_engine.py

Core backend logic for the Ps & Qs Meeting Queue Manager.

Implements a two-tier priority queue system:
    - DSL students (priority tier 1)
    - Non-DSL students (priority tier 2)
Within each tier: First-Come, First-Serve (FCFS)

No database. No GUI. Pure logic engine.
This file manages the in-memory queue logic only.
It does NOT store student records permanently.
It does NOT handle SQL directly.
It is responsible for:
    - enqueueing students into the correct queue
    - prioritizing DSL students
    - preserving FCFS order within each tier
    - tracking active requests
    - cancelling requests
    - reporting queue positions
    as of 2026-03-11, this is the core logic engine that will be used by the CLI and GUI interfaces.
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

    - queue_id identifies which professor/queue this request belongs to
    - session_id identifies which office-hours session it belongs to
    - served_at and cancelled_at preserve historical timestamps
    - near_front_notified prevents duplicate near-front notifications
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

     # each request now belongs to one queue and one session
    queue_id: int = 0
    session_id: int = 0

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    # Automatically generates a unique ID string when created.

    creation_time: datetime = field(default_factory=datetime.now)
    #creation_time: datetime = field(default_factory= datetime.now)
    #Timestamp of when a request was created.

    near_front_notified: bool = False
    # Tracks whether the student already received a "near the front" email.

    # Sequence number for FCFS ordering across both queues
    # (Engine will assign this when equeue is called)
    join_seq: int = 0

    status: str = "Waiting"
    # Default status, other values include: Completed and Cancelled
    
    notes: str = ""
    # For Professors and TA's to add custom notes.

    # lifecycle timestamps
    served_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # used to prevent repeated near-front notifications
    near_front_notified: bool = False


# -------------------------------------------------------------------
# Core Queue Manager
# ----------------------------------------------------------------

    @property
    # Returns a formatted time (HH:MM:SS) for display purposes.
    # This is computed dynamically and always accurate (I hope).
    def formatted_time(self) -> str:
        """
        Returns a formatted time string (HH:MM:SS) for when the request was created.
        Useful for display purposes in the UI and CLI.
        """
        return self.creation_time.strftime('%H:%M:%S')

class MeetingQueueManager:
    """
    Manages a two-tier meeting queue:
        1. DSL queue
        2. Non-DSL queue

    Rules:
        - DSL students are always served before non-DSL students
        - FCFS is preserved within each tier

    Internal design:
        - Queues only store request IDs
        - Full MeetingRequest objects are stored in a dictionary
        - Active student tracking prevents duplicate active requests

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

# ------------------------------------------------------
# Internal Helper Methods (Internal Use Only)
# ------------------------------------------------------

    def _tier(self, req: MeetingRequest) -> Deque[str]:
        """
        Helper method to determine the tier of a request.
        Returns the correct deque for the given request.

        DSL students go to the DSL queue.
        Non-DSL students go to the non-DSL queue.
        """
        return self._dsl_queue if req.is_dsl_queue else self._non_dsl_queue
        
    def _remove_from_queue(self, dq: Deque[str], request_id: str) -> bool:
        """
        Helper method to safely remove a request ID from a given deque.
        Returns:
            True  -> if the request ID was found and removed
            False -> if the request ID was not found
        """
        try:
            dq.remove(request_id)
            return True
        except ValueError:
            return False

    def load_waiting_requests(self, requests: List[MeetingRequest]) -> None:
        """
        Loads already- existing waiting requests into memory.

        This is used when the program starts and we want to rebuild
        the queue from the databse instead of starting empty.

        Requests should already have:
        - request_id
        - join-seq
        - status
        - creation_time
        """

        # Clear current in-memory state first.
        self._dsl_queue.clear()
        self._non_dsl_queue.clear()
        self.requests_by_id.clear()
        self._active_requests_by_student.clear()
        self._join_counter = 0

        # Load requests in gloabal join order so FCFS is preserved.
        for req in sorted(requests, key=lambda r: r.join_seq):
            if req.status != "Waiting":
                continue

            # Keep queue-side student_id consistently as a string.
            req.student_id = str(req.student_id)

            # Store the full request object.
            self.requests_by_id[req.request_id] = req

            #Track active request by student.
            self._active_requests_by_student[str(req.student_id)] = req.student_id

            # Append the request ID to the correct queue based on its tier.
            self._tier(req).append(req.request_id)

            # Keep join counter in sync with the highest known join_seq.
            if req.join_seq > self._join_counter:
                self._join_counter = req.join_seq


#------------------------------------- Data Model & Core Queue Operations ------------------------------------- #
    def enqueue(self, req: MeetingRequest) -> str:
        """
        Adds a new request to the queue.
        Steps:
            1. Reject duplicate active student requests
            2. Assign a join sequence number
            3. Store request in lookup tables
            4. Append request ID to the correct queue

        Returns:
            The generated request_id
        """
        # Check if student already has an active request
        # 1. Prevent duplicate active requests
        req.student_id = str(req.student_id)
        if req.student_id in self._active_requests_by_student:
            raise AlreadyWaitingError(f"Student '{req.student_id}' already has an active request.")
        
        # 2. Increment the global join counter and assign join sequence number (FCFS tracking)
        self._join_counter += 1
        req.join_seq = self._join_counter

        # 3. Store the full request object in the main lookup dictionary.
        self.requests_by_id[req.request_id] = req
        # Track this student as having an active request (for duplicate prevention and cancellation)
        self._active_requests_by_student[req.student_id] = req.request_id

        # 4. Add to correct tier queue, putting the request ID (not the full object) in the queue for memory efficiency.
        queue = self._tier(req)
        queue.append(req.request_id)
        
        # returns the unique request ID generated for this request, which can be used for tracking and reference in the future.
        return req.request_id

    def peek_next(self) -> Optional[MeetingRequest]:
        """
        View the next request to be served without removing it from the queue.
        Returns None if no requests are waiting.
        Priority rule:
            - If DSL queue has students, return the first DSL request
            - Otherwise return the first non-DSL request
            - If both are empty, return None
        """
        # DSL queue always has priority.
        if self._dsl_queue:
            return self.requests_by_id[self._dsl_queue[0]] 
        # If no DSL requests, check non-DSL queue.
        elif self._non_dsl_queue:
            return self.requests_by_id[self._non_dsl_queue[0]]
        # No students are waiting in either queue.
        else:
            return None

    def dequeue_next(self) -> Optional[MeetingRequest]:
        """
        Remove and return the next request to be served.
        Priority rule:
            - Serve DSL first if available
            - Otherwise serve non-DSL

        Returns:
            The completed MeetingRequest, or None if queue is empty
        """
        # Remove from DSL first if available.
        if self._dsl_queue:
            request_id = self._dsl_queue.popleft()
        # Otherwise remove from the non-DSL queue.
        elif self._non_dsl_queue:
            request_id = self._non_dsl_queue.popleft()
        # If both queues are empty, there is nothing to serve.
        else:
            return None

        # Look up the full request object.
        req = self.requests_by_id[request_id]
        req.status = "Completed" # Update status to Completed
        req.served_at = datetime.now() # Set the served_at timestamp to now
        self._active_requests_by_student.pop(req.student_id, None) # Remove from active tracking
        
        # We intentionally keep the request in requests_by_id for history/debugging.
        # It is no longer active because it is not in either queue and not in active tracker.
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
        # Remove the request ID from its queue.
        removed = self._remove_from_queue(queue, request_id)
        if not removed:
            return False
        
        # Mark the request as cancelled.
        req.status = "Cancelled"
        req.served_at = datetime.now() # Set the cancelled_at timestamp to now
        # Remove the student from active request tracking.
        self._active_requests_by_student.pop(student_id, None)

        # We intentionally keep the cancelled request in requests_by_id for history/debugging.
        return True
        '''
        This was before return true after 
        if not removed:
            return False
        # Step 4: Remove the lookup tables / active tracking
        self.requests_by_id.pop(request_id, None)
        self._active_requests_by_student.pop(student_id, None)

        # Step 5: Updating le status zu Cancelled
        req.status = "Cancelled"
        '''
    
    #------------------------------------- Utility Methods & Reporing Methods ------------------------------------- #

    def get_position(self, student_id: str) -> Optional[int]:
        """
        Get the current position of a student's request in the merged queue.
        (Dsl students are ahead of non-DSL, but FCFS is preserved within each tier)
        Position starts at 1.

        Returns:
            int position if active and waiting
            None if student is not currently waiting a.k.a no active request found for this student.
        """

        # Step 1: Get the student's active request ID (if any)
        request_id = self._active_requests_by_student.get(student_id)
        if not request_id:
            return None # No active request for this student

        # Step 2: Build the merged queue 
        merged = self.merged_queue()

        # Step 3: Find the position of the student's request in the merged queue
        for index, req in enumerate(merged, start=1): # Start counting positions from 1
            if req.request_id == request_id:
                return index
            
        # If not found, return None as a safety fallback
        return None # Should never happen if data is consistent, but return None if not found

    def merged_queue(self) -> List[MeetingRequest]:
        """
        Returns the visible queue in current service order.

        Current behavior:
            - all waiting DSL students first
            - then all waiting non-DSL students

        Note:
            This is NOT yet a true global FCFS merge across both tiers.
            It is a tiered view with FCFS preserved within each tier.
            also what tiered view is basically an arranged list of all waiting requests with DSL students listed first 
            (in their FCFS order) followed by non-DSL students (in their FCFS order).
            MUHAHAHA anyways
        """

         # Output list to build the merged queue view.
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
    
    def has_active_request(self, student_id: str) -> bool:
        """
        Check if a student currently has an active request in the queue.
        Returns True if they have an active request, False otherwise.
        """
        return student_id in self._active_requests_by_student
    
    def queue_counts(self) -> Dict[str, int]:
        """
        Returns a dictionary with the counts of waiting requests in each queue.
        Example output: {'DSL': 3, 'Non-DSL': 5}
        """
        return {
            'DSL': len(self._dsl_queue),
            'Non-DSL': len(self._non_dsl_queue),
            'Total': len(self._dsl_queue) + len(self._non_dsl_queue)
        }

    def get_active_request_by_student(self, student_id: str) -> Optional[MeetingRequest]:
        """
        Return the active waiting request object for a student if one exists.
        """
        student_id = str(student_id)
        request_id = self._active_requests_by_student.get(student_id)
        if request_id is None:
            return None
        return self.requests_by_id.get(request_id)