import logging
from phonenumbers import parse, is_valid_number, format_number, NumberParseException, PhoneNumberFormat
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import password_validation

from datetime import date, timedelta
import re

logger = logging.getLogger(__name__)

# Constants for validation
GENDER_CHOICES = ['MA', 'FE', 'UD']  # Male, Female, Undisclosed
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
VALID_GRADES = [str(i) for i in range(1, 13)] + ['A-Level', 'O-Level', 'Other']
VALID_DEPARTMENTS = ['Mathematics', 'Science', 'English', 'History', 'Computer Science', 'Other']
MAX_NAME_LENGTH = 50
MAX_FIELD_LENGTH = 100
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 150

# Contact Info Validators
def validate_phone_number(value: str) -> str:
    """
    Validate and format international phone numbers using the phonenumbers library.
    Returns the phone number in E164 format if valid.
    """
    if not value:
        return value
    try:
        parsed = parse(value, None)
        if not is_valid_number(parsed):
            logger.warning("Invalid phone number: %s", value)
            raise ValidationError(_('Invalid phone number'))
        return format_number(parsed, PhoneNumberFormat.E164)
    except NumberParseException:
        logger.warning("Phone number parse error: %s", value)
        raise ValidationError(_('Invalid phone number format'))

def validate_parent_email(value: str) -> str:
    """
    Validate that the parent email is a valid email address using Django's EmailValidator.
    """
    if not value:
        return value
    validator = EmailValidator(message=_('Invalid parent email address'))
    try:
        validator(value)
        if len(value) > MAX_FIELD_LENGTH:
            logger.warning("Parent email too long: %s", value)
            raise ValidationError(_('Parent email must be under %(max)s characters') % {'max': MAX_FIELD_LENGTH})
    except ValidationError as e:
        logger.warning("Invalid parent email: %s", value)
        raise ValidationError(e.message)
    return value

# Personal Info Validators
def validate_date_of_birth(value: date) -> date:
    """
    Validate that the date of birth is not in the future and the user is at least 5 years old.
    """
    if not value:
        return value
    today = date.today()
    if value > today:
        logger.warning("Future date of birth: %s", value)
        raise ValidationError(_('Date of birth cannot be in the future'))
    min_age_date = today - timedelta(days=5 * 365)  # Approx 5 years
    if value > min_age_date:
        logger.warning("Date of birth too recent: %s", value)
        raise ValidationError(_('Date of birth indicates age under 5 years'))
    return value

def validate_gender(value: str) -> str:
    """
    Validate that gender is one of the allowed choices (case-insensitive).
    """
    if not value:
        return value
    normalized = value.upper()
    if normalized not in GENDER_CHOICES:
        logger.warning("Invalid gender: %s", value)
        raise ValidationError(_('Gender must be one of: %(choices)s') % {'choices': ', '.join(GENDER_CHOICES)})
    return normalized

def validate_first_name(value: str) -> str:
    """
    Validate first name: letters, spaces, hyphens, max length.
    """
    if not value:
        return value
    if len(value) > MAX_NAME_LENGTH:
        logger.warning("First name too long: %s", value)
        raise ValidationError(_('First name must be under %(max)s characters') % {'max': MAX_NAME_LENGTH})
    if not re.match(r'^[A-Za-z\s-]+$', value):
        logger.warning("Invalid characters in first name: %s", value)
        raise ValidationError(_('First name can only contain letters, spaces, or hyphens'))
    return value

def validate_last_name(value: str) -> str:
    """
    Validate last name: letters, spaces, hyphens, max length.
    """
    if not value:
        return value
    if len(value) > MAX_NAME_LENGTH:
        logger.warning("Last name too long: %s", value)
        raise ValidationError(_('Last name must be under %(max)s characters') % {'max': MAX_NAME_LENGTH})
    if not re.match(r'^[A-Za-z\s-]+$', value):
        logger.warning("Invalid characters in last name: %s", value)
        raise ValidationError(_('Last name can only contain letters, spaces, or hyphens'))
    return value

# Authentication Validators
def validate_username(value: str) -> str:
    """
    Validate username: alphanumeric, length between 3-150, and unique.
    """
    if not value:
        return value
    if len(value) < MIN_USERNAME_LENGTH:
        logger.warning("Username too short: %s", value)
        raise ValidationError(_('Username must be at least %(min)s characters') % {'min': MIN_USERNAME_LENGTH})
    if len(value) > MAX_USERNAME_LENGTH:
        logger.warning("Username too long: %s", value)
        raise ValidationError(_('Username must be under %(max)s characters') % {'max': MAX_USERNAME_LENGTH})
    if not re.match(r'^[A-Za-z0-9_]+$', value):
        logger.warning("Invalid characters in username: %s", value)
        raise ValidationError(_('Username can only contain letters, numbers, and underscores'))
    return value


def validate_password_strength(value: str, user=None) -> str:
    """
    Validate password using Django's password validators.
    Ensure it meets the following criteria:
    - At least 8 characters long.
    - Includes at least one uppercase letter.
    - Contains at least one special character.
    - Prevents excessive repetition of the same character.
    """
    
    try:
        validate_password(value, user)
    except ValidationError as e:
        logger.warning("Password validation failed: %s", str(e))
        raise ValidationError(e.messages)

    # Check minimum length
    if len(value) < 8:
        logger.warning("Password too short: %s", value)
        raise ValidationError(_("Password must be at least 8 characters long."))

    # Check for at least one uppercase letter
    if not any(char.isupper() for char in value):
        logger.warning("Password lacks uppercase letter: %s", value)
        raise ValidationError(_("Password must contain at least one uppercase letter."))

    # Check for at least one special character (e.g., !@#$%^&*)
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        logger.warning("Password lacks a special character: %s", value)
        raise ValidationError(_("Password must contain at least one special character."))

    # Check for excessive repetition of same character
    if re.search(r"(.)\1{3,}", value):  # More than 3 repeated characters in a row
        logger.warning("Password contains excessive repeated characters: %s", value)
        raise ValidationError(_("Password must not contain the same character more than three times in a row."))

    return value

# File Upload Validators
def validate_avatar(value) -> str:
    """
    Validate that the uploaded avatar is a valid image and within size limits.
    """
    if not value:
        return value
    if value.content_type not in ALLOWED_IMAGE_TYPES:
        logger.warning("Invalid avatar content type: %s", value.content_type)
        raise ValidationError(_('Avatar must be a JPEG, PNG, or GIF image'))
    if value.size > MAX_AVATAR_SIZE:
        logger.warning("Avatar file too large: %s bytes", value.size)
        raise ValidationError(_('Avatar file size must be under %(max)s MB') % {'max': MAX_AVATAR_SIZE // (1024 * 1024)})
    return value

# Role-Specific Validators
def validate_grade_level(value: str) -> str:
    """
    Validate that grade level is one of the allowed values.
    """
    if not value:
        return value
    if value not in VALID_GRADES:
        logger.warning("Invalid grade level: %s", value)
        raise ValidationError(_('Grade level must be one of: %(choices)s') % {'choices': ', '.join(VALID_GRADES)})
    return value

def validate_department(value: str) -> str:
    """
    Validate that department is one of the allowed values.
    """
    if not value:
        return value
    if value not in VALID_DEPARTMENTS:
        logger.warning("Invalid department: %s", value)
        raise ValidationError(_('Department must be one of: %(choices)s') % {'choices': ', '.join(VALID_DEPARTMENTS)})
    return value

def validate_office_number(value: str) -> str:
    """
    Validate office number: alphanumeric, max length.
    """
    if not value:
        return value
    # if len(value) > MAX_FIELD_LENGTH:
    #     logger.warning("Office number too long: %s", value)
    #     raise ValidationError(_('Office number must be under %(max)s characters') % {'max': MAX_FIELD_LENGTH})
    # if not re.match(r'^[A-Za-z0-9\s-]+$', value):
    #     logger.warning("Invalid characters in office number: %s", value)
    #     raise ValidationError(_('Office number can only contain alphanumeric characters, spaces, or hyphens'))
    return value

def validate_qualifications(value: str) -> str:
    """
    Validate qualifications: max length, optional comma-separated format.
    """
    if not value:
        return value
    if len(value) > MAX_FIELD_LENGTH:
        logger.warning("Qualifications too long: %s", value)
        raise ValidationError(_('Qualifications must be under %(max)s characters') % {'max': MAX_FIELD_LENGTH})
    return value