import smtplib
from celery import Task
from email.message import EmailMessage
from app.core.config import settings

class SendWelcomeEmailTask(Task):
    name = "send_welcome_email_task"

    def run(self, to_email: str, subject: str, body: str):
        msg = EmailMessage() 
        msg["From"] = settings.email_address 
        msg["To"] = to_email 
        msg["Subject"] = subject 
        msg.set_content(body)

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(settings.email_address, settings.app_password)
            smtp.send_message(msg)