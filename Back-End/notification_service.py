"""
notification_service.py

Handles sending email notifcation for meetings: 
- Upcoming meeting reminders
- Position in Waitlist is top 1-3 (wahtever it will be set to)

Design choice:
We keep this VERY separte so we can later replace:
    SMTP -> API Service (Sengrid, AWS SES, which ever we end up choosing.. still researching)

- Uses .env via python-dotenv
- Supports immediate queueing of email jobs instead of direct send only
- Supports retry behavior through email_jobs table
- Supports background worker thread
- Supports scheduled reminder emails
- Supports "now serving" emails
"""

import os                                       # os.getenv() lets us read environment variables like SMTP_HOST and SMTP_USER.
import smtplib                                  # smtplib is Python's built-in SMTP client library.
import threading
import time
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Optional

# Optional: load .env here instead of main startup if you want this file to be self-contained.
# Make dotenv optional so the program does not crash if the package is missing.
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        """
        Fallback no-op function if python-dotenv is not installed.
        This lets the rest of the program still run.
        """
        pass

from Priority_Queue import MeetingRequest
from queue_db import (
    queue_email_job,
    get_due_email_jobs,
    mark_email_job_sent,
    mark_email_job_failed,
    get_request_by_id,
    update_near_front_notified,
    get_waiting_requests,
)

# Load variables from .env so SMTP settings are not hardcoded.
load_dotenv()

class EmailNotifier:
    """
    Responsible for sending queue-related emails.

    Environment variables expected:
        SMTP_HOST
        SMTP_PORT
        SMTP_USER
        SMTP_PASSWORD
        SMTP_FROM
    """


    def __init__(self) -> None:
        # Loads configuarion from environment variables
        # Read email settings from environment variables.
        # This keeps secrets OUT of source code.
        # Avoids hardcoding passwords in code.
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)


    def is_configured(self) -> bool:
        """
        Returns True only if all required email settings are present.
        Check if email system is ready to send
        """
        return all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.smtp_from,
        ])
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
  
    #   Sends a basic email
    #   Returns True if successful, False otherwise
    #   This is used by the background worker when processing queued email jobs.

        if not self.is_configured():
            print("Email system is not configured. Skipping email.")
            print("SMTP_HOST:", self.smtp_host)
            print("SMTP_USER:", self.smtp_user)
            print("SMTP_FROM:", self.smtp_from)
            return False

        try:
            print(f"Preparing to send email to {to_email} with subject: {subject}")

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = to_email
            msg.set_content(body)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                print("Connected to SMTP server.")
                server.starttls()
                print("TLS started.")
                server.login(self.smtp_user, self.smtp_password)
                print("SMTP login successful.")
                server.send_message(msg)
                print("Email sent successfully.")

            return True

        except Exception as e:
            print(f"Email failed: {e}")
            return False
    
    def get_current_position_from_db(self, request_id: str) -> Optional[int]:
        """
        Recalculates the student's current queue position from the database.

        This prevents stale email positions.
        """
        req = get_request_by_id(request_id)

        if req is None or req.status != "Waiting":
            return None

        waiting_requests = get_waiting_requests(
            queue_id=req.queue_id,
            session_id=req.session_id,
        )

        # Match your current queue rule:
        # DSL first, then Non-DSL.
        merged = (
            [r for r in waiting_requests if r.is_dsl_queue]
            + [r for r in waiting_requests if not r.is_dsl_queue]
        )

        for index, current_req in enumerate(merged, start=1):
            if current_req.request_id == request_id:
                return index

        return None

# -------------Email templates → queued jobs-------------------


    def queue_join_confirmation(self, req: MeetingRequest, position: int) -> bool:
        """
        Email sent when student joins queue.
        Queues a join-confirmation email to be sent soon.
        """
        subject = "Ps & Qs - Queue Confirmation"

        body = (
            f"Hello {req.student_name},\n"
            f"~~~~~~~~~~~~~~~~~~~~~"
            f"You are now in the queue.\n"
            f"Position: {position}\n"
            f"Joined at: {req.formatted_time}\n"
            f"Topic: {req.title}\n"
            f"~~~~~~~~~~~~~~~~~~~~~"
            f"Please wait for your turn."
        )

        return queue_email_job(
            recipient=req.email,
            subject=subject,
            body=body,
            request_id=req.request_id,
            scheduled_for=datetime.now(),
        )
    
    def queue_near_front_notification(self, req: MeetingRequest, position: int) -> bool:
        """
        Email whern student is near the front
        """
        subject = "Ps & Qs - You're Almost Up!"

        body = (
            f"Hello {req.student_name},\n\n"
            f"====================================\n"
            f"        Ps & Qs Queue Confirmation\n"
            f"====================================\n\n"
            f"You are near the front of the waitlist.\n"
            f"Topic: {req.title}\n"
            f"Current Position: {position}\n"
            f"Joined at: {req.formatted_time}\n\n"
            f"Please be ready!\n\n"
            f"Thank you,\n"
            
        )

        job_id = queue_email_job(
            recipient=req.email,
            subject=subject,
            body=body,
            request_id=req.request_id,
            scheduled_for=datetime.now(),
        )

        # CHANGEd:
        # Prevent duplicate near-front notifications.
        req.near_front_notified = True
        update_near_front_notified(req.request_id, True)

        return job_id
    
    def queue_now_serving_email(self, req: MeetingRequest) -> bool:
        """
        Sends an email when the student is now being served.
        """
        subject = "Ps & Qs - You Are Now Being Served"

        body = (
            f"Hello {req.student_name},\n\n"
            f"====================================\n"
            f"        Ps & Qs Queue Confirmation\n"
            f"====================================\n\n"
            f"It is now your turn.\n\n"
            f"Topic: {req.title}\n"
            f"Joined at: {req.formatted_time}\n\n"
            f"Please join the office hours now.\n\n"
            f"Thank you,\n"
            f"Ps & Qs Meeting Queue Manager\n"
        )

        return queue_email_job(
            recipient=req.email,
            subject=subject,
            body=body,
            request_id=req.request_id,
            scheduled_for=datetime.now(),
        )
    def queue_waiting_reminder(self, req: MeetingRequest, delay_minutes: int = 10) -> int:
            """
            CHANGED:
            Queues a scheduled reminder to be sent in the future.

            This is a simple first version of scheduled reminders.
            """
            subject = "Ps & Qs Queue Reminder"
            body = (
                f"Hello {req.student_name},\n\n"
                f"This is a reminder that you are still in the queue.\n"
                f"Topic: {req.title}\n\n"
                f"You will receive another update when you are closer to the front."
            )

            scheduled_for = datetime.now() + timedelta(minutes=delay_minutes)

            return queue_email_job(
                recipient=req.email,
                subject=subject,
                body=body,
                request_id=req.request_id,
                scheduled_for=scheduled_for,
            )


def process_due_email_jobs(notifier: EmailNotifier, limit: int = 10) -> None:
    """
    CHANGED:
    Processes due pending email jobs.

    Retry behavior:
    - if sending fails, the job remains pending
    - scheduled_for is pushed into the future
    - attempt_count increases
    """

    print("Checking for due email jobs...")
    jobs = get_due_email_jobs(limit=limit)
    print("Due email jobs found:", len(jobs))

    jobs = get_due_email_jobs(limit=limit)

    for job in jobs:
        request_id = job["request_id"]

        # If this job is linked to a request, make sure that request still makes sense.
        # Example:
        # scheduled reminder should not fire for a completed/cancelled request.
        if request_id:
            req = get_request_by_id(request_id)

            # If the request cannot be found in queue_db, do not silently discard the job.
            # For the current prototype, some queue actions are still managed in memory,
            # so we allow the queued email to send using the stored job data.
            if req is None:
                req = None

            # Only suppress reminder emails if we were able to find the request
            # and confirm that it is no longer waiting.
            if req is not None and req.status != "Waiting" and "Reminder" in job["subject"]:
                mark_email_job_sent(job["job_id"])
                continue

        # Start with stored body
        body = job["body"]

        # Dynamically update position-based emails BEFORE sending
        if request_id and (
            "Queue Confirmation" in job["subject"] or
            "Almost Up" in job["subject"]
        ):
            req = get_request_by_id(request_id)
            position = notifier.get_current_position_from_db(request_id)

            if req is not None and position is not None:
                body = (
                    f"Hello {req.student_name},\n\n"
                    f"==============================\n"
                    f"Ps & Qs Queue Update\n"
                    f"==============================\n\n"
                    f"Topic: {req.title}\n"
                    f"Current Position: {position}\n"
                    f"Joined at: {req.formatted_time}\n\n"
                    f"Please be ready when your turn is close.\n"
                )

        print(f"Attempting to send queued email to {job['recipient']} with subject: {job['subject']}")

        # Send email with UPDATED body
        success = notifier.send_email(
            to_email=job["recipient"],
            subject=job["subject"],
            body=body,
        )

        if success:
            mark_email_job_sent(job["job_id"])
        else:
            mark_email_job_failed(
                job_id=job["job_id"],
                error_message="SMTP send failed",
                retry_delay_seconds=60,
            )
    def queue_join_confirmation(self, req: MeetingRequest, position: int, estimated_minutes: int = None) -> bool:
        subject = "Ps & Qs - Queue Confirmation"

        estimate_line = ""
        if estimated_minutes is not None:
            estimate_line = f"Estimated wait time: about {estimated_minutes} minutes\n"

        body = (
            f"Hello {req.student_name},\n\n"
            f"====================================\n"
            f"Ps & Qs Queue Confirmation\n"
            f"====================================\n\n"
            f"You have successfully joined the queue.\n\n"
            f"Position: {position}\n"
            f"{estimate_line}"
            f"Joined at: {req.formatted_time}\n"
            f"Topic: {req.title}\n\n"
            f"This is only an estimate and may change depending on each meeting.\n\n"
            f"Thank you,\n"
            f"Ps & Qs Meeting Queue Manager\n"
        )

        return queue_email_job(
            recipient=req.email,
            subject=subject,
            body=body,
            request_id=req.request_id,
            scheduled_for=datetime.now(),
        )

def _email_worker_loop(notifier: EmailNotifier, poll_seconds: int) -> None:
    """
    Background loop for email processing.
    """
    while True:
        process_due_email_jobs(notifier)
        time.sleep(poll_seconds)


def start_email_worker(notifier: EmailNotifier, poll_seconds: int = 10) -> threading.Thread:
    """
    Starts a daemon thread that keeps processing queued email jobs.
    """
    worker = threading.Thread(
        target=_email_worker_loop,
        args=(notifier, poll_seconds),
        daemon=True,
    )
    worker.start()
    return worker