from app.application.services.email_service import SendWelcomeEmailTask
from app.application.ports.email_sender import EmailSender

class CeleryEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str) -> None:
        
        SendWelcomeEmailTask().delay(to, subject, body)
