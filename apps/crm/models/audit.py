from django.conf import settings
from django.db import models
from .timestamp import TimestampedModel


class AuditTrail(TimestampedModel):
    """Comprehensive audit trail for CRUD actions on key models."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='audit_actions')
    action = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model', 'object_id']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.action} on {self.model} by {self.user.username if self.user else 'System'}"


