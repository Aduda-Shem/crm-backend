from django.db import models

from django.conf import settings
from .lead import Lead
from .timestamp import TimestampedModel


class Reminder(TimestampedModel):
    """
        Scheduled reminders for follow-ups and tasks.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='reminders')
    message = models.CharField(max_length=255)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(
        max_length=50,
        choices=[
            ('FOLLOW_UP', 'Follow-up'),
            ('CALL', 'Call Reminder'),
            ('MEETING', 'Meeting Reminder'),
            ('TASK', 'Task Reminder'),
        ],
        default='FOLLOW_UP'
    )

    class Meta:
        ordering = ['scheduled_time']

    def __str__(self) -> str:
        return f"Reminder: {self.message} for {self.lead.name}"
