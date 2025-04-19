# # apps/examination/signals.py
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from .models import Test
# import logging
# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Test)
# def log_test_save(sender, instance, created, **kwargs):
#     action = "created" if created else "updated"
#     logger.info(f"Test {instance.id} {action} by {instance.creator.email if instance.creator else 'unknown'}")

# @receiver(post_delete, sender=Test)
# def log_test_delete(sender, instance, **kwargs):
#     logger.info(f"Test {instance.id} deleted by {instance.creator.email if instance.creator else 'unknown'}")