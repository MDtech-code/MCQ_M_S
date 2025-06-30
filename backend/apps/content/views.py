from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.common.authentication import CookieTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from .models import Subject, Topic, Question
from .serializers import QuestionSerializer
from apps.common.throttles import CustomUserRateThrottle
from apps.common.permissions import IsTeacher
from .tasks import send_question_notification_task, notify_admin_approval_task
from django.core.paginator import Paginator, EmptyPage
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from apps.content.utils.utils import process_question_form_data, get_subject_topic_context
from django.db.models import Prefetch
from django.core.cache import cache
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)



def get_subject_topic_context(user):
    cache_key = f"subject_topic_context:{user.id}"
    context = cache.get(cache_key)
    if not context:
        subjects = Subject.objects.all()
        topics = Topic.objects.select_related('subject').all()
        context = {
            'subjects': list(subjects),
            'topics': list(topics)
        }
        cache.set(cache_key, context, timeout=86400)  # 24 hours
        logger.debug(f"Cached subject_topic_context for user {user.id}")
    else:
        logger.debug(f"Cache hit for subject_topic_context for user {user.id}")

    return context  


class QuestionFilter:
    def __init__(self, queryset, params, user):
        self.queryset = queryset
        self.params = params
        self.user = user

    def apply(self):
        filters = {}
        needs_distinct = False

        if difficulty := self.params.get('difficulty'):
            if difficulty not in ['E', 'M', 'H']:
                raise ValueError("Difficulty must be E, M, or H")
            filters['difficulty'] = difficulty
        
        if subject_id := self.params.get('subject'):
            filters['topics__subject_id'] = subject_id
            needs_distinct = True
        
        if topic_id := self.params.get('topic'):
            if subject_id:
                if not Topic.objects.filter(id=topic_id, subject_id=subject_id).exists():
                    raise ValueError("Topic does not belong to specified subject")
            filters['topics__id'] = topic_id
            needs_distinct = True
        
        if status := self.params.get('status'):
            if self.user.role == 'TE':
                if status not in ['PENDING', 'APPROVED', 'REJECTED']:
                    raise ValueError("Status must be PENDING, APPROVED, or REJECTED")
                filters['approval__status'] = status
        
        if created_after := self.params.get('created_after'):
            try:
                datetime.strptime(created_after, '%Y-%m-%d')
                filters['created_at__gte'] = created_after
            except ValueError:
                raise ValueError("Invalid date format for created_after")
        
        queryset = self.queryset.filter(**filters)
        return queryset.distinct() if needs_distinct else queryset

@method_decorator(ensure_csrf_cookie, name='dispatch')
class QuestionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        if not request.user.is_active:
            logger.warning(f"Inactive user {request.user.email} attempted to list questions")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is inactive.")
                return redirect('public:teacher_dashboard')
            return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
        if request.user.role == 'TE':
            queryset = Question.objects.all().select_related('created_by', 'approval').prefetch_related(Prefetch('topics', queryset=Topic.objects.select_related('subject')))
        else:
            logger.warning(f"Invalid role {request.user.role} for {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Invalid role.")
                return redirect('public:teacher_dashboard')
            return Response({"error": "Invalid role"}, status=status.HTTP_403_FORBIDDEN)

        # Apply filters
        try:
            question_filter = QuestionFilter(queryset, request.query_params, request.user)
            queryset = question_filter.apply()
        except ValueError as e:
            logger.warning(f"Invalid filter for {request.user.email}: {str(e)}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, str(e))
                return redirect('question_list')
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Pagination
        paginator = Paginator(queryset, 20)
        page = request.query_params.get('page', 1)
        try:
            questions = paginator.page(page)
        except EmptyPage:
            logger.warning(f"Invalid page {page} for question list by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Page not found.")
                return redirect('question_list')
            return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)

        # Caching
        cache_key = f"question_list:{request.user.id}:{request.user.role}:{hash(str(request.query_params))}:{page}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for {cache_key}")
            if request.accepted_renderer.format == 'html':
                context = get_subject_topic_context(request.user)
                return Response(
                    {
                        'count': cached_data['count'],
                        'results': questions,
                        **context,
                        'current_filters': request.query_params
                    },
                    template_name='content/teacher/question_list.html'
                )
            return Response(cached_data)

        serializer = QuestionSerializer(questions, many=True)
        response_data = {
            "count": paginator.count,
            "results": serializer.data
        }   
        cache.set(cache_key, response_data, timeout=3600)  # 1 hour
        logger.info(f"Question list retrieved by {request.user.email} (role: {request.user.role})")

        if request.accepted_renderer.format == 'html':
            context = get_subject_topic_context(request.user)
            return Response(
                {
                    'count': response_data['count'],
                    'results': questions,
                    **context,
                    'current_filters': request.query_params
                },
                template_name='content/teacher/question_list.html'
            )
        return Response(response_data)
@method_decorator(ensure_csrf_cookie, name='dispatch')
class QuestionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        if request.accepted_renderer.format == 'html':
            context = get_subject_topic_context(request.user)
            initial_form_data = {
                'question_type': 'MCQ',
                'topics': [],
                'question_text': '',
                'difficulty': '',
                'options': {'A': '', 'B': '', 'C': '', 'D': ''},
                'correct_answer': '',
                'metadata': '{}',
            }
            return Response(
                {
                    **context,
                    'form_data': initial_form_data,
                    'is_update': False,
                },
                template_name='content/teacher/question_form.html'
            )
        return Response({"message": "Question creation endpoint (GET)"}, status=status.HTTP_200_OK)

    def post(self, request):
        logger.debug(f"[[[[[[[]]]]]]]Received data]]]]]]]]: {request.data}")
        processed_data = process_question_form_data(request.data) if request.accepted_renderer.format == 'html' else request.data

        logger.debug(f"Processed data passed to serializer: {processed_data}")

        serializer = QuestionSerializer(data=processed_data, context={'request': request})
        if serializer.is_valid():
            question = serializer.save()
            send_question_notification_task.delay(question.id, request.user.email, action="created")
            if question.approval.flagged_by_system:
                notify_admin_approval_task.delay(question.id, question.approval.flag_reason)
            logger.info(f"Question {question.id} created by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Question created successfully.")
                return redirect('question_list')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"Question creation failed for {request.user.email}: {serializer.errors}")
        if request.accepted_renderer.format == 'html':
            context = get_subject_topic_context(request.user)
            return Response(
                {
                    'errors': serializer.errors,
                    'form_data': request.data,
                    **context,
                    'is_update': False,
                },
                template_name='content/teacher/question_form.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@method_decorator(ensure_csrf_cookie, name='dispatch')
class QuestionUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request, pk):
        question = get_object_or_404(Question.objects.select_related('created_by', 'approval').prefetch_related('topics'), pk=pk, created_by=request.user)
        if request.accepted_renderer.format == 'html':
            context = get_subject_topic_context(request.user)
            serializer = QuestionSerializer(question)
            initial_form_data = {
                'question_type': serializer.data['question_type'],
                'topics': [str(topic_id) for topic_id in serializer.data['topics']],
                'question_text': serializer.data['question_text'],
                'difficulty': serializer.data['difficulty'],
                'options': serializer.data['options'],
                'correct_answer': serializer.data['correct_answer'],
                'metadata': json.dumps(serializer.data['metadata']) if serializer.data['metadata'] else '{}',
            }
            return Response(
                {
                    **context,
                    'form_data': initial_form_data,
                    'question': question,
                    'is_update': True,
                },
                template_name='content/teacher/question_form.html'
            )
        return Response(QuestionSerializer(question).data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        question = get_object_or_404(Question.objects.select_related('created_by', 'approval').prefetch_related('topics'), pk=pk, created_by=request.user)
        processed_data = process_question_form_data(request.data) if request.accepted_renderer.format == 'html' else request.data
        logger.debug(f"Processed data passed to serializer: {processed_data}")
        serializer = QuestionSerializer(instance=question, data=processed_data, context={'request': request})
        if serializer.is_valid():
            question = serializer.save()
            send_question_notification_task.delay(question.id, request.user.email, action="updated")
            if question.approval.flagged_by_system:
                notify_admin_approval_task.delay(question.id, question.approval.flag_reason)
            logger.info(f"Question {question.id} updated by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Question updated successfully.")
                return redirect('question_list')
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        logger.warning(f"Question update failed for {request.user.email}: {serializer.errors}")
        if request.accepted_renderer.format == 'html':
            context = get_subject_topic_context(request.user)
            return Response(
                {
                    'errors': serializer.errors,
                    'form_data': processed_data,
                    **context,
                    'question': question,
                    'is_update': True,
                },
                template_name='content/teacher/question_form.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class QuestionDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def post(self, request, pk):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to delete question {pk}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('public:teacher_dashboard')
            return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)

        try:
            question = Question.objects.select_related('created_by', 'approval').get(pk=pk, created_by=request.user)
        except Question.DoesNotExist:
            logger.warning(f"Question {pk} not found or not owned by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Question not found or not owned by you.")
                return redirect('question_list')
            return Response({"error": "Question not found or not owned by you"}, status=status.HTTP_404_NOT_FOUND)

        if question.approval.status == 'APPROVED':
            logger.warning(f"Attempt to delete approved question {pk} by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Cannot delete approved questions.")
                return redirect('question_list')
            return Response({"error": "Cannot delete approved questions"}, status=status.HTTP_403_FORBIDDEN)

        question.delete()
        send_question_notification_task.delay(pk, request.user.email, action="deleted")
        logger.info(f"Question {pk} deleted by {request.user.email}")
        if request.accepted_renderer.format == 'html':
            messages.success(request, "Question deleted successfully.")
            return redirect('question_list')
        return Response(status=status.HTTP_204_NO_CONTENT)
