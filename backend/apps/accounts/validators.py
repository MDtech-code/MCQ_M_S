# from phonenumbers import parse, is_valid_number, format_number, NumberParseException
# from phonenumbers import PhoneNumberFormat
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _


# def validate_phone_number(value: str) -> str:
#     """
#     Validate and format international phone numbers using the phonenumbers library.
#     """
#     if not value:
#         return value
    
#     try:
#         parsed = parse(value, None)
#         if not is_valid_number(parsed):
#             raise ValidationError(_('Invalid phone number'))
#         return format_number(parsed, PhoneNumberFormat.E164)
#     except NumberParseException:
#         raise ValidationError(_('Invalid phone number format'))
from phonenumbers import parse, is_valid_number, format_number, NumberParseException
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import date
from phonenumbers import PhoneNumberFormat
import re


def validate_phone_number(value: str) -> str:
    """
    Validate and format international phone numbers using the phonenumbers library.
    """
    if not value:
        return value
    
    try:
        parsed = parse(value, None)
        if not is_valid_number(parsed):
            raise ValidationError(_('Invalid phone number'))
        return format_number(parsed, PhoneNumberFormat.E164)
    except NumberParseException:
        raise ValidationError(_('Invalid phone number format'))


def validate_date_of_birth(value: date) -> date:
    """
    Validate that the date of birth is not in the future.
    """
    if value and value > date.today():
        raise ValidationError(_('Date of birth cannot be in the future.'))
    return value


def validate_gender(value: str) -> str:
    """
    Validate that gender is one of the allowed choices.
    """
    if value and value not in ['MA', 'FE', 'UD']:
        raise ValidationError(_('Gender must be "MA", "FE", or "UD".'))
    return value


def validate_avatar(value) -> None:
    """
    Validate that the uploaded avatar is a valid image and within size limits.
    """
    if value:
        valid_types = ['image/jpeg', 'image/png', 'image/gif']
        if value.content_type not in valid_types:
            raise ValidationError(_('Avatar must be a JPEG, PNG, or GIF image.'))
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise ValidationError(_('Avatar file size must be under 5MB.'))
    return value


def validate_parent_email(value: str) -> str:
    """
    Validate that the parent email is a valid email address.
    """
    if value and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', value):
        raise ValidationError(_('Invalid parent email address.'))
    return value


def validate_grade_level(value: str) -> str:
    """
    Validate that grade level is provided for students (optional validation).
    """
    if value is None or value.strip() == '':
        return value  # Optional, no strict validation
    return value


def validate_department(value: str) -> str:
    """
    Validate that department is provided for teachers/admins (optional validation).
    """
    if value is None or value.strip() == '':
        return value  # Optional, no strict validation
    return value


def validate_office_number(value: str) -> str:
    """
    Validate office number (optional, no strict validation).
    """
    return value


def validate_qualifications(value: str) -> str:
    """
    Validate qualifications (optional, no strict validation).
    """
    return value


def validate_first_name(value: str) -> str:
    """
    Validate first name (optional, no strict validation).
    """
    return value


def validate_last_name(value: str) -> str:
    """
    Validate last name (optional, no strict validation).
    """
    return value