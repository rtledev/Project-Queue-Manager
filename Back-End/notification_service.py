"""
notification_service.py

Handles sending email notifcation for meetings: 
- Upcoming meeting reminders
- Position in Waitlist is top 1-3 (wahtever it will be set to)

Design choice:
We keep this VERY separte so we can later replace:
    SMTP -> API Service (Sengrid, AWS SES, which ever we end up choosing.. still researching)
"""

import os                                       # os.getenv() lets us read environment variables like SMTP_HOST and SMTP_USER.
import smtplib                                  # smtplib is Python's built-in SMTP client library.
from email.message import EmailMessage

from Priority_Queue import MeetingRequest

# Optional: load .env here instead of main startup if you want this file to be self-contained.
from dotenv import load_dotenv
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
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_host)


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
        """
        Sends a basic email
        Returns True if successful, False otherwise
        """

        # If not configured, skip send
        if not self.is_configured():
            print("Email system is not configured. Skipping email.")
            return False
        
        try:
            # Building email message
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = to_email
            msg.set_content(body)

            # Connect to SMTP sever
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()           # secure connection (TLS)
                server.login(self.smtp_user, self.smtp_password)    # Log in using the configured SMTP credentials.
                server.send_message(msg)                            # Send the message.

            return True
        
        except Exception as e:
             # For now, print the error and return False.
            # Later this can be logged to a file or retry queue.
            print(f"Email failed: {e}")
            return False
        
    def send_join_confirmation(self, req: MeetingRequest, position: int) -> bool:
        """
        Email sent when student joins queue.
        """

        subject = "Queue Confirmation"

        body = (
            f"Hello {req.student_name},\n"
            f"~~~~~~~~~~~~~~~~~~~~~"
            f"You are now in the queue.\n"
            f"Position: {position}\n"
            f"Topic: {req.title}\n"
            f"~~~~~~~~~~~~~~~~~~~~~"
            f"Please wait for your turn."
        )

        return self.send_email(req.email, subject, body)
    
    def send_near_front_notification(self, req: MeetingRequest, position: int) -> bool:
        """
        Email whern student is near the front
        """
        subject = "You're Almost Up!"

        body = (
            f"Hello {req.student_name},\n"
            f"You are near the front of the waitlist.\n"
            f"Position: {position}\n"
            f"Please be ready!"
        )

        return self.send_email(req.email, subject, body)
    
    def send_now_serving_email(self, req: MeetingRequest, position: int) -> bool:
        """
        Sends an email when the student is now being served.
        """
        subject = "Ps & Qs - You Are Now Being Served"

        body = (
            f"Hello {req.student_name},\n\n"
            f"~~~~~~~~~~~~~~~~~~~~~"
            f"It is now your turn.\n"
            f"Position: {position}\n"
            f"Topic: {req.title}\n\n"
            f"~~~~~~~~~~~~~~~~~~~~~"
            f"Please join the office hours now."
        )

        return self.send_email(req.email, subject, body)