from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access control.

    Roles:
    - MANAGER: full access
    - AGENT: restricted (no delete for leads/contacts)
    """

    class Role(models.TextChoices):
        MANAGER = 'MANAGER', 'Manager'
        AGENT = 'AGENT', 'Agent'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AGENT,
        help_text="Role controls authorization capabilities in the system.",
    )

    def is_manager(self) -> bool:
        return self.role == self.Role.MANAGER

    def is_agent(self) -> bool:
        return self.role == self.Role.AGENT


