from rest_framework import serializers
from .models import StudentProgress, TestAnalytics, TestAttemptHistory
from apps.content.models import Subject, Topic
from apps.examination.models import Test

class TestSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()

    class Meta:
        model = Test
        fields = ['title', 'subject']

class TestAttemptHistorySerializer(serializers.ModelSerializer):
    test = serializers.StringRelatedField()
    subject = serializers.CharField(source='test.subject.name')

    class Meta:
        model = TestAttemptHistory
        fields = ['test', 'subject', 'score', 'completed_at']

class StudentProgressSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()
    subject_id = serializers.PrimaryKeyRelatedField(source='subject', read_only=True)
    strength_topics = serializers.StringRelatedField(many=True)
    weakness_topics = serializers.StringRelatedField(many=True)

    class Meta:
        model = StudentProgress
        fields = ['subject', 'subject_id', 'total_attempts', 'average_score', 'strength_topics', 'weakness_topics', 'feedback', 'last_updated']

class TestAnalyticsSerializer(serializers.ModelSerializer):
    test = TestSerializer()

    class Meta:
        model = TestAnalytics
        fields = ['test', 'average_score', 'difficulty_distribution', 'question_analysis', 'anomalies']
