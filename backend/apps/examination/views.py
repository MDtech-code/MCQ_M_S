# apps/examination/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.common.authentication import CookieTokenAuthentication
from .models import Test, TestAttempt
from .serializers import TestSerializer,TestAttemptSerializer, StudentResponseSerializer
from apps.common.throttles import CustomUserRateThrottle
from apps.accounts.models import User
from django.core.paginator import Paginator, EmptyPage
from django.utils import timezone
from django.utils.dateparse import parse_date
from .models import Test, TestAttempt, StudentResponse
from apps.content.models import Subject,Question,Topic
from datetime import timedelta
from apps.common.permissions import IsAdmin,IsStudent,IsTeacher
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.shortcuts import redirect
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.authentication import SessionAuthentication
from django.core.paginator import Paginator, EmptyPage
import json
import logging
from django.db.models import Q
logger = logging.getLogger(__name__)



@method_decorator(ensure_csrf_cookie, name='dispatch')
class TestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        if request.accepted_renderer.format == 'html':
            subjects = Subject.objects.all()
            questions = Question.objects.filter(is_active=True)
            topics = Topic.objects.all()
            print(topics)
            return Response(
                {
                    'is_update': False,
                    'subjects': subjects,
                    'questions': questions,
                    'topics': topics,
                    'difficulties': ["Easy", "Medium", "Hard"],
                    'form_data': {},
                    'errors': {}
                },
                template_name='examination/teacher/test_form.html'
            )
        return Response({"message": "Test creation endpoint (GET)"}, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('teacher_dashboard')
            return Response(
                {"error": "Account not active or verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.accepted_renderer.format == 'html':
            raw = request.POST
            python_data = {
                'title': raw.get('title', '').strip(),
                'subject': raw.get('subjects', ''),  # Use single subject from the form
                'duration': raw.get('duration', ''),
                'max_attempts': raw.get('max_attempts', ''),
            }

            # Scoring scheme
            correct = raw.get('scoring_scheme_correct', '').strip()
            incorrect = raw.get('scoring_scheme_incorrect', '').strip()
            try:
                python_data['scoring_scheme'] = {
                    'correct': float(correct) if correct else 1.0,
                    'incorrect': float(incorrect) if incorrect else -0.25
                }
            except (ValueError, TypeError):
                python_data['scoring_scheme'] = {'correct': 1.0, 'incorrect': -0.25}

            # Question selection
            if raw.get('question_selection') == 'auto':
                topics = raw.getlist('question_filters_topic')  # Support multiple topics
                if topics:
                    python_data['question_filters'] = {'topic': topics}
                    difficulty_map = {'Easy': 'E', 'Medium': 'M', 'Hard': 'H'}
                    diff = raw.get('question_filters_difficulty', '').strip()
                    if diff in ['E', 'M', 'H']:
                        python_data['question_filters']['difficulty'] = difficulty_map[diff]
                else:
                    python_data['question_filters'] = {}
            else:
                python_data['questions'] = raw.getlist('questions')
                python_data['question_filters'] = {}
            logger.debug(f"Processed payload: {python_data}")

        else:
            python_data = request.data

        serializer = TestSerializer(data=python_data, context={'request': request})
        if serializer.is_valid():
            test = serializer.save(created_by=request.user)
            logger.info(f"Test {test.id} created by {test.created_by.email}")
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Test created successfully.")
                return redirect('test_list')
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
        if request.accepted_renderer.format == 'html':
            subjects = Subject.objects.all()
            questions = Question.objects.filter(is_active=True)
            topics = Topic.objects.all()
            return Response(
                {
                    'is_update': False,
                    'errors': serializer.errors,
                    'form_data': python_data,
                    'subjects': subjects,
                    'questions': questions,
                    'topics': topics,
                    'difficulties': ["Easy", "Medium", "Hard"],
                },
                template_name='examination/teacher/test_form.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'is_update': False,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     # 'difficulties': ["E", "M", "H"],
#                     'difficulties': ["Easy", "Medium", "Hard"],
#                     'form_data': {},
#                     'errors': {}
#                 },
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response({"message": "Test creation endpoint (GET)"}, status=status.HTTP_200_OK)

#     def post(self, request):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         if request.accepted_renderer.format == 'html':
#             raw = request.POST
#             python_data = {
#                 'title': raw.get('title', '').strip(),
#                 'subjects': raw.getlist('subjects'),
#                 'duration': raw.get('duration', ''),
#                 'max_attempts': raw.get('max_attempts', ''),
#             }

#             # Scoring scheme
#             correct = raw.get('scoring_scheme_correct', '').strip()
#             incorrect = raw.get('scoring_scheme_incorrect', '').strip()
#             try:
#                 python_data['scoring_scheme'] = {
#                     'correct': float(correct) if correct else 1.0,
#                     'incorrect': float(incorrect) if incorrect else -0.25
#                 }
#             except (ValueError, TypeError):
#                 python_data['scoring_scheme'] = {'correct': 1.0, 'incorrect': -0.25}

#             # Question selection
#             if raw.get('question_selection') == 'auto':
#                 topic = raw.get('question_filters_topic', '').strip()
#                 if topic:
#                     python_data['question_filters'] = {'topic': topic}
#                     difficulty_map = {'Easy': 'E', 'Medium': 'M', 'Hard': 'H'}
#                     diff = raw.get('question_filters_difficulty', '').strip()
#                     diff = difficulty_map.get(diff, diff)

#                     if diff in ['E', 'M', 'H']:
#                         python_data['question_filters']['difficulty'] = diff
#                     print('diff yukk hia ',diff)
#                 else:
#                     python_data['question_filters'] = {}
#             else:
#                 python_data['questions'] = raw.getlist('questions')
#                 python_data['question_filters'] = {}

#         else:
#             python_data = request.data

#         serializer = TestSerializer(data=python_data, context={'request': request})
#         if serializer.is_valid():
#             test = serializer.save(created_by=request.user)
#             logger.info(f"Test {test.id} created by {test.created_by.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test created successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'is_update': False,
#                     'errors': serializer.errors,
#                     'form_data': python_data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     # 'difficulties': ["E", "M", "H"]
#                     'difficulties': ["Easy", "Medium", "Hard"],
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class TestUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request, pk):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('teacher_dashboard')
            return Response(
                {"error": "Account not active or verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            test = Test.objects.get(pk=pk, created_by=request.user)
        except Test.DoesNotExist:
            logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Test not found or not owned by you.")
                return redirect('test_list')
            return Response(
                {"error": "Test not found or not owned by you"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TestSerializer(test)
        if request.accepted_renderer.format == 'html':
            subjects = Subject.objects.all()
            questions = Question.objects.filter(is_active=True)
            topics = Topic.objects.all()
            return Response(
                {
                    'is_update': True,
                    'test': test,
                    'form_data': {
                        'title': test.title,
                        'subject': test.subject.id if test.subject else '',
                        'duration': test.duration,
                        'max_attempts': test.max_attempts,
                        'scoring_scheme': {
                            'correct': test.scoring_scheme.get('correct', 1.0),
                            'incorrect': test.scoring_scheme.get('incorrect', -0.25)
                        },
                        'questions': [q.id for q in test.questions.all()] if test.questions.exists() else [],
                        'question_filters': test.question_filters if test.question_filters else {}
                    },
                    'subjects': subjects,
                    'questions': questions,
                    'topics': topics,
                    'difficulties': ["Easy", "Medium", "Hard"],
                },
                template_name='examination/teacher/test_form.html'
            )
        return Response(serializer.data)

    def post(self, request, pk):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('teacher_dashboard')
            return Response(
                {"error": "Account not active or verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            test = Test.objects.get(pk=pk, created_by=request.user)
        except Test.DoesNotExist:
            logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Test not found or not owned by you.")
                return redirect('test_list')
            return Response(
                {"error": "Test not found or not owned by you"},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.accepted_renderer.format == 'html':
            raw = request.POST
            processed_data = {
                'title': raw.get('title', test.title).strip(),
                'subject': raw.get('subjects', str(test.subject.id) if test.subject else ''),  # Use single subject
                'duration': raw.get('duration', test.duration),
                'max_attempts': raw.get('max_attempts', test.max_attempts),
            }

            # Scoring scheme
            correct = raw.get('scoring_scheme_correct', '').strip() or str(test.scoring_scheme.get('correct', 1.0))
            incorrect = raw.get('scoring_scheme_incorrect', '').strip() or str(test.scoring_scheme.get('incorrect', -0.25))
            try:
                processed_data['scoring_scheme'] = {
                    'correct': float(correct),
                    'incorrect': float(incorrect)
                }
            except (ValueError, TypeError):
                processed_data['scoring_scheme'] = {
                    'correct': test.scoring_scheme.get('correct', 1.0),
                    'incorrect': test.scoring_scheme.get('incorrect', -0.25)
                }

            # Question selection
            if raw.get('question_selection') == 'auto':
                topics = raw.getlist('question_filters_topic')  # Support multiple topics
                processed_data['question_filters'] = {}
                if topics:
                    processed_data['question_filters']['topic'] = topics
                    difficulty_map = {'Easy': 'E', 'Medium': 'M', 'Hard': 'H'}
                    diff = raw.get('question_filters_difficulty', '').strip() or (test.question_filters.get('difficulty') if test.question_filters else '')
                    if diff in ['E', 'M', 'H']:
                        processed_data['question_filters']['difficulty'] = difficulty_map[diff]
                processed_data['questions'] = []
            else:
                processed_data['questions'] = raw.getlist('questions') or [q.id for q in test.questions.all()]
                processed_data['question_filters'] = {}

        else:
            processed_data = request.data

        serializer = TestSerializer(test, data=processed_data, context={'request': request})
        if serializer.is_valid():
            updated_test = serializer.save()
            logger.info(f"Test {updated_test.id} updated by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Test updated successfully.")
                return redirect('test_list')
            return Response(serializer.data, status=status.HTTP_200_OK)

        logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
        if request.accepted_renderer.format == 'html':
            subjects = Subject.objects.all()
            questions = Question.objects.filter(is_active=True)
            topics = Topic.objects.all()
            return Response(
                {
                    'is_update': True,
                    'test': test,
                    'errors': serializer.errors,
                    'form_data': processed_data,
                    'subjects': subjects,
                    'questions': questions,
                    'topics': topics,
                    'difficulties': ["Easy", "Medium", "Hard"],
                },
                template_name='examination/teacher/test_form.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestUpdateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

    


#     def get(self, request, pk):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Test not found or not owned by you.")
#                 return redirect('test_list')
#             return Response(
#                 {"error": "Test not found or not owned by you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = TestSerializer(test)
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'is_update': True,
#                     'test': test,
#                     'form_data': {
#                         'title': test.title,
#                         'subjects': [s.id for s in test.subjects.all()],
#                         'duration': test.duration,
#                         'max_attempts': test.max_attempts,
#                         'scoring_scheme': {
#                             'correct': test.scoring_scheme.get('correct', 1.0),
#                             'incorrect': test.scoring_scheme.get('incorrect', -0.25)
#                         },
#                         'questions': [q.id for q in test.questions.all()] if test.questions.exists() else [],
#                         'question_filters': test.question_filters if test.question_filters else {}
#                     },
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     # 'difficulties': ["E", "M", "H"]
#                     'difficulties': ["Easy", "Medium", "Hard"],
#                 },
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response(serializer.data)

#     def post(self, request, pk):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Test not found or not owned by you.")
#                 return redirect('test_list')
#             return Response(
#                 {"error": "Test not found or not owned by you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         if request.accepted_renderer.format == 'html':
#             raw = request.POST
#             processed_data = {
#                 'title': raw.get('title', test.title).strip(),
#                 'subjects': raw.getlist('subjects'),
#                 'duration': raw.get('duration', test.duration),
#                 'max_attempts': raw.get('max_attempts', test.max_attempts),
#             }

#             # Scoring scheme
#             correct = raw.get('scoring_scheme_correct', '').strip() or str(test.scoring_scheme.correct)
#             incorrect = raw.get('scoring_scheme_incorrect', '').strip() or str(test.scoring_scheme.incorrect)
#             try:
#                 processed_data['scoring_scheme'] = {
#                     'correct': float(correct),
#                     'incorrect': float(incorrect)
#                 }
#             except (ValueError, TypeError):
#                 processed_data['scoring_scheme'] = {
#                     'correct': test.scoring_scheme.correct,
#                     'incorrect': test.scoring_scheme.incorrect
#                 }

#             # Question selection
#             if raw.get('question_selection') == 'auto':
#                 topic = raw.get('question_filters_topic', '').strip() or (test.question_filters.get('topic') if test.question_filters else '')
#                 processed_data['question_filters'] = {}
#                 if topic:
#                     processed_data['question_filters']['topic'] = topic
#                     difficulty_map = {'Easy': 'E', 'Medium': 'M', 'Hard': 'H'}
#                     diff = raw.get('question_filters_difficulty', '').strip() or (test.question_filters.get('difficulty') if test.question_filters else '')
#                     diff = difficulty_map.get(diff, diff)
#                     if diff in ['E', 'M', 'H']:
#                         processed_data['question_filters']['difficulty'] = diff
#                 processed_data['questions'] = []
#             else:
#                 processed_data['questions'] = raw.getlist('questions') or [q.id for q in test.questions.all()]
#                 processed_data['question_filters'] = {}

#         else:
#             processed_data = request.data

#         serializer = TestSerializer(test, data=processed_data, context={'request': request})
#         if serializer.is_valid():
#             updated_test = serializer.save()
#             logger.info(f"Test {updated_test.id} updated by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test updated successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'is_update': True,
#                     'test': test,
#                     'errors': serializer.errors,
#                     'form_data': processed_data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     # 'difficulties': ["E", "M", "H"]
#                     'difficulties': ["Easy", "Medium", "Hard"],
                    
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H']
#                 },
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response({"message": "Test creation endpoint (GET)"}, status=status.HTTP_200_OK)

#     def post(self, request):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Convert form data for ManyToMany and JSON fields
#         data = request.data.copy()
#         if 'subjects' in data and isinstance(data['subjects'], str):
#             data.setlist('subjects', data['subjects'].split(','))
#         if 'questions' in data and isinstance(data['questions'], str):
#             data.setlist('questions', data['questions'].split(','))
#         if 'scoring_scheme_correct' in data and 'scoring_scheme_incorrect' in data:
#             data['scoring_scheme'] = {
#                 'correct': float(data.pop('scoring_scheme_correct')[0]),
#                 'incorrect': float(data.pop('scoring_scheme_incorrect')[0])
#             }
#         if 'question_filters_topic' in data:
#             data['question_filters'] = {'topic': data.pop('question_filters_topic')[0]}
#             if 'question_filters_difficulty' in data and data['question_filters_difficulty']:
#                 data['question_filters']['difficulty'] = data.pop('question_filters_difficulty')[0]

#         serializer = TestSerializer(data=data, context={'request': request})
#         if serializer.is_valid():
#             test = serializer.save(created_by=request.user)
#             logger.info(f"Test {test.id} created by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test created successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'errors': serializer.errors,
#                     'form_data': request.data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H']
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True, created_by=request.user)
#             return Response(
#                 {'subjects': subjects, 'questions': questions},
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response({"message": "Test creation endpoint (GET)"}, status=status.HTTP_200_OK)

#     def post(self, request):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         serializer = TestSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             test = serializer.save(created_by=request.user)
#             logger.info(f"Test {test.id} created by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test created successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True, created_by=request.user)
#             return Response(
#                 {
#                     'errors': serializer.errors,
#                     'form_data': request.data,
#                     'subjects': subjects,
#                     'questions': questions
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#! corect testcreate start form 157
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'is_update': False,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H'],
#                     'difficulties': ["Easy", "Medium", "Hard"],
#         'form_data': request.POST if request.method == "POST" else {},
#         'errors': {}
#                 },
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response({"message": "Test creation endpoint (GET)"}, status=status.HTTP_200_OK)

#     def post(self, request):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )


#         if request.accepted_renderer.format == 'html':
#             raw = request.POST  # QueryDict
#             python_data = {
#                 'title': raw.get('title', '').strip(),
#                 'subjects': raw.getlist('subjects'),
#                 # Manual selection: raw.getlist('questions'),
#                 # Auto-selection you’ll handle below…
#                 'duration': raw.get('duration', ''),
#                 'max_attempts': raw.get('max_attempts', ''),
#             }

#             # Scoring scheme
#             correct = raw.get('scoring_scheme_correct', '').strip()
#             incorrect = raw.get('scoring_scheme_incorrect', '').strip()
#             try:
#                 python_data['scoring_scheme'] = {
#                     'correct': float(correct),
#                     'incorrect': float(incorrect)
#                 }
#             except (ValueError, TypeError):
#                 python_data['scoring_scheme'] = {}  # will fail validation later

#             # Question filters
#             if raw.get('question_selection') == 'auto':
#                 topic = raw.get('question_filters_topic', '').strip()
#                 if topic:
#                     filters = {'topic': topic}
#                     diff = raw.get('question_filters_difficulty', '').strip()
#                     if diff:
#                         filters['difficulty'] = diff
#                     python_data['question_filters'] = filters
#                 else:
#                     python_data['question_filters'] = {}
#             else:
#                 python_data['question_filters'] = {}
#                 python_data['questions'] = raw.getlist('questions')

#         else:
#             # JSON API: DRF already gave us a dict of native types
#             python_data = request.data

#         # 3) Now pass that clean dict into your serializer
#         serializer = TestSerializer(data=python_data, context={'request': request})
#         if serializer.is_valid():
#             test = serializer.save(created_by=request.user)
#             logger.info(f"Test {test.id} created by {test.created_by.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test created successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'errors': serializer.errors,
#                     'form_data': request.data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H']
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H']
#                 },
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response({"message": "Test creation endpoint (GET)"}, status=status.HTTP_200_OK)

#     def post(self, request):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Convert form data for HTML, preserve JSON data
#         data = request.data.copy()
#         if request.accepted_renderer.format == 'html':
#             if 'subjects' in data and isinstance(data['subjects'], str):
#                 data.setlist('subjects', data['subjects'].split(','))
#             if 'questions' in data and isinstance(data['questions'], str):
#                 data.setlist('questions', data['questions'].split(','))
#             if 'scoring_scheme_correct' in data and 'scoring_scheme_incorrect' in data:
#                 data['scoring_scheme'] = {
#                     'correct': float(data.pop('scoring_scheme_correct')[0]),
#                     'incorrect': float(data.pop('scoring_scheme_incorrect')[0])
#                 }
#             if 'question_filters_topic' in data:
#                 data['question_filters'] = {'topic': data.pop('question_filters_topic')[0]}
#                 if 'question_filters_difficulty' in data and data['question_filters_difficulty']:
#                     data['question_filters']['difficulty'] = data.pop('question_filters_difficulty')[0]

#         serializer = TestSerializer(data=data, context={'request': request})
#         if serializer.is_valid():
#             test = serializer.save(created_by=request.user)
#             logger.info(f"Test {test.id} created by {test.created_by.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test created successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'errors': serializer.errors,
#                     'form_data': request.data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H']
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def post(self, request):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create test")
#             return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
#         serializer = TestSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestListView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if not request.user.is_active:
#             logger.warning(f"Inactive user {request.user.email} attempted to list tests")
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         if request.user.role == User.Role.TEACHER:
#             queryset = Test.objects.filter(created_by=request.user)
#         elif request.user.role == User.Role.STUDENT:
#             queryset = Test.objects.all()
#         else:
#             logger.warning(f"Invalid role {request.user.role} for {request.user.email}")
#             return Response({"error": "Invalid role"}, status=status.HTTP_403_FORBIDDEN)

#         # Filters
#         subject_id = request.query_params.get('subject')
#         if subject_id:
#             try:
#                 queryset = queryset.filter(subjects__id=subject_id)
#             except ValueError:
#                 return Response({"error": "Invalid subject ID"}, status=status.HTTP_400_BAD_REQUEST)

#         status_filter = request.query_params.get('status')
#         if status_filter == 'active':
#             queryset = queryset.filter(schedule_start__lte=timezone.now(), schedule_end__gte=timezone.now())
#         elif status_filter == 'upcoming':
#             queryset = queryset.filter(schedule_start__gt=timezone.now())
#         elif status_filter == 'expired':
#             queryset = queryset.filter(schedule_end__lt=timezone.now())

#         paginator = Paginator(queryset, 20)
#         page = request.query_params.get('page', 1)
#         try:
#             tests = paginator.page(page)
#         except EmptyPage:
#             logger.warning(f"Invalid page {page} for test list by {request.user.email}")
#             return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)

#         serializer = TestSerializer(tests, many=True)
#         logger.info(f"Test list retrieved by {request.user.email} (role: {request.user.role})")
#         return Response({
#             "count": paginator.count,
#             "results": serializer.data
#         })

#! import test update start from 409
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestUpdateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request, pk):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Test not found or not owned by you.")
#                 return redirect('test_list')
#             return Response(
#                 {"error": "Test not found or not owned by you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = TestSerializer(test)
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'test': test,
#                     'form_data': serializer.data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H']
#                 },
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response(serializer.data)

#     def post(self, request, pk):  # POST to simulate PUT for HTML forms
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Test not found or not owned by you.")
#                 return redirect('test_list')
#             return Response(
#                 {"error": "Test not found or not owned by you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

        
#         if request.accepted_renderer.format == 'html':
#             raw = request.POST
#             processed_data = {
#                 'title': raw.get('title', '').strip(),
#                 'subjects': raw.getlist('subjects'),
#                 'duration': raw.get('duration', 10),
#                 'max_attempts': raw.get('max_attempts', 1),
#             }
#             # questions
#             if raw.get('question_selection') == 'manual':
#                 processed_data['questions'] = raw.getlist('questions')
#             else:
#                 processed_data['questions'] = []  # or leave out if your serializer handles missing
#             # scoring_scheme
#             try:
#                 processed_data['scoring_scheme'] = {
#                     'correct': float(raw.get('scoring_scheme_correct', 0)),
#                     'incorrect': float(raw.get('scoring_scheme_incorrect', 0)),
#                 }
#             except (ValueError, TypeError):
#                 processed_data['scoring_scheme'] = {}
#             # question_filters
#             if raw.get('question_selection') == 'auto':
#                 filters = {}
#                 topic = raw.get('question_filters_topic', '').strip()
#                 if topic:
#                     filters['topic'] = topic
#                     diff = raw.get('question_filters_difficulty', '').strip()
#                     if diff in ['E', 'M', 'H']:
#                         filters['difficulty'] = diff
#                 processed_data['question_filters'] = filters
#         else:
#             processed_data['question_filters'] = {}
#         serializer = TestSerializer(test, data=processed_data, context={'request': request})
#         if serializer.is_valid():
#             updated_test = serializer.save()
#             logger.info(f"Test {updated_test.id} updated by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test updated successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True)
#             topics = Topic.objects.all()
#             return Response(
#                 {
#                     'errors': serializer.errors,
#                     'form_data': request.data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'topics': topics,
#                     'difficulties': ['E', 'M', 'H'],
#                     'test': test
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestUpdateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request, pk):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Test not found or not owned by you.")
#                 return redirect('test_list')
#             return Response(
#                 {"error": "Test not found or not owned by you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = TestSerializer(test)
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True, created_by=request.user)
#             print(serializer.data)
#             return Response(
#                 {
#                     'test': test,
#                     'form_data': serializer.data,
#                     'subjects': subjects,
#                     'questions': questions
#                 },
#                 template_name='examination/teacher/test_form.html'
#             )
#         return Response(serializer.data)

#     def post(self, request, pk):  # POST to simulate PUT for HTML forms
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Test not found or not owned by you.")
#                 return redirect('test_list')
#             return Response(
#                 {"error": "Test not found or not owned by you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = TestSerializer(test, data=request.data, context={'request': request})
#         if serializer.is_valid():
#             updated_test = serializer.save()
#             logger.info(f"Test {updated_test.id} updated by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Test updated successfully.")
#                 return redirect('test_list')
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             subjects = Subject.objects.all()
#             questions = Question.objects.filter(is_active=True, created_by=request.user)
#             return Response(
#                 {
#                     'errors': serializer.errors,
#                     'form_data': request.data,
#                     'subjects': subjects,
#                     'questions': questions,
#                     'test': test
#                 },
#                 template_name='examination/teacher/test_form.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# class TestUpdateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def put(self, request, pk):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update test {pk}")
#             return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             return Response({"error": "Test not found or not owned by you"}, status=status.HTTP_404_NOT_FOUND)

#         if TestAttempt.objects.filter(test=test).exists():
#             logger.warning(f"Test {pk} update failed: Already attempted")
#             return Response({"error": "Cannot update test with attempts"}, status=status.HTTP_403_FORBIDDEN)

#         serializer = TestSerializer(test, data=request.data, context={'request': request})
#         if serializer.is_valid():
#             updated_test = serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@method_decorator(ensure_csrf_cookie, name='dispatch')
class TestDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def post(self, request, pk):  # POST for HTML form compatibility
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to delete test {pk}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('teacher_dashboard')
            return Response(
                {"error": "Account not active or verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            test = Test.objects.get(pk=pk, created_by=request.user)
        except Test.DoesNotExist:
            logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Test not found or not owned by you.")
                return redirect('test_list')
            return Response(
                {"error": "Test not found or not owned by you"},
                status=status.HTTP_404_NOT_FOUND
            )

        

        test.delete()
        logger.info(f"Test {pk} deleted by {request.user.email}")
        if request.accepted_renderer.format == 'html':
            messages.success(request, "Test deleted successfully.")
            return redirect('test_list')
        return Response(status=status.HTTP_204_NO_CONTENT)
# class TestDeleteView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def delete(self, request, pk):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to delete test {pk}")
#             return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             test = Test.objects.get(pk=pk, created_by=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {pk} not found or not owned by {request.user.email}")
#             return Response({"error": "Test not found or not owned by you"}, status=status.HTTP_404_NOT_FOUND)

#         if TestAttempt.objects.filter(test=test).exists():
#             logger.warning(f"Test {pk} deletion failed: Already attempted")
#             return Response({"error": "Cannot delete test with attempts"}, status=status.HTTP_403_FORBIDDEN)

#         test.delete()
#         logger.info(f"Test {pk} deleted by {request.user.email}")
#         return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TestListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        logger.info(f"TestListView accessed by {request.user.email} (role: {request.user.role})")

        if not request.user.is_active:
            logger.warning(f"Inactive user {request.user.email} attempted to list tests")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is inactive.")
                return redirect('dashboard')
            return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)

        # Queryset based on role
        if request.user.role == 'TE':
            base_query = Test.objects.filter(created_by=request.user)
        elif request.user.role == 'ST':
            base_query = Test.objects.all()
        else:
            logger.warning(f"Unauthorized role: {request.user.role}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Invalid user role.")
                return redirect('dashboard')
            return Response({"error": "Invalid user role"}, status=status.HTTP_403_FORBIDDEN)

        # Initialize filter Q objects
        filters = Q()
        question_filters = Q()

        # Subject filter (direct on Test model)
        if subject_id := request.query_params.get('subject'):
            try:
                filters &= Q(subject__id=subject_id)
            except ValueError:
                logger.error(f"Invalid subject ID: {subject_id}")
                if request.accepted_renderer.format == 'html':
                    messages.error(request, "Invalid subject ID.")
                    return redirect('test_list')
                return Response({"error": "Invalid subject ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Topic filter (through questions)
        if topic_id := request.query_params.get('topic'):
            try:
                question_filters &= Q(topics__id=topic_id)
            except ValueError:
                logger.error(f"Invalid topic ID: {topic_id}")

        # Difficulty filter (through questions)
        if difficulty := request.query_params.get('difficulty'):
            difficulty_map = {'Easy': 'E', 'Medium': 'M', 'Hard': 'H'}
            if mapped_diff := difficulty_map.get(difficulty):
                question_filters &= Q(difficulty=mapped_diff)

        # Date filter
        if created_after := request.query_params.get('created_after'):
            try:
                filters &= Q(created_at__gte=parse_date(created_after))
            except (ValueError, TypeError):
                logger.error(f"Invalid date format: {created_after}")

        # Apply question-related filters through questions relationship
        if question_filters:
            filters &= Q(questions__in=Question.objects.filter(question_filters))

        # Final queryset with distinct results
        queryset = base_query.filter(filters).distinct()

        logger.debug(f"Final queryset for {request.user.email}: {queryset.values('id', 'title', 'duration')}")

        # Pagination for HTML
        if request.accepted_renderer.format == 'html':
            paginator = Paginator(queryset, 20)
            page = request.query_params.get('page', 1)
            
            try:
                tests = paginator.page(page)
            except EmptyPage:
                logger.warning(f"Invalid page {page} for test list by {request.user.email}")
                messages.error(request, "Page not found.")
                return redirect('test_list')

            # Get filter options
            subjects = Subject.objects.all()
            topics = Topic.objects.all()
            difficulties = ['Easy', 'Medium', 'Hard']

            template_name = 'examination/test/test_list.html' if request.user.role == 'TE' else 'examination/test/test_list.html'
            
            return Response(
                {
                    'count': paginator.count,
                    'results': tests,
                    'subjects': subjects,
                    'topics': topics,
                    'difficulties': difficulties,
                    'current_filters': request.query_params.dict()
                },
                template_name=template_name
            )

        # JSON response
        serializer = TestSerializer(queryset, many=True)
        return Response(serializer.data)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestListView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         logger.info(f"TestListView accessed by {request.user.email} (role: {request.user.role})")

#         if not request.user.is_active:
#             logger.warning(f"Inactive user {request.user.email} attempted to list tests")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is inactive.")
#                 return redirect('dashboard')
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)

#         # Queryset based on role
#         if request.user.role == 'TE':
#             queryset = Test.objects.filter(created_by=request.user)
#         elif request.user.role == 'ST':
#             queryset = Test.objects.all()
#         else:
#             logger.warning(f"Unauthorized role: {request.user.role}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Invalid user role.")
#                 return redirect('dashboard')
#             return Response({"error": "Invalid user role"}, status=status.HTTP_403_FORBIDDEN)

#         # Subject filter
#         subject_id = request.query_params.get('subject')
#         if subject_id:
#             try:
#                 queryset = queryset.filter(subject__id=subject_id)
#             except ValueError:
#                 logger.error(f"Invalid subject ID: {subject_id}")
#                 if request.accepted_renderer.format == 'html':
#                     messages.error(request, "Invalid subject ID.")
#                     return redirect('test_list')
#                 return Response({"error": "Invalid subject ID"}, status=status.HTTP_400_BAD_REQUEST)

#         logger.debug(f"Queryset for {request.user.email}: {queryset.values('id', 'title', 'duration')}")

#         # Pagination for HTML
#         if request.accepted_renderer.format == 'html':
#             paginator = Paginator(queryset, 20)
#             page = request.query_params.get('page', 1)
#             try:
#                 tests = paginator.page(page)
#             except EmptyPage:
#                 logger.warning(f"Invalid page {page} for test list by {request.user.email}")
#                 messages.error(request, "Page not found.")
#                 return redirect('test_list')

#             subjects = Subject.objects.all()
#             template_name = 'examination/teacher/test_list.html' if request.user.role == 'TE' else 'examination/student/test_list.html'
#             return Response(
#                 {
#                     'count': paginator.count,
#                     'results': tests,
#                     'subjects': subjects,
#                     'current_filters': request.query_params
#                 },
#                 template_name=template_name
#             )

#         # JSON response
#         serializer = TestSerializer(queryset, many=True)
#         return Response(serializer.data)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestListView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         logger.info(f"TestListView accessed by {request.user.email} (role: {request.user.role})")

#         if not request.user.is_active:
#             logger.warning(f"Inactive user {request.user.email} attempted to list tests")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is inactive.")
#                 return redirect('dashboard')  # Generic dashboard, adjust in Task 7
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)

#         # Queryset based on role
#         if request.user.role == 'TE':
#             queryset = Test.objects.filter(created_by=request.user)
#         elif request.user.role == 'ST':
#             queryset = Test.objects.all()  # Students see all available tests
#         else:
#             logger.warning(f"Unauthorized role: {request.user.role}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Invalid user role.")
#                 return redirect('dashboard')
#             return Response({"error": "Invalid user role"}, status=status.HTTP_403_FORBIDDEN)

#         # Subject filter
#         subject_id = request.query_params.get('subject')
#         if subject_id:
#             print(subject_id)
#             try:
#                 queryset = queryset.filter(subjects__id=subject_id)
#                 print(queryset)
#             except ValueError:
#                 logger.error(f"Invalid subject ID: {subject_id}")
#                 if request.accepted_renderer.format == 'html':
#                     messages.error(request, "Invalid subject ID.")
#                     return redirect('test_list')
#                 return Response({"error": "Invalid subject ID"}, status=status.HTTP_400_BAD_REQUEST)

#         logger.debug(f"Queryset for {request.user.email}: {queryset.values('id', 'title', 'duration')}")

#         # Pagination for HTML
#         if request.accepted_renderer.format == 'html':
#             paginator = Paginator(queryset, 20)
#             page = request.query_params.get('page', 1)
#             try:
#                 tests = paginator.page(page)
#             except EmptyPage:
#                 logger.warning(f"Invalid page {page} for test list by {request.user.email}")
#                 messages.error(request, "Page not found.")
#                 return redirect('test_list')

#             subjects = Subject.objects.all()
#             template_name = 'examination/teacher/test_list.html' if request.user.role == 'TE' else 'examination/student/test_list.html'
#             for result in tests:
#                 print('result:',result.subjects)
#             return Response(
#                 {
#                     'count': paginator.count,
#                     'results': tests,
#                     'subjects': subjects,
#                     'current_filters': request.query_params
#                 },
#                 template_name=template_name
#             )

#         # JSON response
#         serializer = TestSerializer(queryset, many=True)
#         return Response(serializer.data)


# class TestListView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def get(self, request):
#         logger.info(f"TestListView accessed by {request.user.email} (role: {request.user.role})")
        
#         if request.user.role == User.Role.TEACHER:
#             queryset = Test.objects.filter(created_by=request.user)
#         elif request.user.role == User.Role.STUDENT:
#             queryset = Test.objects.all()  # Students see all available tests
#         else:
#             logger.warning(f"Unauthorized role: {request.user.role}")
#             return Response({"error": "Invalid user role"}, status=status.HTTP_403_FORBIDDEN)

#         subject_id = request.query_params.get('subject')
#         if subject_id:
#             try:
#                 queryset = queryset.filter(subjects__id=subject_id)
#             except ValueError:
#                 logger.error(f"Invalid subject ID: {subject_id}")
#                 return Response({"error": "Invalid subject ID"}, status=status.HTTP_400_BAD_REQUEST)

#         logger.debug(f"Queryset for {request.user.email}: {queryset.values('id', 'title', 'duration')}")
        
#         serializer = TestSerializer(queryset, many=True)
#         return Response(serializer.data)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TestAttemptView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get_renderers(self):
        # Force PATCH to only use JSONRenderer
        if self.request.method.lower() == 'patch':
            return [JSONRenderer()]
        return super().get_renderers()

    def get(self, request, pk=None):
        logger.debug('Processing GET request for TestAttemptView')
        if pk:
            try:
                attempt = TestAttempt.objects.get(pk=pk, student=request.user)
                serializer = TestAttemptSerializer(attempt)
                if request.accepted_renderer.format == 'html':
                    responses = StudentResponse.objects.filter(attempt=attempt)
                    return Response(
                        {
                            'user': request.user,
                            'attempt': attempt,
                            'test': attempt.test,
                            'questions': attempt.test.questions.all(),
                            'responses': {r.question.id: r for r in responses}
                        },
                        template_name='examination/student/test_attempt.html'
                    )
                return Response(serializer.data)
            except TestAttempt.DoesNotExist:
                logger.warning(f"Attempt {pk} not found for {request.user.email}")
                if request.accepted_renderer.format == 'html':
                    messages.error(request, "Attempt not found.")
                    return redirect('student_dashboard')
                return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

        attempts = TestAttempt.objects.filter(student=request.user)
        serializer = TestAttemptSerializer(attempts, many=True)
        if request.accepted_renderer.format == 'html':
            return Response(
                {'user': request.user, 'attempts': attempts},
                template_name='examination/student/test_attempts.html'
            )
        return Response(serializer.data)

    def post(self, request):
        logger.debug(f"POST request data: {request.body}")
        serializer = TestAttemptSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attempt = serializer.save()
            logger.info(f"Attempt {attempt.id} started by {request.user.email} for test {attempt.test.id}")
            if request.accepted_renderer.format == 'html':
                return redirect('attempt_detail', pk=attempt.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Attempt creation failed for {request.user.email}: {serializer.errors}")
        if request.accepted_renderer.format == 'html':
            messages.error(request, "Failed to start test.")
            return redirect('student_dashboard')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            attempt = TestAttempt.objects.get(pk=pk, student=request.user)
        except TestAttempt.DoesNotExist:
            return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

        if attempt.end_time:
            return Response({"error": "Attempt already submitted"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        deadline = attempt.start_time + timedelta(minutes=attempt.test.duration)
        if now > deadline:
            attempt.end_time = deadline
            attempt.calculate_score()
            attempt.save()
            return Response(
                {"error": "Test duration expired", "score": attempt.score},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate scoring_scheme
        scoring_scheme = attempt.test.scoring_scheme or {'correct': 1, 'incorrect': 0}
        if not isinstance(scoring_scheme, dict) or 'correct' not in scoring_scheme:
            logger.warning(f"Invalid scoring_scheme for test {attempt.test.id}: {scoring_scheme}")
            scoring_scheme = {'correct': 1, 'incorrect': 0}
        logger.debug(f"Scoring scheme for test {attempt.test.id}: {scoring_scheme}")

        # Clear any prior responses
        StudentResponse.objects.filter(attempt=attempt).delete()
        logger.debug(f"Deleted prior StudentResponse objects for attempt {attempt.id}")

        total_time = 0
        correct_count = 0
        total_q = attempt.test.questions.count()

        # Handle both FormData (from test_attempt.html) and JSON (from API)
        resp_list = request.data.get('responses', [])
        if not resp_list and request.POST:
            # FormData case: parse request.POST
            raw = request.POST
            form_data_log = {key: raw.get(key) for key in raw}
            logger.debug(f"FormData received for attempt {attempt.id}: {form_data_log}")
            resp_list = []
            for question in attempt.test.questions.all():
                ans = raw.get(f'answer_{question.id}', '').strip().upper()
                time_taken = int(raw.get(f'time_taken_{question.id}', 0))
                resp_list.append({
                    'question': question.id,
                    'selected_answer': ans,
                    'time_taken': time_taken
                })
        else:
            # JSON case: log received payload
            logger.debug(f"JSON responses received for attempt {attempt.id}: {resp_list}")

        for item in resp_list:
            try:
                q = Question.objects.get(pk=item['question'])
            except Question.DoesNotExist:
                logger.error(f"Question {item.get('question')} not found")
                continue
            ans = item.get('selected_answer', '').strip().upper() if item.get('selected_answer') else ''
            is_correct = False
            if ans:
                is_correct = (ans == q.correct_answer.upper())
                if is_correct:
                    correct_count += 1
            time_taken = int(item.get('time_taken', 0))
            total_time += time_taken

            # Log question details
            logger.debug(f"Processing question {q.id}: correct_answer={q.correct_answer}, selected_answer={ans}, is_correct={is_correct}, time_taken={time_taken}")

            serializer = StudentResponseSerializer(
                data={
                    'attempt': attempt.id,
                    'question': q.id,
                    'selected_answer': ans,
                    'is_correct': is_correct,
                    'time_taken': time_taken
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            response = serializer.save()
            logger.debug(f"Created StudentResponse {response.id} for question {q.id}: selected_answer={ans}, is_correct={is_correct}, time_taken={time_taken}")

        # Log StudentResponse objects after creation
        responses = StudentResponse.objects.filter(attempt=attempt)
        response_log = [
            {
                'response_id': r.id,
                'question_id': r.question.id,
                'selected_answer': r.selected_answer,
                'is_correct': r.is_correct,
                'time_taken': r.time_taken
            } for r in responses
        ]
        logger.debug(f"StudentResponse objects for attempt {attempt.id}: {response_log}")

        attempt.performance_metrics = {
            'accuracy': correct_count / total_q if total_q else 0,
            'avg_time_per_question': total_time / total_q if total_q else 0
        }
        logger.debug(f"Performance metrics for attempt {attempt.id}: correct_count={correct_count}, total_questions={total_q}, total_time={total_time}")

        attempt.end_time = now
        logger.debug(f"Calling calculate_score for attempt {attempt.id} with scoring_scheme={scoring_scheme}")
        attempt.calculate_score()
        logger.debug(f"Score calculated for attempt {attempt.id}: score={attempt.score}")
        attempt.save()
        logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {attempt.score}")

        return Response({
            'id': attempt.id,
            'score': attempt.score,
            'performance_metrics': attempt.performance_metrics
        }, status=status.HTTP_200_OK)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestAttemptView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]


#     def get_renderers(self):
#         # Force PATCH to only use JSONRenderer
#         if self.request.method.lower() == 'patch':
#             return [JSONRenderer()]
#         return super().get_renderers()

#     def get(self, request, pk=None):
#         print('mujia yaad kar lia ')
#         if pk:
#             try:
#                 attempt = TestAttempt.objects.get(pk=pk, student=request.user)
#                 serializer = TestAttemptSerializer(attempt)
#                 if request.accepted_renderer.format == 'html':
#                     responses = StudentResponse.objects.filter(attempt=attempt)
#                     return Response(
#                         {
#                             'user': request.user,
#                             'attempt': attempt,
#                             'test': attempt.test,
#                             'questions': attempt.test.questions.all(),
#                             'responses': {r.question.id: r for r in responses}
#                         },
#                         template_name='examination/student/test_attempt.html'
#                     )
#                 return Response(serializer.data)
#             except TestAttempt.DoesNotExist:
#                 logger.warning(f"Attempt {pk} not found for {request.user.email}")
#                 if request.accepted_renderer.format == 'html':
#                     messages.error(request, "Attempt not found.")
#                     return redirect('student_dashboard')
#                 return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

#         attempts = TestAttempt.objects.filter(student=request.user)
#         serializer = TestAttemptSerializer(attempts, many=True)
#         if request.accepted_renderer.format == 'html':
#             return Response(
#                 {'user': request.user, 'attempts': attempts},
#                 template_name='examination/student/test_attempts.html'
#             )
#         return Response(serializer.data)

#     def post(self, request):
#          print('mia post hu yia data hia :',request.body)
#          serializer = TestAttemptSerializer(data=request.data, context={'request': request})
#          if serializer.is_valid():
#              attempt = serializer.save()
#              logger.info(f"Attempt {attempt.id} started by {request.user.email} for test {attempt.test.id}")
#              if request.accepted_renderer.format == 'html':
#                  return redirect('attempt_detail', pk=attempt.id)
#              return Response(serializer.data, status=status.HTTP_201_CREATED)
#          logger.warning(f"Attempt creation failed for {request.user.email}: {serializer.errors}")
#          if request.accepted_renderer.format == 'html':
#              messages.error(request, "Failed to start test.")
#              return redirect('student_dashboard')
#          return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

#     def patch(self, request, pk):
#         try:
#             attempt = TestAttempt.objects.get(pk=pk, student=request.user)
#         except TestAttempt.DoesNotExist:
#             return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

#         if attempt.end_time:
#             return Response({"error": "Attempt already submitted"}, status=status.HTTP_400_BAD_REQUEST)

#         now = timezone.now()
#         deadline = attempt.start_time + timedelta(minutes=attempt.test.duration)
#         if now > deadline:
#             attempt.end_time = deadline
#             attempt.calculate_score()
#             attempt.save()
#             return Response(
#                 {"error": "Test duration expired", "score": attempt.score},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Process all responses in one go, using POSTed form data
#         if request.accepted_renderer.format == 'html':
#             raw = request.POST
#             total_time = 0
#             correct_count = 0

#             # Clear any prior responses
#             StudentResponse.objects.filter(attempt=attempt).delete()

#             for question in attempt.test.questions.all():
#                 ans = raw.get(f'answer_{question.id}', '').strip()
#                 if not ans:
#                     continue
#                 time_taken = int(raw.get(f'time_taken_{question.id}', 0))
#                 is_correct = (ans == question.correct_answer)
#                 if is_correct:
#                     correct_count += 1
#                 total_time += time_taken

#                 StudentResponse.objects.create(
#                     attempt=attempt,
#                     question=question,
#                     selected_answer=ans,
#                     is_correct=is_correct,
#                     time_taken=time_taken
#                 )

#             total_q = attempt.test.questions.count()
#             attempt.performance_metrics = {
#                 'accuracy': correct_count / total_q if total_q else 0,
#                 'avg_time_per_question': total_time / total_q if total_q else 0
#             }

#         else:
#             # # JSON API: single bulk "responses" payload
#             # resp_list = request.data.get('responses', [])
#             # total_time = 0
#             # correct_count = 0
#             StudentResponse.objects.filter(attempt=attempt).delete()
#             for question in attempt.test.questions.all():
#                 ans = raw.get(f'answer_{question.id}', '').strip()
#                 if not ans:
#                     continue
#                 time_taken = int(raw.get(f'time_taken_{question.id}', 0))
#                 is_correct = (ans == question.correct_answer)
#                 StudentResponse.objects.create(
#                     attempt=attempt,
#                     question=question,
#                     selected_answer=ans,
#                     is_correct=is_correct,
#                     time_taken=time_taken
#                 )
#             attempt.end_time = now
#             attempt.calculate_score()
#             attempt.save()
#             logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {attempt.score}")
#         #     StudentResponse.objects.filter(attempt=attempt).delete()

#         #     for item in resp_list:
#         #         q = Question.objects.get(pk=item['question'])
#         #         serializer = StudentResponseSerializer(
#         #             data={
#         #                 'attempt': attempt.id,
#         #                 'question': q.id,
#         #                 'selected_answer': item['selected_answer'],
#         #                 'time_taken': item['time_taken']
#         #             },
#         #             context={'request': request}
#         #         )
#         #         serializer.is_valid(raise_exception=True)
#         #         serializer.save()
#         #         total_time += item['time_taken']
#         #         if item['selected_answer'] == q.correct_answer:
#         #             correct_count += 1

#         #     total_q = attempt.test.questions.count()
#         #     attempt.performance_metrics = {
#         #         'accuracy': correct_count / total_q if total_q else 0,
#         #         'avg_time_per_question': total_time / total_q if total_q else 0
#         #     }

#         # attempt.end_time = now
#         # attempt.calculate_score()
#         # attempt.save()
#         # logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {attempt.score}")

#         # Always return JSON here (renderers override)
#         return Response({
#             'id': attempt.id,
#             'score': attempt.score,
#             'performance_metrics': attempt.performance_metrics
#         }, status=status.HTTP_200_OK)

     
    # def patch(self, request, pk):
    #     try:
    #         attempt = TestAttempt.objects.get(pk=pk, student=request.user)
    #     except TestAttempt.DoesNotExist:
    #         logger.warning(f"Attempt {pk} not found for {request.user.email}")
    #         if request.accepted_renderer.format == 'html':
    #             messages.error(request, "Attempt not found.")
    #             return redirect('student_dashboard')
    #         return Response({"error": "Attempt not found or not yours"}, status=status.HTTP_404_NOT_FOUND)

    #     if attempt.end_time:
    #         logger.warning(f"Attempt {pk} already submitted by {request.user.email}")
    #         if request.accepted_renderer.format == 'html':
    #             messages.error(request, "Attempt already submitted.")
    #             return redirect('test_results')
    #         return Response({"error": "Attempt already submitted"}, status=status.HTTP_400_BAD_REQUEST)

    #     time_limit = attempt.start_time + timedelta(minutes=attempt.test.duration)
    #     now = timezone.now()
    #     if now > time_limit:
    #         attempt.end_time = time_limit
    #         attempt.calculate_score()
    #         attempt.save()
    #         logger.info(f"Attempt {attempt.id} auto-expired for {request.user.email} with score {attempt.score}")
    #         if request.accepted_renderer.format == 'html':
    #             messages.error(request, "Test duration expired.")
    #             return redirect('test_results')
    #         return Response(
    #             {"error": "Test duration expired", "id": attempt.id, "score": attempt.score},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # Process responses from HTML form
    #     if request.accepted_renderer.format == 'html':
    #         raw = request.POST
    #         responses = {}
    #         total_time_taken = 0
    #         correct_count = 0
    #         for question in attempt.test.questions.all():
    #             answer = raw.get(f'answer_{question.id}', '').strip()
    #             if answer:
    #                 time_taken = int(raw.get(f'time_taken_{question.id}', '30'))  # Default 30s
    #                 responses[question.id] = {'selected_answer': answer, 'time_taken': time_taken}
    #                 total_time_taken += time_taken
    #                 is_correct = (answer == question.correct_answer)
    #                 if is_correct:
    #                     correct_count += 1
    #                 StudentResponse.objects.create(
    #                     attempt=attempt,
    #                     question=question,
    #                     selected_answer=answer,
    #                     is_correct=is_correct,
    #                     time_taken=time_taken
    #                 )

    #         # Update performance metrics
    #         total_questions = attempt.test.questions.count()
    #         accuracy = correct_count / total_questions if total_questions else 0
    #         avg_time = total_time_taken / total_questions if total_questions else 0
    #         attempt.performance_metrics = {
    #             'accuracy': accuracy,
    #             'avg_time_per_question': avg_time
    #         }
    #     else:
    #         # JSON API: Expect responses in data
    #         responses = request.data.get('responses', {})
    #         total_time_taken = 0
    #         correct_count = 0
    #         for question_id, response_data in responses.items():
    #             question = attempt.test.questions.get(id=question_id)
    #             serializer = StudentResponseSerializer(data={
    #                 'attempt': attempt.id,
    #                 'question': question.id,
    #                 'selected_answer': response_data['selected_answer'],
    #                 'time_taken': response_data['time_taken']
    #             }, context={'request': request})
    #             if serializer.is_valid():
    #                 serializer.save()
    #                 total_time_taken += response_data['time_taken']
    #                 if response_data['selected_answer'] == question.correct_answer:
    #                     correct_count += 1
    #             else:
    #                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #         total_questions = attempt.test.questions.count()
    #         accuracy = correct_count / total_questions if total_questions else 0
    #         avg_time = total_time_taken / total_questions if total_questions else 0
    #         attempt.performance_metrics = {
    #             'accuracy': accuracy,
    #             'avg_time_per_question': avg_time
    #         }

    #     attempt.end_time = now
    #     attempt.calculate_score()
    #     attempt.save()
    #     logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {attempt.score}")
    #     if request.accepted_renderer.format == 'html':
    #         messages.success(request, "Test submitted successfully.")
    #         return Response({'message': 'submitted'}, status=status.HTTP_200_OK)
            
            
    #     return Response({
    #         'id': attempt.id,
    #         'score': attempt.score,
    #         'performance_metrics': attempt.performance_metrics
    #     }, status=status.HTTP_200_OK)
    



@method_decorator(ensure_csrf_cookie, name='dispatch')
class TestResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request, pk=None):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Unverified student {request.user.email} attempted to view results")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not verified.")
                return redirect('student_dashboard')
            return Response({"error": "Account not verified"}, status=status.HTTP_403_FORBIDDEN)

        if pk:
            print(pk)
            try:
                attempt = TestAttempt.objects.get(pk=pk, student=request.user)
                responses = StudentResponse.objects.filter(attempt=attempt)
                if request.accepted_renderer.format == 'html':
                    return Response(
                        {
                            'user': request.user,
                            'attempt': attempt,
                            'responses': responses,
                            'performance_metrics': attempt.performance_metrics
                        },
                        template_name='examination/student/test_result_detail.html'
                    )
                return Response({
                    'attempt_id': attempt.id,
                    'test_title': attempt.test.title,
                    'score': attempt.score,
                    'max_score': attempt.test.questions.count() * attempt.test.scoring_scheme.get('correct', 1),
                    'performance_metrics': attempt.performance_metrics,
                    'responses': [{
                        'question_id': r.question.id,
                        'question_text': r.question.question_text,
                        'selected_answer': r.selected_answer,
                        'is_correct': r.is_correct,
                        'time_taken': r.time_taken
                    } for r in responses]
                })
            except TestAttempt.DoesNotExist:
                logger.warning(f"Attempt {pk} not found for {request.user.email}")
                if request.accepted_renderer.format == 'html':
                    messages.error(request, "Attempt not found.")
                    return redirect('test_results')
                return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

        attempts = TestAttempt.objects.filter(student=request.user).order_by('-end_time')
        if request.accepted_renderer.format == 'html':
            return Response(
                {'user': request.user, 'attempts': attempts},
                template_name='examination/student/test_results.html'
            )
        serializer = TestAttemptSerializer(attempts, many=True)
        return Response(serializer.data)
# class TestAttemptView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def post(self, request):
#         serializer = TestAttemptSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             attempt = serializer.save()
#             logger.info(f"Attempt {attempt.id} started by {request.user.email} for test {attempt.test.id}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, pk):
#         try:
#             attempt = TestAttempt.objects.get(pk=pk, student=request.user)
#         except TestAttempt.DoesNotExist:
#             return Response({"error": "Attempt not found or not yours"}, status=status.HTTP_404_NOT_FOUND)
        
#         if attempt.end_time:
#             return Response({"error": "Attempt already submitted"}, status=status.HTTP_400_BAD_REQUEST)
        
#         time_limit = attempt.start_time + timedelta(minutes=attempt.test.duration)
#         now = timezone.now()
#         if now > time_limit:
#             attempt.end_time = time_limit
#             attempt.calculate_score()
#             attempt.save()
#             logger.info(f"Attempt {attempt.id} auto-expired for {request.user.email} with score {attempt.score}")
#             return Response({"error": "Test duration expired", "id": attempt.id, "score": attempt.score}, status=status.HTTP_400_BAD_REQUEST)
        
#         attempt.end_time = now
#         attempt.calculate_score()
#         attempt.save()
#         logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {attempt.score}")
#         return Response({"id": attempt.id, "score": attempt.score}, status=status.HTTP_200_OK)

#     def get(self, request):
#         attempts = TestAttempt.objects.filter(student=request.user)
#         serializer = TestAttemptSerializer(attempts, many=True)
#         return Response(serializer.data)

class StudentResponseView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    def post(self, request):
        serializer = StudentResponseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            response = serializer.save()
            logger.info(f"Response {response.id} saved for question {response.question.id} by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestAttemptView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def post(self, request):
#         serializer = TestAttemptSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             attempt = serializer.save()
#             logger.info(f"Attempt {attempt.id} started by {request.user.email} for test {attempt.test.id}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, pk):
#         try:
#             attempt = TestAttempt.objects.get(pk=pk, student=request.user)
#         except TestAttempt.DoesNotExist:
#             return Response({"error": "Attempt not found or not yours"}, status=status.HTTP_404_NOT_FOUND)
        
#         if attempt.end_time:
#             return Response({"error": "Attempt already submitted"}, status=status.HTTP_400_BAD_REQUEST)
        
#         attempt.end_time = timezone.now()
#         score = attempt.calculate_score()
#         attempt.save()
#         logger.info(f"Attempt {attempt.id} submitted by {request.user.email} with score {score}")
#         return Response({"id": attempt.id, "score": score}, status=status.HTTP_200_OK)

#     def get(self, request):
#         attempts = TestAttempt.objects.filter(student=request.user)
#         serializer = TestAttemptSerializer(attempts, many=True)
#         return Response(serializer.data)

# class StudentResponseView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def post(self, request):
#         serializer = StudentResponseSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             response = serializer.save()
#             logger.info(f"Response {response.id} saved for question {response.question.id} by {request.user.email}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



























# # apps/examination/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions
# from apps.accounts.authentication import CookieTokenAuthentication
# from .models import Test
# from .serializers import TestSerializer
# from apps.common.throttles import CustomUserRateThrottle
# from apps.accounts.models import User
# from .tasks import send_test_notification_task
# from django.utils import timezone
# from django.core.paginator import Paginator, EmptyPage
# import logging
# logger = logging.getLogger(__name__)

# class IsTeacher(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == User.Role.TEACHER

# class TestCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def post(self, request):
#         if not request.user.is_active:
#             logger.warning(f"Inactive teacher {request.user.email} attempted to create test")
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         serializer = TestSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             # Validate question_filters (async via Celery)
#             question_filters = serializer.validated_data.get('question_filters', {})
#             if question_filters:
#                 from .tasks import validate_question_filters_task
#                 validate_question_filters_task.delay(
#                     serializer.validated_data['question_filters'],
#                     on_success=lambda: serializer.save(creator=request.user)
#                 )
#             else:
#                 test = serializer.save(creator=request.user)
#                 send_test_notification_task.delay(
#                     test.id, request.user.email, action="created"
#                 )
#                 logger.info(f"Test {test.id} created by {request.user.email}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         logger.warning(f"Test creation failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestUpdateView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def patch(self, request, test_id):
#         if not request.user.is_active:
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             test = Test.objects.get(id=test_id, creator=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {test_id} not found for {request.user.email}")
#             return Response({"error": "Test not found or not owned"}, status=status.HTTP_404_NOT_FOUND)
        
#         # Prevent editing if test started
#         if test.schedule_start <= timezone.now():
#             logger.warning(f"Attempt to edit started test {test_id} by {request.user.email}")
#             return Response({"error": "Cannot edit test that has started"}, status=status.HTTP_400_BAD_REQUEST)
        
#         serializer = TestSerializer(test, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             send_test_notification_task.delay(
#                 test.id, request.user.email, action="updated"
#             )
#             logger.info(f"Test {test.id} updated by {request.user.email}")
#             return Response(serializer.data)
#         logger.warning(f"Test update failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class TestDeleteView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def delete(self, request, test_id):
#         if not request.user.is_active:
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             test = Test.objects.get(id=test_id, creator=request.user)
#         except Test.DoesNotExist:
#             logger.warning(f"Test {test_id} not found for {request.user.email}")
#             return Response({"error": "Test not found or not owned"}, status=status.HTTP_404_NOT_FOUND)
        
#         # Prevent deletion if test has attempts
#         if test.testattempt_set.exists():
#             logger.warning(f"Attempt to delete test {test_id} with attempts by {request.user.email}")
#             return Response({"error": "Cannot delete test with attempts"}, status=status.HTTP_400_BAD_REQUEST)
        
#         test.delete()
#         send_test_notification_task.delay(
#             test_id, request.user.email, action="deleted"
#         )
#         logger.info(f"Test {test_id} deleted by {request.user.email}")
#         return Response({"message": "Test deleted"}, status=status.HTTP_200_OK)

# class TestListView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request):
#         if not request.user.is_active:
#             return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
#         queryset = Test.objects.filter(creator=request.user).select_related('creator').prefetch_related('subjects')
#         # Filters
#         subject_id = request.query_params.get('subject')
#         active = request.query_params.get('active')
        
#         if subject_id:
#             queryset = queryset.filter(subjects__id=subject_id)
#         if active is not None:
#             now = timezone.now()
#             if bool(active):
#                 queryset = queryset.filter(schedule_start__lte=now, schedule_end__gte=now)
#             else:
#                 queryset = queryset.exclude(schedule_start__lte=now, schedule_end__gte=now)
        
#         # Pagination
#         paginator = Paginator(queryset, 20)
#         page = request.query_params.get('page', 1)
#         try:
#             tests = paginator.page(page)
#         except EmptyPage:
#             return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        
#         serializer = TestSerializer(tests, many=True)
#         logger.info(f"Test list retrieved by {request.user.email}")
#         return Response({
#             "count": paginator.count,
#             "results": serializer.data
#         })