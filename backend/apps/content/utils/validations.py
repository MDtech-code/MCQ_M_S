import re
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from fuzzywuzzy import fuzz
from spellchecker import SpellChecker
from django.core.cache import cache
import string




logger = logging.getLogger(__name__)

# Constants
ALLOWED_QUESTION_TYPES = ['MCQ']
DIFFICULTY_CHOICES = ['E', 'M', 'H']
ALLOWED_SOURCES = ['manual', 'auto_nlp']
MAX_SUBJECT_NAME_LENGTH = 100
MAX_TOPIC_NAME_LENGTH = 100
MAX_QUESTION_TEXT_LENGTH = 1000



def log_validation_error(field, value, message):
    """Log validation errors consistently."""
    logger.warning(f"Validation failed for {field}: {value}. {message}")

def validate_subject_name(value: str) -> str:
    """Validate subject name: letters, spaces, hyphens, max length."""
    if not value:
        return value
    if len(value) > MAX_SUBJECT_NAME_LENGTH:
        log_validation_error("subject_name", value, f"Must be under {MAX_SUBJECT_NAME_LENGTH} characters")
        raise ValidationError(_('Subject name must be under %(max)s characters') % {'max': MAX_SUBJECT_NAME_LENGTH})
    if not re.match(r'^[A-Za-z\s-]+$', value):
        log_validation_error("subject_name", value, "Only letters, spaces, or hyphens allowed")
        raise ValidationError(_('Subject name can only contain letters, spaces, or hyphens'))
    return value

def validate_topic_name(value: str) -> str:
    """Validate topic name: alphanumeric, spaces, max length."""
    if not value:
        return value
    if len(value) > MAX_TOPIC_NAME_LENGTH:
        log_validation_error("topic_name", value, f"Must be under {MAX_TOPIC_NAME_LENGTH} characters")
        raise ValidationError(_('Topic name must be under %(max)s characters') % {'max': MAX_TOPIC_NAME_LENGTH})
    if not re.match(r'^[A-Za-z0-9\s]+$', value):
        log_validation_error("topic_name", value, "Only alphanumeric and spaces allowed")
        raise ValidationError(_('Topic name can only contain alphanumeric characters and spaces'))
    return value

def validate_question_text(value: str) -> str:
    """Validate question text: max length, suspicious content, typos, duplicates."""
    if not value:
        log_validation_error("question_text", value, "Question text is required")
        raise ValidationError(_('Question text is required'))
    if len(value) > MAX_QUESTION_TEXT_LENGTH:
        log_validation_error("question_text", value, f"Must be under {MAX_QUESTION_TEXT_LENGTH} characters")
        raise ValidationError(_('Question text must be under %(max)s characters') % {'max': MAX_QUESTION_TEXT_LENGTH})
    
    # Suspicious content
    suspicious_patterns = [
        r'\b(fuck|shit|damn)\b',
        r'^[a-zA-Z0-9\s\?\.]{0,5}$',
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            log_validation_error("question_text", value, "Invalid or inappropriate content")
            raise ValidationError(_('Question text appears invalid or inappropriate'))
    
    # Typo check
    spell = SpellChecker()
    cache_key = "spellchecker_common_words"
    common_words = cache.get(cache_key, set())
    words = value.translate(str.maketrans('', '', string.punctuation)).split()
    typos = [
        word for word in words
        if word.lower() not in spell and word not in common_words and not word.isdigit() and len(word) > 3
    ]
    if typos:
        log_validation_error("question_text", value, f"Potential typos: {', '.join(typos)}")
        raise ValidationError(_('Potential typos detected: %(typos)s') % {'typos': ', '.join(typos)})
    common_words.update(words)
    cache.set(cache_key, common_words, timeout=86400)  # 24 hours
    
    return value

def validate_question_type(value: str) -> str:
    """Validate question type against allowed types."""
    if value not in ALLOWED_QUESTION_TYPES:
        log_validation_error("question_type", value, f"Must be one of {ALLOWED_QUESTION_TYPES}")
        raise ValidationError(_('Question type must be one of: %(types)s') % {'types': ', '.join(ALLOWED_QUESTION_TYPES)})
    return value

def validate_difficulty(value: str) -> str:
    """Validate difficulty against choices."""
    if value not in DIFFICULTY_CHOICES:
        log_validation_error("difficulty", value, f"Must be one of {DIFFICULTY_CHOICES}")
        raise ValidationError(_('Difficulty must be one of: %(choices)s') % {'choices': ', '.join(DIFFICULTY_CHOICES)})
    return value

def validate_options(value: dict) -> dict:
    """Validate options are correctly formatted and non-empty."""
    
    # Check if it's a dictionary with required keys
    expected_keys = {'A', 'B', 'C', 'D'}
    if not isinstance(value, dict) or set(value.keys()) != expected_keys:
        raise ValidationError("Options must be a dict with keys A, B, C, D")

    # Ensure all values are non-empty
    for key, val in value.items():
        if not val.strip():
            raise ValidationError(_('Option %(key)s cannot be empty') % {'key': key})

    return value
def validate_source(value: str) -> str:
    """Validate source against allowed values."""
    if value not in ALLOWED_SOURCES:
        log_validation_error("source", value, f"Must be one of {ALLOWED_SOURCES}")
        raise ValidationError(_('Source must be one of: %(sources)s') % {'sources': ', '.join(ALLOWED_SOURCES)})
    return value

def validate_topic_subject_consistency(topics):
    """Ensure all topics belong to the same subject."""
    if topics:
        subject_ids = set(topic.subject_id for topic in topics)
        if len(subject_ids) > 1:
            log_validation_error("topics", topics, "All topics must belong to the same subject")
            raise ValidationError(_('All topics must belong to the same subject'))
    return topics

def check_duplicate_question(question_text, topics, instance=None):
    from apps.content.models import Question
    """Check for duplicate questions based on text similarity."""
    if not topics:
        return
    cache_key = f"question_text_hash:{':'.join(str(t.id) for t in topics)}"
    cached_hashes = cache.get(cache_key, [])
    question_hash = hash(question_text.lower())
    if question_hash in cached_hashes:
        log_validation_error("question_text", question_text, "Duplicate question detected via cache")
        raise ValidationError(_('Question is too similar to an existing one'))
    
    existing_questions = Question.objects.filter(topics__in=topics).values('question_text').distinct()
    if instance:
        existing_questions = existing_questions.exclude(id=instance.id)
    
    for existing_text in existing_questions:
        if fuzz.ratio(question_text.lower(), existing_text['question_text'].lower()) > 90:
            log_validation_error("question_text", question_text, "Too similar to existing question")
            raise ValidationError(_('Question is too similar to an existing one'))
    
    cached_hashes.append(question_hash)
    cache.set(cache_key, cached_hashes, timeout=86400)  # 24 hours