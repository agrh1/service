from django.utils import timezone
from celery import shared_task
from .models import ProcessingHistory


@shared_task
def record_processing(status: str, details: str = "", ticket_id: int | None = None):
    history = ProcessingHistory.objects.create(
        ticket_id=ticket_id,
        status=status,
        details=details,
    )
    return history.id
