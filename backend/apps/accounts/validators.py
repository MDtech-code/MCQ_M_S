from phonenumbers import parse, is_valid_number, format_number, NumberParseException
from phonenumbers import PhoneNumberFormat
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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