from django.db import models
from django.utils.translation import gettext_lazy as _
class Gender(models.TextChoices):
    """
    Enum-like class to define gender identities for user profiles.

    Used for:
        - Field choices in models (e.g., User.gender)
        - UI filters, form rendering, and analytics grouping

    Values:
        MALE        ('MA') — Identifies as male
        FEMALE      ('FE') — Identifies as female
        UNDISCLOSED ('UD') — Opted not to share

    This class is designed to support internationalization
    and inclusive filtering across the platform.
    """
    MALE = 'MA', _('Male')
    FEMALE = 'FE', _('Female')
    UNDISCLOSED = 'UD', _('Prefer not to say')