from celery import Celery
from app.core.config import settings
from app.application.services.email_service import SendWelcomeEmailTask

celery = Celery(
    "clean",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
    broker_connection_retry_on_startup=True,
)

celery.register_task(SendWelcomeEmailTask)
