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

import uuid
# Generates unique IDs.
# We use this to create unique request IDs automatically.

class QueueError(Exception):
    """Base exception for queue engine errors"""
    # All custom queue errors inherit from this


class NotFoundError(QueueError):
    """Raised when a request or student is not found in the system."""
    pass
class AlreadyWaitingError(QueueError):
    """Raised when a student already has an active waiting request."""
    pass

@dataclass
class MeetingRequest:
    student_id: str       # Unique studen identifier (In our case CWID)
    student_name: str     # Student's full name
    email: str            # Email for notification purposes.
    title: str            # Topic title
    keywords: List[str] = field(default_factory=list) 
    # default_factory=list prevents ALL objects sharing the same list

    group_ok: bool = False          # Whether student allows grouping
    notification_ok:bool = False    # Student's full name
    is_dsl: bool = False            # Wether student is in DSL priority tier

    request_id: str = field(defualt_factory=lambda: uuid.uuid4().hex)
    # Automatically generates a unique ID string when created.
    
    