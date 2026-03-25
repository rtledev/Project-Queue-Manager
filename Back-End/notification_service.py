"""
notification_service.py

Handles sending email notifcation for meetings: 
- Upcoming meeting reminders
- Position in Waitlist is top 1-3 (wahtever it will be set to)

Design choice:
We keep this VERY separte so we can later replace:
    SMTP -> API Service (Sengrid, AWS SES, which ever we end up choosing.. still researching)
"""

import os
import smtplib
from email.message import EmailMessage

from Priority_Queue import MeetingRequest

class EmailNotifier:
    """
    Handles al email notificaitons.
    """

    def __init__(self) -> None:
        # Loads configuarion from environment variables
        # Avoids hardcoding passwords in code.
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smpt_port = int(os.getenv("SMTP_PORT", "587"))
        self.smpt_user = os.getenv("SMTP_USER", "")
        self.smpt_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_host)


    def is_configured(self) -> bool:
        """
        Check if email system is ready to send
        """
        return all([
            self.smtp_host,
            self.smpt_user,
            self.smpt_password
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

            # Connect to SMTP sever
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()           # secure connection (TLS)
                server.login(self.smpt_user, self.smpt_password)
                server.send_message(msg)

            return True
        
        except Exception as e:
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