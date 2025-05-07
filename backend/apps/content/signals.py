from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Subject, Topic, Question, QuestionApproval
from django.core.cache import cache

import logging
logger = logging.getLogger(__name__)





@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Question)
def invalidate_question_cache(sender, instance, **kwargs):
    """Invalidate question list cache on save/delete."""
    cache.delete_pattern(f"question_list:{instance.created_by.id}:*")
    logger.debug(f"Invalidated question cache for user {instance.created_by.id}")

@receiver(post_save, sender=QuestionApproval)
def invalidate_approval_cache(sender, instance, **kwargs):
    """Invalidate question list cache on approval change."""
    cache.delete_pattern(f"question_list:{instance.question.created_by.id}:*")
    logger.debug(f"Invalidated approval cache for user {instance.question.created_by.id}")

@receiver(post_save, sender=Subject)
@receiver(post_delete, sender=Subject)
def invalidate_subject_cache(sender, instance, **kwargs):
    """Invalidate subject cache on save/delete."""
    cache.delete('subjects_all')
    logger.debug("Invalidated subject cache")

@receiver(post_save, sender=Topic)
@receiver(post_delete, sender=Topic)
def invalidate_topic_cache(sender, instance, **kwargs):
    """Invalidate topic cache on save/delete."""
    cache.delete('topics_all')
    logger.debug("Invalidated topic cache")

@receiver(post_save, sender=Subject)
def log_subject_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(f"Subject {instance.id} {action}")

@receiver(post_save, sender=Topic)
def log_topic_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(f"Topic {instance.id} {action} in subject {instance.subject.name}")

@receiver(post_save, sender=Question)
def log_question_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(f"Question {instance.id} {action} by {instance.created_by.email if instance.created_by else 'unknown'}")

@receiver(post_save, sender=QuestionApproval)
def log_approval_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(f"Approval {instance.id} {action} for question {instance.question.id} ({instance.status})")

@receiver(post_delete, sender=Subject)
def log_subject_delete(sender, instance, **kwargs):
    logger.info(f"Subject {instance.id} deleted")

@receiver(post_delete, sender=Topic)
def log_topic_delete(sender, instance, **kwargs):
    logger.info(f"Topic {instance.id} deleted from subject {instance.subject.name}")

@receiver(post_delete, sender=Question)
def log_question_delete(sender, instance, **kwargs):
    logger.info(f"Question {instance.id} deleted by {instance.created_by.email if instance.created_by else 'unknown'}")