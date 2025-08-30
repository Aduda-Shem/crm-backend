from celery import shared_task
from django.utils import timezone
from apps.crm.models import Reminder


@shared_task
def process_due_reminders():
    """
        Mark due reminders as sent. In real life, send emails/notifications.
    """
    now = timezone.now()
    qs = Reminder.objects.filter(status=Reminder.Status.PENDING, scheduled_time__lte=now)
    updated = qs.update(status=Reminder.Status.SENT)
    return updated


