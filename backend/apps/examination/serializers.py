# apps/examination/serializers.py
from rest_framework import serializers
from .models import Test, TestAttempt, StudentResponse
from apps.content.models import Question, Subject, Topic
from apps.content.serializers import QuestionSerializer
from apps.accounts.models import User  # Import User model
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# class TestSerializer(serializers.ModelSerializer):
#     subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
#     questions = serializers.PrimaryKeyRelatedField(queryset=Question.objects.filter(is_active=True), many=True, required=False)
#     created_by = serializers.StringRelatedField(read_only=True)
#     scoring_scheme = serializers.JSONField()
#     question_filters = serializers.JSONField(default=dict)

#     class Meta:
#         model = Test
#         fields = [
#             'id', 'title', 'created_by', 'subject', 'questions', 'duration',
#             'max_attempts', 'scoring_scheme', 'question_filters', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

#     def validate(self, data):
#         subject = data.get('subject')
#         questions = data.get('questions', [])
#         question_filters = data.get('question_filters', {})
#         scoring_scheme = data.get('scoring_scheme', {})
#         duration = data.get('duration', 10)

#         if not subject:
#             logger.warning("Test creation failed: No subjects provided")
#             raise serializers.ValidationError({"subjects": "A subject is required"})

#         if not questions and not question_filters:
#             logger.warning("Test creation failed: No questions or filters provided")
#             raise serializers.ValidationError({"questions": "Provide exactly 5 questions or use filters"})

#         if question_filters:
#             if 'topic' not in question_filters:
#                 logger.warning("Test creation failed: Topic required in filters")
#                 raise serializers.ValidationError({"question_filters": "Topic ID is required for auto-selection"})
#             try:
#                 topic_id = int(question_filters['topic'])
#                 topic = Topic.objects.get(id=topic_id)
#             except (ValueError, Topic.DoesNotExist):
#                 logger.warning(f"Test creation failed: Invalid topic ID {question_filters.get('topic')}")
#                 raise serializers.ValidationError({"question_filters": "Invalid topic ID"})

#             queryset = Question.objects.filter(is_active=True, topics=topic)
#             if 'difficulty' in question_filters:
#                 if question_filters['difficulty'] not in ['E', 'M', 'H']:
#                     raise serializers.ValidationError({"question_filters": "Invalid difficulty (E, M, H)"})
#                 queryset = queryset.filter(difficulty=question_filters['difficulty'])
            
#             questions = queryset.distinct()[:5]
#             if len(questions) < 5:
#                 logger.warning(f"Test creation failed: Only {len(questions)} questions match filters {question_filters}")
#                 raise serializers.ValidationError({"question_filters": f"Need 5 questions, found {len(questions)} for topic {topic.name}"})
#             data['questions'] = questions

#         if len(questions) != 5:
#             logger.warning(f"Test creation failed: Invalid question count ({len(questions)}, expected 5)")
#             raise serializers.ValidationError({"questions": "Test must have exactly 5 questions"})

#         subject_ids = set(s.id for s in subjects)
#         if question_filters.get('topic'):
#             topic_id = int(question_filters['topic'])
#             for q in questions:
#                 q_subject_ids = set(t.subject_id for t in q.topics.all())
#                 q_topic_ids = set(t.id for t in q.topics.all())
#                 if not subject_ids.intersection(q_subject_ids):
#                     logger.warning(f"Test creation failed: Question {q.id} does not belong to test subjects")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to test subjects"})
#                 if topic_id not in q_topic_ids:
#                     logger.warning(f"Test creation failed: Question {q.id} does not match topic {topic_id}")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not match topic ID {topic_id}"})
#         else:
#             for q in questions:
#                 q_subject_ids = set(t.subject_id for t in q.topics.all())
#                 if not subject_ids.intersection(q_subject_ids):
#                     logger.warning(f"Test creation failed: Question {q.id} does not belong to test subjects")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to test subjects"})

#         # if not isinstance(scoring_scheme, dict) or 'correct' not in scoring_scheme or 'incorrect' in scoring_scheme:
#         #     logger.warning("Test creation failed: Invalid scoring scheme")
#         #     raise serializers.ValidationError({"scoring_scheme": "Must include 'correct' and 'incorrect' values"})
#         if not isinstance(scoring_scheme, dict) or 'correct' not in scoring_scheme or 'incorrect' not in scoring_scheme:
#             logger.warning("Test creation failed: Invalid scoring scheme")
#             raise serializers.ValidationError({"scoring_scheme": "Must include 'correct' and 'incorrect' values"})

#         if duration <= 0:
#             logger.warning(f"Test creation failed: Invalid duration {duration}")
#             raise serializers.ValidationError({"duration": "Duration must be positive"})

#         return data

#     def create(self, validated_data):
#         subjects = validated_data.pop('subjects', [])
#         questions = validated_data.pop('questions', [])
#         test = Test.objects.create(**validated_data)
#         test.subjects.set(subjects)
#         test.questions.set(questions)
#         logger.info(f"Test {test.id} created by {test.created_by.email}")
#         return test

#     def update(self, instance, validated_data):
#         subjects = validated_data.pop('subjects', None)
#         questions = validated_data.pop('questions', None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         if subjects is not None:
#             instance.subjects.set(subjects)
#         if questions is not None:
#             instance.questions.set(questions)
#         logger.info(f"Test {instance.id} ")
#         return instance


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
        student = self.context['request'].user
        logger.debug(f"User: {student}, Role: {student.role}, Role Type: {type(student.role)}")
        if student.role != User.Role.STUDENT:
            logger.warning(f"Validation failed: User {student.email} has role {student.role}, expected {User.Role.STUDENT}")
            raise serializers.ValidationError("Only students can start attempts.")
        test = data['test']
        attempts = TestAttempt.objects.filter(test=test, student=student).count()
        if attempts >= test.max_attempts:
            logger.warning(f"Validation failed: Maximum attempts reached for user {student.email} on test {test.id}")
            raise serializers.ValidationError("Maximum attempts reached.")
        return data

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        validated_data['start_time'] = timezone.now()
        return super().create(validated_data)

# class StudentResponseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StudentResponse
#         fields = ['id', 'attempt', 'question', 'selected_answer', 'is_correct', 'time_taken']
#         read_only_fields = ['is_correct']

#     def validate(self, data):
#         attempt = data['attempt']
#         question = data['question']
#         if attempt.student != self.context['request'].user:
#             raise serializers.ValidationError("You can only respond to your own attempts.")
#         if question not in attempt.test.questions.all():
#             raise serializers.ValidationError("Question does not belong to this test.")
#         if data['selected_answer'] not in question.options:
#             raise serializers.ValidationError("Invalid answer option.")
#         if attempt.end_time:
#             raise serializers.ValidationError("Attempt is already submitted.")
#         if timezone.now() > attempt.start_time + timedelta(minutes=attempt.test.duration):
#             raise serializers.ValidationError("Test duration has expired.")
#         return data


# apps.examination.serializers.py

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
        if data['selected_answer'] not in question.options:
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

# # apps/examination/serializers.py
# from rest_framework import serializers
# from .models import Test, TestAttempt, StudentResponse
# from apps.content.models import Question, Subject, Topic
# from apps.content.serializers import QuestionSerializer
# from django.utils import timezone
# from datetime import timedelta
# import logging

# logger = logging.getLogger(__name__)

# class TestSerializer(serializers.ModelSerializer):
#     subjects = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True)
#     questions = serializers.PrimaryKeyRelatedField(queryset=Question.objects.filter(is_active=True), many=True, required=False)
#     created_by = serializers.StringRelatedField(read_only=True)
#     scoring_scheme = serializers.JSONField()
#     question_filters = serializers.JSONField(default=dict)

#     class Meta:
#         model = Test
#         fields = [
#             'id', 'title', 'created_by', 'subjects', 'questions', 'duration',
#             'max_attempts', 'scoring_scheme', 'question_filters', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

#     def validate(self, data):
#         subjects = data.get('subjects', [])
#         questions = data.get('questions', [])
#         question_filters = data.get('question_filters', {})
#         scoring_scheme = data.get('scoring_scheme', {})
#         duration = data.get('duration', 10)  # Default to 10 minutes

#         # Validate subjects
#         if not subjects:
#             logger.warning("Test creation failed: No subjects provided")
#             raise serializers.ValidationError({"subjects": "At least one subject is required"})

#         # Validate questions or apply filters
#         if not questions and not question_filters:
#             logger.warning("Test creation failed: No questions or filters provided")
#             raise serializers.ValidationError({"questions": "Provide exactly 5 questions or use filters"})

#         if question_filters:
#             if 'topic' not in question_filters:
#                 logger.warning("Test creation failed: Topic required in filters")
#                 raise serializers.ValidationError({"question_filters": "Topic ID is required for auto-selection"})
#             try:
#                 topic_id = int(question_filters['topic'])
#                 topic = Topic.objects.get(id=topic_id)
#             except (ValueError, Topic.DoesNotExist):
#                 logger.warning(f"Test creation failed: Invalid topic ID {question_filters.get('topic')}")
#                 raise serializers.ValidationError({"question_filters": "Invalid topic ID"})

#             queryset = Question.objects.filter(is_active=True, topics=topic)
#             if 'difficulty' in question_filters:
#                 if question_filters['difficulty'] not in ['E', 'M', 'H']:
#                     raise serializers.ValidationError({"question_filters": "Invalid difficulty (E, M, H)"})
#                 queryset = queryset.filter(difficulty=question_filters['difficulty'])
            
#             questions = queryset.distinct()[:5]
#             if len(questions) < 5:
#                 logger.warning(f"Test creation failed: Only {len(questions)} questions match filters {question_filters}")
#                 raise serializers.ValidationError({"question_filters": f"Need 5 questions, found {len(questions)} for topic {topic.name}"})
#             data['questions'] = questions

#         if len(questions) != 5:
#             logger.warning(f"Test creation failed: Invalid question count ({len(questions)}, expected 5)")
#             raise serializers.ValidationError({"questions": "Test must have exactly 5 questions"})

#         subject_ids = set(s.id for s in subjects)
#         if question_filters.get('topic'):
#             topic_id = int(question_filters['topic'])
#             for q in questions:
#                 q_subject_ids = set(t.subject_id for t in q.topics.all())
#                 q_topic_ids = set(t.id for t in q.topics.all())
#                 if not subject_ids.intersection(q_subject_ids):
#                     logger.warning(f"Test creation failed: Question {q.id} does not belong to test subjects")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to test subjects"})
#                 if topic_id not in q_topic_ids:
#                     logger.warning(f"Test creation failed: Question {q.id} does not match topic {topic_id}")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not match topic ID {topic_id}"})
#         else:
#             for q in questions:
#                 q_subject_ids = set(t.subject_id for t in q.topics.all())
#                 if not subject_ids.intersection(q_subject_ids):
#                     logger.warning(f"Test creation failed: Question {q.id} does not belong to test subjects")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to test subjects"})

#         if not isinstance(scoring_scheme, dict) or 'correct' not in scoring_scheme or 'incorrect' not in scoring_scheme:
#             logger.warning("Test creation failed: Invalid scoring scheme")
#             raise serializers.ValidationError({"scoring_scheme": "Must include 'correct' and 'incorrect' values"})

#         if duration <= 0:
#             logger.warning(f"Test creation failed: Invalid duration {duration}")
#             raise serializers.ValidationError({"duration": "Duration must be positive"})

#         return data

#     def create(self, validated_data):
#         subjects = validated_data.pop('subjects', [])
#         questions = validated_data.pop('questions', [])
#         test = Test.objects.create(**validated_data, created_by=self.context['request'].user)
#         test.subjects.set(subjects)
#         test.questions.set(questions)
#         logger.info(f"Test {test.id} created by {test.created_by.email}")
#         return test

#     def update(self, instance, validated_data):
#         subjects = validated_data.pop('subjects', None)
#         questions = validated_data.pop('questions', None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         if subjects is not None:
#             instance.subjects.set(subjects)
#         if questions is not None:
#             instance.questions.set(questions)
#         logger.info(f"Test {instance.id} updated by {instance.created_by.email}")
#         return instance

# class TestAttemptSerializer(serializers.ModelSerializer):
#     start_time = serializers.DateTimeField(format="%Y-%m-%d %I:%M:%S %p %Z")
#     end_time = serializers.DateTimeField(format="%Y-%m-%d %I:%M:%S %p %Z", allow_null=True)

#     class Meta:
#         model = TestAttempt
#         fields = ['id', 'test', 'student', 'start_time', 'end_time', 'score']
#         read_only_fields = ['student', 'start_time', 'end_time', 'score']

#     def validate(self, data):
#         student = self.context['request'].user
#         if student.role != 'STUDENT':
#             raise serializers.ValidationError("Only students can start attempts.")
#         test = data['test']
#         attempts = TestAttempt.objects.filter(test=test, student=student).count()
#         if attempts >= test.max_attempts:
#             raise serializers.ValidationError("Maximum attempts reached.")
#         return data

#     def create(self, validated_data):
#         validated_data['student'] = self.context['request'].user
#         validated_data['start_time'] = timezone.now()
#         return super().create(validated_data)

# class StudentResponseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StudentResponse
#         fields = ['id', 'attempt', 'question', 'selected_answer', 'is_correct', 'time_taken']
#         read_only_fields = ['is_correct']

#     def validate(self, data):
#         attempt = data['attempt']
#         question = data['question']
#         if attempt.student != self.context['request'].user:
#             raise serializers.ValidationError("You can only respond to your own attempts.")
#         if question not in attempt.test.questions.all():
#             raise serializers.ValidationError("Question does not belong to this test.")
#         if data['selected_answer'] not in question.options:
#             raise serializers.ValidationError("Invalid answer option.")
#         if attempt.end_time:
#             raise serializers.ValidationError("Attempt is already submitted.")
#         if timezone.now() > attempt.start_time + timedelta(minutes=attempt.test.duration):
#             raise serializers.ValidationError("Test duration has expired.")
#         return data
# # apps/examination/serializers.py
# from rest_framework import serializers
# from .models import Test,TestAttempt,StudentResponse
# from apps.content.models import Question, Subject, Topic
# from apps.content.serializers import QuestionSerializer
# from django.db.models import Q
# from django.utils import timezone

# import logging
# logger = logging.getLogger(__name__)

# class TestSerializer(serializers.ModelSerializer):
#     subjects = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True)
#     questions = serializers.PrimaryKeyRelatedField(queryset=Question.objects.filter(is_active=True), many=True, required=False)
#     created_by = serializers.StringRelatedField(read_only=True)
#     scoring_scheme = serializers.JSONField()
#     question_filters = serializers.JSONField(default=dict)

#     class Meta:
#         model = Test
#         fields = [
#             'id', 'title', 'created_by', 'subjects', 'questions', 'duration',
#              'max_attempts', 'scoring_scheme',
#             'question_filters', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

#     def validate(self, data):
#         subjects = data.get('subjects', [])
#         questions = data.get('questions', [])
#         question_filters = data.get('question_filters', {})
#         scoring_scheme = data.get('scoring_scheme', {})

#         # Validate subjects
#         if not subjects:
#             logger.warning(f"Test creation failed: No subjects provided")
#             raise serializers.ValidationError({"subjects": "At least one subject is required"})

#         # Validate questions or apply filters
#         if not questions and not question_filters:
#             logger.warning(f"Test creation failed: No questions or filters provided")
#             raise serializers.ValidationError({"questions": "Provide exactly 5 questions or use filters"})

#         if question_filters:
#             # Require topic in filters
#             if 'topic' not in question_filters:
#                 logger.warning(f"Test creation failed: Topic required in filters")
#                 raise serializers.ValidationError({"question_filters": "Topic ID is required for auto-selection"})
#             try:
#                 topic_id = int(question_filters['topic'])
#                 topic = Topic.objects.get(id=topic_id)
#             except (ValueError, Topic.DoesNotExist):
#                 logger.warning(f"Test creation failed: Invalid topic ID {question_filters.get('topic')}")
#                 raise serializers.ValidationError({"question_filters": "Invalid topic ID"})

#             # Build query
#             queryset = Question.objects.filter(is_active=True, topics=topic)
#             if 'difficulty' in question_filters:
#                 if question_filters['difficulty'] not in ['E', 'M', 'H']:
#                     raise serializers.ValidationError({"question_filters": "Invalid difficulty (E, M, H)"})
#                 queryset = queryset.filter(difficulty=question_filters['difficulty'])
            
#             # Select exactly 5 questions
#             questions = queryset.distinct()[:5]
#             if len(questions) < 5:
#                 logger.warning(f"Test creation failed: Only {len(questions)} questions match filters {question_filters}")
#                 raise serializers.ValidationError({"question_filters": f"Need 5 questions, found {len(questions)} for topic {topic.name}"})
#             data['questions'] = questions

#         # Validate question count
#         if len(questions) != 5:
#             logger.warning(f"Test creation failed: Invalid question count ({len(questions)}, expected 5)")
#             raise serializers.ValidationError({"questions": "Test must have exactly 5 questions"})

#         # Validate question-subject and topic consistency
#         subject_ids = set(s.id for s in subjects)
#         if question_filters.get('topic'):
#             topic_id = int(question_filters['topic'])
#             for q in questions:
#                 q_subject_ids = set(t.subject_id for t in q.topics.all())
#                 q_topic_ids = set(t.id for t in q.topics.all())
#                 if not subject_ids.intersection(q_subject_ids):
#                     logger.warning(f"Test creation failed: Question {q.id} does not belong to test subjects")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to test subjects"})
#                 if topic_id not in q_topic_ids:
#                     logger.warning(f"Test creation failed: Question {q.id} does not match topic {topic_id}")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not match topic ID {topic_id}"})
#         else:
#             # Manual selection: ensure subject consistency
#             for q in questions:
#                 q_subject_ids = set(t.subject_id for t in q.topics.all())
#                 if not subject_ids.intersection(q_subject_ids):
#                     logger.warning(f"Test creation failed: Question {q.id} does not belong to test subjects")
#                     raise serializers.ValidationError({"questions": f"Question {q.id} does not belong to test subjects"})

#         # Validate scoring scheme
#         if not isinstance(scoring_scheme, dict) or 'correct' not in scoring_scheme or 'incorrect' not in scoring_scheme:
#             logger.warning(f"Test creation failed: Invalid scoring scheme")
#             raise serializers.ValidationError({"scoring_scheme": "Must include 'correct' and 'incorrect' values"})

#         return data

#     def create(self, validated_data):
#         subjects = validated_data.pop('subjects', [])
#         questions = validated_data.pop('questions', [])
#         test = Test.objects.create(**validated_data, created_by=self.context['request'].user)
#         test.subjects.set(subjects)
#         test.questions.set(questions)
#         logger.info(f"Test {test.id} created by {test.created_by.email}")
#         return test

#     def update(self, instance, validated_data):
#         subjects = validated_data.pop('subjects', None)
#         questions = validated_data.pop('questions', None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         if subjects is not None:
#             instance.subjects.set(subjects)
#         if questions is not None:
#             instance.questions.set(questions)
#         logger.info(f"Test {instance.id} updated by {instance.created_by.email}")
#         return instance
    







# # apps/examination/serializers.py


# class TestAttemptSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TestAttempt
#         fields = ['id', 'test', 'student', 'start_time', 'end_time', 'score']
#         read_only_fields = ['student', 'start_time', 'end_time', 'score']

#     def validate(self, data):
#         student = self.context['request'].user
#         if student.role != 'STUDENT':
#             raise serializers.ValidationError("Only students can start attempts.")
#         test = data['test']
#         if test.schedule_start > timezone.now() or test.schedule_end < timezone.now():
#             raise serializers.ValidationError("Test is not active.")
#         attempts = TestAttempt.objects.filter(test=test, student=student).count()
#         if attempts >= test.max_attempts:
#             raise serializers.ValidationError("Maximum attempts reached.")
#         return data

#     def create(self, validated_data):
#         validated_data['student'] = self.context['request'].user
#         validated_data['start_time'] = timezone.now()
#         return super().create(validated_data)

# class StudentResponseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StudentResponse
#         fields = ['id', 'attempt', 'question', 'selected_answer', 'is_correct', 'time_taken']
#         read_only_fields = ['is_correct']

#     def validate(self, data):
#         attempt = data['attempt']
#         question = data['question']
#         if attempt.student != self.context['request'].user:
#             raise serializers.ValidationError("You can only respond to your own attempts.")
#         if question not in attempt.test.questions.all():
#             raise serializers.ValidationError("Question does not belong to this test.")
#         if data['selected_answer'] not in question.options:
#             raise serializers.ValidationError("Invalid answer option.")
#         if attempt.end_time:
#             raise serializers.ValidationError("Attempt is already submitted.")
#         return data