from typing import Callable, List, Optional, Dict, Any
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class ValidatorRegistry:
    """Registry for managing validation rules dynamically."""

    _validators: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, field: str, choices: Optional[List[str]] = None, validator: Optional[Callable] = None) -> None:
        """Register a validation rule for a field."""
        if field in cls._validators:
            logger.warning(f"Overwriting validator for field: {field}")
        cls._validators[field] = {
            'choices': choices,
            'validator': validator
        }
        logger.debug(f"Registered validator for field: {field}")

    @classmethod
    def get_choices(cls, field: str) -> Optional[List[str]]:
        """Get choices for a field, if registered."""
        config = cls._validators.get(field)
        return config['choices'] if config else None

    @classmethod
    def get_validator(cls, field: str) -> Optional[Callable]:
        """Get validator function for a field, if registered."""
        config = cls._validators.get(field)
        return config['validator'] if config else None

    @classmethod
    def validate(cls, field: str, value: Any) -> Any:
        """Validate a value using the registered validator or choices."""
        config = cls._validators.get(field)
        if not config:
            logger.warning(f"No validator registered for field: {field}")
            return value

        if config['choices'] and value and value not in config['choices']:
            logger.warning(f"Invalid value for {field}: {value}")
            raise ValidationError(f"{field} must be one of: {', '.join(config['choices'])}")
        
        if config['validator']:
            return config['validator'](value)
        
        return value

# Register default validation rules
ValidatorRegistry.register('gender', choices=['MA', 'FE', 'UD'])
ValidatorRegistry.register('grade_level', choices=[str(i) for i in range(1, 13)] + ['A-Level', 'O-Level', 'Other'])
ValidatorRegistry.register('department', choices=['Mathematics', 'Science', 'English', 'History', 'Computer Science', 'Other'])
