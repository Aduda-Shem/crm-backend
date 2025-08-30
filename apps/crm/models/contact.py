from django.db import models
from .timestamp import TimestampedModel
from .lead import Lead

class Contact(TimestampedModel):
    """
        Contact information linked to leads.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    linked_lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='contacts')
    title = models.CharField(max_length=100, blank=True, help_text="Job title or role")
    company = models.CharField(max_length=200, blank=True, help_text="Company name")
    is_primary = models.BooleanField(default=False, help_text="Primary contact for this lead")

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"
