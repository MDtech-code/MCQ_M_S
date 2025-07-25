
from phonenumbers import parse, is_valid_number, format_number, NumberParseException, PhoneNumberFormat
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from PIL import Image
import os
from datetime import date, timedelta
import re
import logging
from apps.accounts.utils.validator_registry import ValidatorRegistry

logger = logging.getLogger(__name__)

# Constants for validation
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MIN_DIMENSIONS = (50, 50)          # width, height in pixels
MAX_DIMENSIONS = (2000, 2000)
MAX_NAME_LENGTH = 70
MAX_FIELD_LENGTH = 100
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 150
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5MB

def validate_person_name(value: str, field_name: str = "Name") -> str:
    """Validate a person's name or username."""
    if not value:
        return value
    if len(value) > MAX_NAME_LENGTH:
        logger.warning("%s too long: %s", field_name, value)
        raise ValidationError(_('%(field_name)s must be under %(max)s characters') % {'field_name': field_name, 'max': MAX_NAME_LENGTH})
    
    if field_name.lower() == "username":
        if len(value) < MIN_USERNAME_LENGTH:
            logger.warning("Username too short: %s", value)
            raise ValidationError(_('Username must be at least %(min)s characters') % {'min': MIN_USERNAME_LENGTH})
        if len(value) > MAX_USERNAME_LENGTH:
            logger.warning("Username too long: %s", value)
            raise ValidationError(_('Username must be under %(max)s characters') % {'max': MAX_USERNAME_LENGTH})
        if not re.match(r'^(?=.*[A-Za-z0-9])[A-Za-z0-9_.-]+$', value):
            raise ValidationError(_("Username must contain at least one letter or number and can only include letters, numbers, dots, hyphens, and underscores"))
    else:
        if not re.match(r'^[A-Za-z\s-]+$', value):
            raise ValidationError(_('%(field_name)s can only contain letters, spaces, or hyphens') % {'field_name': field_name})
    
    return value

def validate_email(value: str, field_name: str = 'Email') -> str:
    """Validate email address."""
    if not value:
        return value
    validator = EmailValidator(message=_('Invalid %(field_name)s address') % {'field_name': field_name})
    try:
        validator(value)
        if len(value) > MAX_FIELD_LENGTH:
            logger.warning("%s too long: %s", field_name, value)
            raise ValidationError(_('%(field_name)s must be under %(max)s characters') % {'max': MAX_FIELD_LENGTH, 'field_name': field_name})
    except ValidationError as e:
        logger.warning("Invalid %s: %s", field_name, value)
        raise ValidationError(e.message)
    return value

def validate_phone_number(value: str, field_name: str = "Phone Number") -> str:
    """Validate and format international phone numbers."""
    if not value:
        return value
    try:
        parsed = parse(value, None)
        if not is_valid_number(parsed):
            logger.warning("Invalid %s: %s", field_name, value)
            raise ValidationError(_('Invalid {}').format(field_name))
        return format_number(parsed, PhoneNumberFormat.E164)
    except NumberParseException:
        logger.warning("%s parse error: %s", field_name, value)
        raise ValidationError(_('Invalid {} format').format(field_name))

def validate_date_of_birth(value: date) -> date:
    """Validate date of birth."""
    if not value:
        return value
    today = date.today()
    if value > today:
        logger.warning("Future date of birth: %s", value)
        raise ValidationError(_('Date of birth cannot be in the future'))
    min_age_date = today - timedelta(days=5 * 365)
    if value > min_age_date:
        logger.warning("Date of birth too recent: %s", value)
        raise ValidationError(_('Date of birth indicates age under 5 years'))
    return value

def validate_gender(value: str) -> str:
    """Validate gender using ValidatorRegistry."""
    return ValidatorRegistry.validate('gender', value)

def validate_grade_level(value: str) -> str:
    """Validate grade level using ValidatorRegistry."""
    return ValidatorRegistry.validate('grade_level', value)

def validate_department(value: str) -> str:
    """Validate department using ValidatorRegistry."""
    return ValidatorRegistry.validate('department', value)

def validate_qualifications(value: str) -> str:
    """Validate qualifications."""
    if not value:
        return value
    if len(value) > MAX_FIELD_LENGTH:
        logger.warning("Qualifications too long: %s", value)
        raise ValidationError(_('Qualifications must be under %(max)s characters') % {'max': MAX_FIELD_LENGTH})
    if not value.strip():
        logger.warning("Qualifications empty: %s", value)
        raise ValidationError(_('Qualifications cannot be empty'))
    return value

def validate_password_strength(value: str, user=None) -> str:
    """Validate password strength."""
    try:
        validate_password(value, user)
    except ValidationError as e:
        logger.warning("Password validation failed: %s", str(e))
        raise ValidationError(e.messages)

    if len(value) < 8:
        logger.warning("Password too short: %s", value)
        raise ValidationError(_("Password must be at least 8 characters long."))
    if not any(char.isupper() for char in value):
        logger.warning("Password lacks uppercase letter: %s", value)
        raise ValidationError(_("Password must contain at least one uppercase letter."))
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        logger.warning("Password lacks a special character: %s", value)
        raise ValidationError(_("Password must contain at least one special character."))
    if re.search(r"(.)\1{3,}", value):
        logger.warning("Password contains excessive repeated characters: %s", value)
        raise ValidationError(_("Password must not contain the same character more than three times in a row."))
    return value

def validate_avatar(file):
    """Validate avatar image."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationError(_('Unsupported file extension. Allowed: %(exts)s'), params={'exts': allowed})

    if file.size > MAX_AVATAR_SIZE:
        max_mb = MAX_AVATAR_SIZE // (1024 * 1024)
        raise ValidationError(_('Avatar file size must be under %(max)d MB'), params={'max': max_mb})

    try:
        file.seek(0)
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError(_('Uploaded file is not a valid image.'))
    finally:
        file.seek(0)

    try:
        file.seek(0)
        img = Image.open(file)
        width, height = img.size
    except Exception:
        raise ValidationError(_('Cannot read image dimensions.'))

    if (width < MIN_DIMENSIONS[0] or height < MIN_DIMENSIONS[1]):
        min_w, min_h = MIN_DIMENSIONS
        raise ValidationError(_('Image is too small; minimum size is %(w)dx%(h)d pixels.'), params={'w': min_w, 'h': min_h})
    if (width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]):
        max_w, max_h = MAX_DIMENSIONS
        raise ValidationError(_('Image is too large; maximum size is %(w)dx%(h)d pixels.'), params={'w': max_w, 'h': max_h})

    file.seek(0)
    return file

def validate_document(file):
    """Validate document file for ApprovalRequest."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ValidatorRegistry.get_choices('document'):
        allowed = ', '.join(sorted(ValidatorRegistry.get_choices('document')))
        raise ValidationError(_('Unsupported file extension. Allowed: %(exts)s'), params={'exts': allowed})

    if file.size > MAX_DOCUMENT_SIZE:
        max_mb = MAX_DOCUMENT_SIZE // (1024 * 1024)
        raise ValidationError(_('Document file size must be under %(max)d MB'), params={'max': max_mb})

    return file
# import logging
# from phonenumbers import parse, is_valid_number, format_number, NumberParseException, PhoneNumberFormat
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.core.validators import EmailValidator
# from django.contrib.auth.password_validation import validate_password
# from PIL import Image
# import os


# from datetime import date, timedelta
# import re

# logger = logging.getLogger(__name__)

# # Constants for validation
# GENDER_CHOICES = ['MA', 'FE', 'UD']  # Male, Female, Undisclosed
# # ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif','image/jpg']
# MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
# ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
# MIN_DIMENSIONS    = (50, 50)          # width, height in pixels
# MAX_DIMENSIONS    = (2000, 2000)


# # ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
# VALID_GRADES = [str(i) for i in range(1, 13)] + ['A-Level', 'O-Level', 'Other']
# VALID_DEPARTMENTS = ['Mathematics', 'Science', 'English', 'History', 'Computer Science', 'Other']
# MAX_NAME_LENGTH = 70
# MAX_FIELD_LENGTH = 100
# MIN_USERNAME_LENGTH = 3
# MAX_USERNAME_LENGTH = 150



# def validate_person_name(value: str, field_name: str = "Name") -> str:
#     """
#     Validate a person's name or username, ensuring it meets character and length requirements.
#     Returns unchanged value if empty (for optional fields).
#     Args:
#         value: The string to validate.
#         field_name: The name of the field for error messaging.
#     Raises:
#         ValidationError: If the value contains invalid characters or exceeds length limits.
#     """
#     if not value:
#         return value
#     if len(value) > MAX_NAME_LENGTH:
#         logger.warning("%s too long: %s", field_name, value)
#         raise ValidationError(_('%(field_name)s must be under %(max)s characters') % {'field_name': field_name, 'max': MAX_NAME_LENGTH})
    
#     if field_name.lower() == "username":
#         if len(value) < MIN_USERNAME_LENGTH:
#             logger.warning("Username too short: %s", value)
#             raise ValidationError(_('Username must be at least %(min)s characters') % {'min': MIN_USERNAME_LENGTH})
#         if len(value) > MAX_USERNAME_LENGTH:
#             logger.warning("Username too long: %s", value)
#             raise ValidationError(_('Username must be under %(max)s characters') % {'max': MAX_USERNAME_LENGTH})
#         if not re.match(r'^(?=.*[A-Za-z0-9])[A-Za-z0-9_.-]+$', value):
#             raise ValidationError(_("Username must contain at least one letter or number and can only include letters, numbers, dots, hyphens, and underscores"))
        
#     else:
#        if not re.match(r'^[A-Za-z\s-]+$', value):
#         raise ValidationError(_('%(field_name)s can only contain letters, spaces, or hyphens') % {'field_name': field_name})
       
#     return value

# def validate_email(value:str,field_name:str = 'Name')-> str:
#     """
#     Validate that the email is a valid email address using Django's EmailValidator.
#     Allows empty values for optional fields.
#     Args:
#         value: The email string to validate.
#         field_name: The name of the field for error messaging.
#     Raises:
#         ValidationError: If the email is invalid or exceeds length limits.
#     """
#     if not value:
#         return value
#     validator = EmailValidator(message=_('Invalid %(field_name)s address') % {'field_name': field_name})
#     try:
#         validator(value)
#         if len(value) > MAX_FIELD_LENGTH:
#             logger.warning("%s too long: %s",field_name, value)
#             raise ValidationError(_('%(field_name)s must be under %(max)s characters') % {'max': MAX_FIELD_LENGTH,'field_name':field_name})
#     except ValidationError as e:
#         logger.warning("Invalid %s: %s",field_name, value)
#         raise ValidationError(e.message)
#     return value


# # Contact Info Validators
# def validate_phone_number(value: str,field_name:str = "Name") -> str:
#     """
#     Validate and format international phone numbers using the phonenumbers library.
#     Returns the phone number in E164 format if valid.

#     Args:
#         value: The phone number string to validate.
#         field_name: The name of the field for error messaging.

#     Raises:
#         ValidationError: If the phone number is invalid or improperly formatted.
#     """

#     if not value:
#         return value
#     try:
#         parsed = parse(value, None)
#         if not is_valid_number(parsed):
#             logger.warning("Invalid %s: %s",field_name, value)
#             raise ValidationError(_('Invalid {}').format(field_name))
#         return format_number(parsed, PhoneNumberFormat.E164)
#     except NumberParseException:
#         logger.warning("%s parse error: %s",field_name, value)
#         raise ValidationError(_('Invalid {} format').format(field_name))
    




# # Personal Info Validators
# def validate_date_of_birth(value: date) -> date:
#     """
#     Validate that the date of birth is not in the future and the user is at least 5 years old.
#     """
#     if not value:
#         return value
#     today = date.today()
#     if value > today:
#         logger.warning("Future date of birth: %s", value)
#         raise ValidationError(_('Date of birth cannot be in the future'))
#     min_age_date = today - timedelta(days=5 * 365)  # Approx 5 years
#     if value > min_age_date:
#         logger.warning("Date of birth too recent: %s", value)
#         raise ValidationError(_('Date of birth indicates age under 5 years'))
#     return value

# def validate_gender(value: str) -> str:
#     """
#     Validate that gender is one of the allowed choices (case-insensitive).
#     """
#     if not value:
#         return value
#     normalized = value.upper()
#     if normalized not in GENDER_CHOICES:
#         logger.warning("Invalid gender: %s", value)
#         raise ValidationError(_('Gender must be one of: %(choices)s') % {'choices': ', '.join(GENDER_CHOICES)})
#     return normalized




# def validate_password_strength(value: str, user=None) -> str:
#     """
#     Validate password using Django's password validators.
#     Ensure it meets the following criteria:
#     - At least 8 characters long.
#     - Includes at least one uppercase letter.
#     - Contains at least one special character.
#     - Prevents excessive repetition of the same character.
#     """
    
#     try:
#         validate_password(value, user)
#     except ValidationError as e:
#         logger.warning("Password validation failed: %s", str(e))
#         raise ValidationError(e.messages)

#     # Check minimum length
#     if len(value) < 8:
#         logger.warning("Password too short: %s", value)
#         raise ValidationError(_("Password must be at least 8 characters long."))

#     # Check for at least one uppercase letter
#     if not any(char.isupper() for char in value):
#         logger.warning("Password lacks uppercase letter: %s", value)
#         raise ValidationError(_("Password must contain at least one uppercase letter."))

#     # Check for at least one special character (e.g., !@#$%^&*)
#     if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
#         logger.warning("Password lacks a special character: %s", value)
#         raise ValidationError(_("Password must contain at least one special character."))

#     # Check for excessive repetition of same character
#     if re.search(r"(.)\1{3,}", value):  # More than 3 repeated characters in a row
#         logger.warning("Password contains excessive repeated characters: %s", value)
#         raise ValidationError(_("Password must not contain the same character more than three times in a row."))

#     return value


# # Role-Specific Validators
# def validate_grade_level(value: str) -> str:
#     """
#     Validate that grade level is one of the allowed values.
#     """
#     if not value:
#         return value
#     if value not in VALID_GRADES:
#         logger.warning("Invalid grade level: %s", value)
#         raise ValidationError(_('Grade level must be one of: %(choices)s') % {'choices': ', '.join(VALID_GRADES)})
#     return value

# def validate_department(value: str) -> str:
#     """
#     Validate that department is one of the allowed values.
#     """
#     if not value:
#         return value
#     if value not in VALID_DEPARTMENTS:
#         logger.warning("Invalid department: %s", value)
#         raise ValidationError(_('Department must be one of: %(choices)s') % {'choices': ', '.join(VALID_DEPARTMENTS)})
#     return value


# def validate_qualifications(value: str) -> str:
#     """
#     Validate qualifications: max length, optional comma-separated format.
#     """
#     if not value:
#         return value
#     if len(value) > MAX_FIELD_LENGTH:
#         logger.warning("Qualifications too long: %s", value)
#         raise ValidationError(_('Qualifications must be under %(max)s characters') % {'max': MAX_FIELD_LENGTH})
#     return value









# def validate_avatar(file):
#     """
#     Raise ValidationError if `file` is not a valid avatar image.
#     """

#     # -- 1) Extension check --
#     ext = os.path.splitext(file.name)[1].lower()
#     if ext not in ALLOWED_EXTENSIONS:
#         allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
#         raise ValidationError(
#             _('Unsupported file extension. Allowed: %(exts)s'),
#             params={'exts': allowed}
#         )

#     # -- 2) File size check --
#     if file.size > MAX_AVATAR_SIZE:
#         max_mb = MAX_AVATAR_SIZE // (1024 * 1024)
#         raise ValidationError(
#             _('Avatar file size must be under %(max)d MB'),
#             params={'max': max_mb}
#         )

#     # -- 3) Verify it’s a real image --
#     try:
#         # Pillow’s verify() will throw if the file is invalid or corrupted
#         file.seek(0)
#         img = Image.open(file)
#         img.verify()
#     except Exception:
#         raise ValidationError(_('Uploaded file is not a valid image.'))
#     finally:
#         file.seek(0)

#     # -- 4) (Optional) Dimension checks --
#     try:
#         file.seek(0)
#         img = Image.open(file)
#         width, height = img.size
#     except Exception:
#         raise ValidationError(_('Cannot read image dimensions.'))

#     if (width < MIN_DIMENSIONS[0] or height < MIN_DIMENSIONS[1]):
#         min_w, min_h = MIN_DIMENSIONS
#         raise ValidationError(
#             _('Image is too small; minimum size is %(w)dx%(h)d pixels.'),
#             params={'w': min_w, 'h': min_h}
#         )

#     if (width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]):
#         max_w, max_h = MAX_DIMENSIONS
#         raise ValidationError(
#             _('Image is too large; maximum size is %(w)dx%(h)d pixels.'),
#             params={'w': max_w, 'h': max_h}
#         )

#     # all good—rewind file and return
#     file.seek(0)
#     return file