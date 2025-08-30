from django.conf import settings
from django.db import models
from .lead import Lead
from .timestamp import TimestampedModel


class Note(TimestampedModel):
    """
        Notes attached to leads for tracking progress and interactions.
    """
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='notes')
    note_type = models.CharField(
        max_length=50, 
        choices=[
            ('GENERAL', 'General'),
            ('CALL', 'Call Note'),
            ('MEETING', 'Meeting Note'),
            ('FOLLOW_UP', 'Follow-up'),
            ('OPPORTUNITY', 'Opportunity'),
        ],
        default='GENERAL'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Note by {self.created_by.username} on {self.lead.name}"
