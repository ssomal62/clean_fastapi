import smtplib
from email.message import EmailMessage

from celery import Task

from ..shared.exceptions import ExternalServiceException
from .settings import infrastructure_settings as settings
from .settings import InfrastructureSettings

class SendWelcomeEmailTask(Task):

    name = "send_welcome_email_task"

    def __init__(self, settings: InfrastructureSettings):
        self.settings = settings

    def run(self, to_email: str, subject: str, body: str):
        try:
            msg = EmailMessage() 
            msg["From"] = settings.EMAIL_ADDRESS 
            msg["To"] = to_email 
            msg["Subject"] = subject 
            msg.set_content(body)

            with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                smtp.starttls()
                smtp.login(settings.EMAIL_ADDRESS, settings.APP_PASSWORD)
                smtp.send_message(msg)
        except smtplib.SMTPException as e:
            raise ExternalServiceException(
                service_name="SMTP",
                message=f"Failed to send email to {to_email}",
                details={"error_type": type(e).__name__, "error_message": str(e)}
            )
        except Exception as e:
            raise ExternalServiceException(
                service_name="Email",
                message=f"Unexpected error while sending email to {to_email}",
                details={"error_type": type(e).__name__, "error_message": str(e)}
            )