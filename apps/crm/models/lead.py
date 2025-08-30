from django.conf import settings
from django.db import models
from .timestamp import TimestampedModel


class Lead(TimestampedModel):
    """
        Represents a sales lead owned by a user.
    """
    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        WON = 'WON', 'Won'
        LOST = 'LOST', 'Lost'

    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leads')
    description = models.TextField(blank=True, help_text="Lead description and details")
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Potential deal value")
    source = models.CharField(max_length=100, blank=True, help_text="Lead source (e.g., website, referral, cold call)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


