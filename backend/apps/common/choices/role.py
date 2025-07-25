from django.db import models
from django.utils.translation import gettext_lazy as _

class Role(models.TextChoices):
    """
    Enum-like class to define user roles across the system.

    Used for:
        - Field choices in models (e.g., UserProfile.role)
        - Permission checks in views and decorators
        - Role-based UI rendering and filtering

    Values:
        STUDENT ('ST') — Represents student users
        TEACHER ('TE') — Represents teaching staff or mentors
        ADMIN   ('AD') — Represents platform administrators

    """

    STUDENT = 'ST', _('Student')
    TEACHER = 'TE', _('Teacher')
    ADMIN = 'AD', _('Admin')