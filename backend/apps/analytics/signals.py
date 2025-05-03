

# from apps.examination.models import Test
# # apps/analytics/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from apps.examination.models import TestAttempt
# from apps.analytics.models import StudentProgress
# from django.db.models import Avg, Count
# from apps.content.models import Topic
# from .models import TestAnalytics,StudentProgress

# @receiver(post_save, sender=TestAttempt)
# def update_student_progress(sender, instance, **kwargs):
#     if instance.score is not None:  # Only update after submission
#         student = instance.student
#         for subject in instance.test.subjects.all():
#             progress, created = StudentProgress.objects.get_or_create(
#                 student=student,
#                 subject=subject,
#                 defaults={'average_score': 0}
#             )
#             progress.update_progress()
#             # Update strengths/weaknesses
#             responses = instance.studentresponse_set.all()
#             topic_performance = {}
#             for response in responses:
#                 for topic in response.question.topics.all():
#                     if topic.id not in topic_performance:
#                         topic_performance[topic.id] = {'correct': 0, 'total': 0}
#                     topic_performance[topic.id]['total'] += 1
#                     if response.is_correct:
#                         topic_performance[topic.id]['correct'] += 1
            
#             progress.strength_topics.clear()
#             progress.weakness_topics.clear()
#             for topic_id, stats in topic_performance.items():
#                 topic = Topic.objects.get(id=topic_id)
#                 accuracy = stats['correct'] / stats['total'] * 100
#                 if accuracy >= 80:
#                     progress.strength_topics.add(topic)
#                 elif accuracy < 50:
#                     progress.weakness_topics.add(topic)





# @receiver(post_save, sender=Test)
# def create_test_analytics(sender, instance, created, **kwargs):
#     if created:
#         TestAnalytics.objects.create(test=instance)

# @receiver(post_save, sender=TestAttempt)
# def update_test_analytics(sender, instance, **kwargs):
#     if instance.score is not None:
#         analytics, created = TestAnalytics.objects.get_or_create(test=instance.test)
#         analytics.update_analytics()