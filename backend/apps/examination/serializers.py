# apps/examination/serializers.py
from rest_framework import serializers
from .models import Test, TestAttempt, StudentResponse
from apps.content.models import Question, Subject, Topic
from apps.content.serializers import QuestionSerializer
from apps.accounts.models import User  # Import User model
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from apps.content.utils.validations import log_validation_error
import logging


logger = logging.getLogger(__name__)

class TestSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    questions = serializers.PrimaryKeyRelatedField(many=True, queryset=Question.objects.filter(is_active=True), required=False)
    created_by = serializers.StringRelatedField(read_only=True)
    scoring_scheme = serializers.JSONField()
    question_filters = serializers.JSONField(default=dict)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'created_by', 'subject','subject_name', 'questions', 'duration',
            'max_attempts', 'scoring_scheme', 'question_filters', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate(self, data):
        subject = data.get('subject')
        questions = data.get('questions', [])
        question_filters = data.get('question_filters', {})
        scoring_scheme = data.get('scoring_scheme', {})
        duration = data.get('duration', 10)

        if not subject:
            logger.warning("Test creation failed: No subject provided")
            raise serializers.ValidationError({"subject": "A subject is required"})

        if not questions and not question_filters:
            logger.warning("Test creation failed: No questions or filters provided")
            raise serializers.ValidationError({"questions": "Provide exactly 5 questions or use filters"})

        if question_filters:
            if 'topic' not in question_filters:
                logger.warning("Test creation failed: Topic required in filters")
                raise serializers.ValidationError({"question_filters": "Topic ID is required for auto-selection"})
            try:
                topic_ids = question_filters.get('topic', [])
                if not isinstance(topic_ids, list):
                    topic_ids = [topic_ids]
                # Convert topic_ids to integers for consistency
                topic_ids = [int(tid) for tid in topic_ids]
                # Update question_filters with converted topic IDs
                data['question_filters']['topic'] = topic_ids  # Add this line

                topics = Topic.objects.filter(id__in=topic_ids, subject=subject)
                if len(topics) != len(topic_ids):
                    logger.warning(f"Test creation failed: Invalid topic IDs {topic_ids}")
                    raise serializers.ValidationError({"question_filters": "Invalid topic ID(s) or topics do not belong to the subject"})
            except (ValueError, Topic.DoesNotExist):
                logger.warning(f"Test creation failed: Invalid topic ID {question_filters.get('topic')}")
                raise serializers.ValidationError({"question_filters": "Invalid topic ID"})

            queryset = Question.objects.filter(is_active=True)
            if topic_ids:
                queryset = queryset.filter(topics__id__in=topic_ids).distinct()
            if 'difficulty' in question_filters:
                if question_filters['difficulty'] not in ['Easy', 'Medium', 'Hard']:
                    raise serializers.ValidationError({"question_filters": "Invalid difficulty (Easy, Medium, Hard)"})
                difficulty_map = {'Easy': 'E', 'Medium': 'M', 'Hard': 'H'}
                queryset = queryset.filter(difficulty=difficulty_map[question_filters['difficulty']])
            
            questions = queryset.distinct()[:5]
            if len(questions) < 5:
                logger.warning(f"Test creation failed: Only {len(questions)} questions match filters {question_filters}")
                raise serializers.ValidationError({"question_filters": f"Need 5 questions, found {len(questions)} for topics {topic_ids}"})
            data['questions'] = questions

        if len(questions) != 5:
            logger.warning(f"Test creation failed: Invalid question count ({len(questions)}, expected 5)")
            raise serializers.ValidationError({"questions": "Test must have exactly 5 questions"})

        subject_id = subject.id if subject else None
        if question_filters.get('topic'):
            topic_ids = question_filters.get('topic', [])
            if not isinstance(topic_ids, list):
                topic_ids = [topic_ids]
            for q in questions:
                q_subject_ids = set(t.subject_id for t in q.topics.all())
                q_topic_ids = set(t.id for t in q.topics.all())
                if subject_id not in q_subject_ids:
                    logger.warning(f"Test creation failed: Question {q.id} does not belong to subject {subject_id}")
                    raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to subject {subject_id}"})
                if not any(topic_id in q_topic_ids for topic_id in topic_ids):
                    logger.warning(f"Test creation failed: Question {q.id} does not match any topic {topic_ids}")
                    raise serializers.ValidationError({"questions": f"Question {q.id} does not match any topic ID {topic_ids}"})
        else:
            for q in questions:
                q_subject_ids = set(t.subject_id for t in q.topics.all())
                if subject_id not in q_subject_ids:
                    logger.warning(f"Test creation failed: Question {q.id} does not belong to subject {subject_id}")
                    raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to subject {subject_id}"})

        if not isinstance(scoring_scheme, dict) or 'correct' not in scoring_scheme or 'incorrect' not in scoring_scheme:
            logger.warning("Test creation failed: Invalid scoring scheme")
            raise serializers.ValidationError({"scoring_scheme": "Must include 'correct' and 'incorrect' values"})

        if duration <= 0:
            logger.warning(f"Test creation failed: Invalid duration {duration}")
            raise serializers.ValidationError({"duration": "Duration must be positive"})

        return data

    def create(self, validated_data):
        subject = validated_data.pop('subject')
        questions = validated_data.pop('questions', [])
        test = Test.objects.create(subject=subject, **validated_data)
        test.questions.set(questions)
        logger.info(f"Test {test.id} created by {test.created_by.email}")
        return test

    def update(self, instance, validated_data):
        subject = validated_data.pop('subject', None)
        questions = validated_data.pop('questions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if subject is not None:
            instance.subject = subject
        instance.save()
        if questions is not None:
            instance.questions.set(questions)
        logger.info(f"Test {instance.id} updated")
        return instance

class TestAttemptSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(format="%Y-%m-%d %I:%M:%S %p %Z", read_only=True)
    end_time = serializers.DateTimeField(format="%Y-%m-%d %I:%M:%S %p %Z", read_only=True, allow_null=True)

    class Meta:
        model = TestAttempt
        fields = ['id', 'test', 'student', 'start_time', 'end_time', 'score']
        read_only_fields = ['id', 'student', 'start_time', 'end_time', 'score']

  
    def validate(self, data):
        """Check if the student has remaining attempts."""
        student = self.context['request'].user
        logger.debug(f"User: {student}, Role: {student.role}, Role Type: {type(student.role)}")
        if student.role != User.Role.STUDENT:
            log_validation_error("role", student.role, f"Expected {User.Role.STUDENT}")
            raise serializers.ValidationError({"non_field_errors": "Only students can start attempts."})
        test = data['test']
        max_attempts = test.max_attempts or 1
        cache_key = f"test_attempts:{student.id}:{test.id}"
        cached_count = cache.get(cache_key)
        if cached_count is None:
            attempts = TestAttempt.objects.filter(test=test, student=student).count()
            cache.set(cache_key, attempts, timeout=3600)  # 1 hour
        else:
            attempts = cached_count
        if attempts >= max_attempts:
            log_validation_error("test", test.id, f"Maximum attempts reached: {attempts}/{max_attempts}")
            raise serializers.ValidationError({"test": f"Maximum attempts ({max_attempts}) reached"})
        return data


    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        validated_data['start_time'] = timezone.now()
        attempt = super().create(validated_data)
        # Update cache
        cache_key = f"test_attempts:{validated_data['student'].id}:{validated_data['test'].id}"
        
        attempts = TestAttempt.objects.filter(test=validated_data['test'], student=validated_data['student']).count()
        cache.set(cache_key, attempts, timeout=3600)
        return attempt



from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from .models import StudentResponse, TestAttempt
from apps.content.models import Question

class StudentResponseSerializer(serializers.ModelSerializer):
    # Declare attempt & question as PK fields, so DRF can resolve them from integers
    attempt = serializers.PrimaryKeyRelatedField(queryset=TestAttempt.objects.all())
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())

    class Meta:
        model = StudentResponse
        fields = ['id', 'attempt', 'question', 'selected_answer', 'is_correct', 'time_taken']
        read_only_fields = ['is_correct']

    def validate(self, data):
        attempt = data['attempt']
        question = data['question']
        user = self.context['request'].user

        if attempt.student != user:
            raise serializers.ValidationError("You can only respond to your own attempts.")
        if question not in attempt.test.questions.all():
            raise serializers.ValidationError("Question does not belong to this test.")
        # if data['selected_answer'] not in question.options:
        if data['selected_answer'] and data['selected_answer'] not in question.options:
            raise serializers.ValidationError("Invalid answer option.")
        if attempt.end_time:
            raise serializers.ValidationError("Attempt is already submitted.")
        if timezone.now() > attempt.start_time + timedelta(minutes=attempt.test.duration):
            raise serializers.ValidationError("Test duration has expired.")
        return data

    def create(self, validated_data):
        # Determine correctness
        question = validated_data['question']
        validated_data['is_correct'] = (validated_data['selected_answer'] == question.correct_answer)
        return super().create(validated_data)

