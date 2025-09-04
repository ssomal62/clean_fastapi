from celery import Celery


def create_celery_app(
    broker: str, 
    backend: str, 
    email_task, 
    broker_connection_retry_on_startup: bool = True
    ) -> Celery:
    """Celery 앱 생성 팩토리 함수"""

    celery = Celery(
        "clean",
        broker=broker,
        backend=backend,
        broker_connection_retry_on_startup=broker_connection_retry_on_startup,
    )
    
    celery.register_task(email_task)
    return celery
