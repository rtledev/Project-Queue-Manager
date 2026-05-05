"""
wait_time_estimator.py

Creates estimated wait times for students in the queue.
- Each person is assigned a random estimated service time between 7-12 minutes.
- Wait time is cumulative.
- Position 1 means the student may be called soon, but we still show an estimated range/time :)
"""

import random
from typing import Dict, List

from Priority_Queue import MeetingRequest

MIN_MINUTES_PER_PERSON = 7
MAX_MINUTES_PER_PERSON = 12

def build_wait_time_estimates( merged_queue: List[MeetingRequest]) -> Dict[str, int]:
        # Builds an estimated wait time for every student in the queue
        # Returns a dict of requested_id -> estimated info

        estimates = {}

        cumulative_minutes = 0

        for req in merged_queue:
            cumulative_minutes += req.estimated_service_minutes

            estimates[req.request_id] = cumulative_minutes

        return estimates