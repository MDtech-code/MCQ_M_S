from rest_framework import serializers
from .models import StudentProgress, TestAnalytics, TestAttemptHistory
from apps.content.models import Subject, Topic

class StudentProgressSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()
    strength_topics = serializers.StringRelatedField(many=True)
    weakness_topics = serializers.StringRelatedField(many=True)

    class Meta:
        model = StudentProgress
        fields = ['subject', 'total_attempts', 'average_score', 'strength_topics', 'weakness_topics', 'feedback', 'last_updated']

class TestAnalyticsSerializer(serializers.ModelSerializer):
    test = serializers.StringRelatedField()

    class Meta:
        model = TestAnalytics
        fields = ['test', 'average_score', 'difficulty_distribution', 'question_analysis', 'anomalies']

class TestAttemptHistorySerializer(serializers.ModelSerializer):
    test = serializers.StringRelatedField()
    subject = serializers.StringRelatedField(source='test.subjects.first')

    class Meta:
        model = TestAttemptHistory
        fields = ['test', 'subject', 'score', 'completed_at', 'duration']
# # apps/analytics/serializers.py
# from rest_framework import serializers
# from .models import StudentProgress, TestAnalytics
# from apps.content.models import Subject, Topic

# class StudentProgressSerializer(serializers.ModelSerializer):
#     subject = serializers.StringRelatedField()
#     strength_topics = serializers.StringRelatedField(many=True)
#     weakness_topics = serializers.StringRelatedField(many=True)

#     class Meta:
#         model = StudentProgress
#         fields = ['subject', 'total_attempts', 'average_score', 'strength_topics', 'weakness_topics', 'last_updated']

# class TestAnalyticsSerializer(serializers.ModelSerializer):
#     test = serializers.StringRelatedField()

#     class Meta:
#         model = TestAnalytics
#         fields = ['test', 'average_score', 'difficulty_distribution', 'question_analysis']