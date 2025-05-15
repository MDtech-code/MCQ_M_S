import logging
from rest_framework import serializers
from .models import Subject, Topic, Question, QuestionApproval
from apps.content.utils.validations import (
    validate_question_text, validate_question_type, validate_difficulty,
    validate_options, validate_source, validate_topic_subject_consistency,
    check_duplicate_question, log_validation_error
)

logger = logging.getLogger(__name__)

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']

class TopicSerializer(serializers.ModelSerializer):
    # subject = serializers.StringRelatedField()
    subject = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'subject', 'name', 'difficulty_level']

class QuestionSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)  # Use nested serializer
    # topics = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), many=True)


    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'difficulty', 'topics',
            'options', 'correct_answer', 'metadata', 'version', 'is_active', 'source',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'version', 'is_active', 'source', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate question fields using centralized validators."""
        data['question_text'] = validate_question_text(data.get('question_text', ''))
        data['question_type'] = validate_question_type(data.get('question_type', 'MCQ'))
        data['difficulty'] = validate_difficulty(data.get('difficulty', ''))
        data['options'] = validate_options(data.get('options', {}))
        correct_answer = data.get('correct_answer')
        if correct_answer not in data['options']:
            log_validation_error("correct_answer", correct_answer, "Must be one of A, B, C, D")
            raise serializers.ValidationError({"correct_answer": "Must be one of A, B, C, D"})
        topics = data.get('topics', [])
        if not topics:
            log_validation_error("topics", topics, "At least one topic is required")
            raise serializers.ValidationError({"topics": "At least one topic is required"})
        validate_topic_subject_consistency(topics)
        check_duplicate_question(data['question_text'], topics, self.instance)
        data['source'] = validate_source(data.get('source', 'manual'))
        return data

    def create(self, validated_data):
        topics = validated_data.pop('topics', [])
        validated_data['is_active'] = False
        question = Question.objects.create(**validated_data, created_by=self.context['request'].user)
        question.topics.set(topics)
        flag_reason = ""
        flagged = False
        if not all(validated_data['options'].values()):
            flagged = True
            flag_reason = "Empty option values detected"
        QuestionApproval.objects.create(
            question=question,
            flagged_by_system=flagged,
            flag_reason=flag_reason
        )
        logger.info(f"Question {question.id} created by {question.created_by.email}")
        return question

    def update(self, instance, validated_data):
        topics = validated_data.pop('topics', None)
        instance.version += 1
        instance.is_active = False
        approval = instance.approval
        if approval.status != 'REJECTED':
            approval.status = 'PENDING'
            approval.flagged_by_system = False
            approval.flag_reason = ""
            approval.reviewed_by = None
            approval.reviewed_at = None
            approval.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if topics is not None:
            instance.topics.set(topics)
        if not all(validated_data.get('options', instance.options).values()):
            approval.flagged_by_system = True
            approval.flag_reason = "Empty option values detected"
            approval.save()
        logger.info(f"Question {instance.id} updated by {instance.created_by.email}")
        return instance
# from datetime import timezone
# from rest_framework import serializers
# from .models import Subject, Topic, Question, QuestionApproval
# from django.core.exceptions import ValidationError
# import logging
# import re
# import string
# from fuzzywuzzy import fuzz
# from spellchecker import SpellChecker
# logger = logging.getLogger(__name__)

# class SubjectSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Subject
#         fields = ['id', 'name', 'description']

# class TopicSerializer(serializers.ModelSerializer):
#     subject = serializers.StringRelatedField()

#     class Meta:
#         model = Topic
#         fields = ['id', 'subject', 'name', 'difficulty_level']

    

# class QuestionSerializer(serializers.ModelSerializer):
#     topics = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), many=True)

#     class Meta:
#         model = Question
#         fields = [
#             'id', 'question_text', 'question_type', 'difficulty', 'topics',
#             'options', 'correct_answer', 'metadata', 'version', 'is_active','source',
#             'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'version', 'is_active','source', 'created_at', 'updated_at']
#     def validate(self, data):
#         # Basic validations
#         if not data.get('topics'):
#             logger.warning(f"Question creation failed: No topics provided")
#             raise serializers.ValidationError({"topics": "At least one topic is required"})
#         if data.get('question_type') != 'MCQ':
#             logger.warning(f"Invalid question_type: {data.get('question_type')}")
#             raise serializers.ValidationError({"question_type": "Only MCQ is supported"})
#         options = data.get('options', {})
#         if set(options.keys()) != {'A', 'B', 'C', 'D'}:
#             logger.warning(f"Invalid options format: {options}")
#             raise serializers.ValidationError({"options": "Options must have keys A, B, C, D"})
#         correct_answer = data.get('correct_answer')
#         if correct_answer not in options:
#             logger.warning(f"Invalid correct_answer: {correct_answer}")
#             raise serializers.ValidationError({"correct_answer": "Must be one of A, B, C, D"})
#         question_text = data.get('question_text', '')
#         # Validate topic-subject consistency
#         topics = data.get('topics', [])
#         if topics:
#             subject_ids = set(topic.subject_id for topic in topics)
#             if len(subject_ids) > 1:
#                 logger.warning(f"Inconsistent subjects in topics: {subject_ids}")
#                 raise serializers.ValidationError({"topics": "All topics must belong to the same subject"})
        
#         # Suspicious content
#         suspicious_patterns = [
#             r'\b(fuck|shit|damn)\b',  # Offensive words
#             r'^[a-zA-Z0-9\s\?\.]{0,5}$',  # Too short/gibberish
#         ]
#         for pattern in suspicious_patterns:
#             if re.search(pattern, question_text, re.IGNORECASE):
#                 logger.warning(f"Suspicious question text: {question_text}")
#                 raise serializers.ValidationError({"question_text": "Question text appears invalid or inappropriate"})
        
       
        
#         # Duplicate question check (exclude current question in update)
#         instance = getattr(self, 'instance', None)
#         existing_questions = Question.objects.filter(topics__in=topics)
#         if instance:
#             existing_questions = existing_questions.exclude(id=instance.id)
#         for existing_text in existing_questions.values_list('question_text', flat=True):
#             if fuzz.ratio(question_text.lower(), existing_text.lower()) > 90:
#                 logger.warning(f"Possible duplicate question: {question_text}")
#                 raise serializers.ValidationError({"question_text": "Question is too similar to an existing one"})
        
#         # Typo check
#         spell = SpellChecker()
#         words = question_text.translate(str.maketrans('','',string.punctuation)).split()
#         typos = [word for word in words if word.lower() not in spell and not word.isdigit() and len(word) > 3]
#         if typos:
#             logger.warning(f"Potential typos in question: {typos}")
#             raise serializers.ValidationError({"question_text": f"Potential typos detected: {', '.join(typos)}"})

#         return data

#     def create(self, validated_data):
#         topics = validated_data.pop('topics', [])
#         validated_data['is_active'] = False
#         question = Question.objects.create(**validated_data, created_by=self.context['request'].user)
#         question.topics.set(topics)
#         flag_reason = ""
#         flagged = False
#         if not all(validated_data['options'].values()):
#             flagged = True
#             flag_reason = "Empty option values detected"
#         QuestionApproval.objects.create(
#             question=question,
#             flagged_by_system=flagged,
#             flag_reason=flag_reason
#         )
#         logger.info(f"Question {question.id} created by {question.created_by.email}")
#         return question
    


#     def update(self, instance, validated_data):
#         topics = validated_data.pop('topics', None)
#         # Increment version
#         instance.version += 1
#         # Reset approval
#         instance.is_active = False
#         approval = instance.approval
#         if approval.status != 'REJECTED':  # Don't reset rejected questions unnecessarily
#             approval.status = 'PENDING'
#             approval.flagged_by_system = False
#             approval.flag_reason = ""
#             approval.reviewed_by = None
#             approval.reviewed_at = None
#             approval.save()
#         # Update fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         if topics is not None:
#             instance.topics.set(topics)
#         # Re-flag if needed
#         if not all(validated_data.get('options', instance.options).values()):
#             approval.flagged_by_system = True
#             approval.flag_reason = "Empty option values detected"
#             approval.save()
#         logger.info(f"Question {instance.id} updated by {instance.created_by.email}")
#         return instance

