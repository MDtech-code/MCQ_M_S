# # apps/examination/tasks.py
# from celery import shared_task
# from django.core.mail import EmailMessage
# from django.conf import settings
# from .models import Test
# from apps.content.models import Question
# from django.db.models import Q
# import logging
# logger = logging.getLogger(__name__)

# @shared_task
# def send_test_notification_task(test_id, teacher_email, action):
#     try:
#         test = Test.objects.get(id=test_id)
#         subject = f"Test {action.capitalize()} Notification"
#         message = (
#             f"Dear Teacher,\n\n"
#             f"Your test '{test.title}' has been {action}.\n"
#             f"Test ID: {test.id}\n"
#             f"Action: {action.capitalize()}\n"
#             f"Visit the platform to manage your tests.\n\n"
#             f"MCQ Test Team"
#         )
#         email = EmailMessage(
#             subject=subject,
#             body=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[teacher_email]
#         )
#         email.send()
#         logger.info(f"Notification sent to {teacher_email} for test {test_id} {action}")
#     except Exception as e:
#         logger.error(f"Failed to send notification for test {test_id}: {str(e)}")

# @shared_task
# def validate_question_filters_task(filters, on_success):
#     try:
#         # Example: Check if questions exist for filters
#         queryset = Question.objects.filter(is_active=True)
#         if 'difficulty' in filters:
#             queryset = queryset.filter(difficulty__in=filters['difficulty'])
#         if 'topics' in filters:
#             queryset = queryset.filter(topics__id__in=filters['topics'])
        
#         if not queryset.exists():
#             logger.warning(f"No questions found for filters: {filters}")
#             raise ValueError("No questions match the provided filters")
        
#         # Execute on_success callback (e.g., save test)
#         on_success()
#         logger.info(f"Question filters validated: {filters}")
#     except Exception as e:
#         logger.error(f"Failed to validate question filters: {str(e)}")