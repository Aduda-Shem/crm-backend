from django.db import models


class TimestampedModel(models.Model):
    """
        Abstract base model to track creation and update times.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

