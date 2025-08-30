from django.db import models
from django.conf import settings
from .contact import Contact
from .timestamp import TimestampedModel


class Correspondence(TimestampedModel):
    """
        Log of all communications with contacts.
    """
    class Type(models.TextChoices):
        EMAIL = 'email', 'Email'
        CALL = 'call', 'Call'
        MEETING = 'meeting', 'Meeting'
        TEXT = 'text', 'Text Message'
        LINKEDIN = 'linkedin', 'LinkedIn'
        OTHER = 'other', 'Other'

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='correspondences')
    type = models.CharField(max_length=20, choices=Type.choices)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='correspondences')
    outcome = models.CharField(
        max_length=100,
        blank=True,
        help_text="Outcome of the communication"
    )
    duration = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Duration in minutes (for calls/meetings)"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.type.title()} with {self.contact.name}"
