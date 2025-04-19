from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from .models import Subject, Topic,Question
from .serializers import  QuestionSerializer
from apps.common.throttles import CustomUserRateThrottle
from apps.accounts.models import User
from .tasks import send_question_notification_task, notify_admin_approval_task
from django.core.paginator import Paginator, EmptyPage
import logging
logger = logging.getLogger(__name__)

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.TEACHER

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.STUDENT




class QuestionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [TokenAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def post(self, request):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to create question")
            return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        



        serializer = QuestionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            question = serializer.save()
            send_question_notification_task.delay(
                question.id, request.user.email, action="created"
            )
            if question.approval.flagged_by_system:
                notify_admin_approval_task.delay(question.id, question.approval.flag_reason)
            logger.info(f"Question {question.id} created by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Question creation failed for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class QuestionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        if not request.user.is_active:
            logger.warning(f"Inactive user {request.user.email} attempted to list questions")
            return Response({"error": "Inactive account"}, status=status.HTTP_403_FORBIDDEN)
        
        # Role-based queryset
        if request.user.role == User.Role.STUDENT:
            queryset = Question.objects.filter(is_active=True).select_related('created_by')
        elif request.user.role == User.Role.TEACHER:
            queryset = Question.objects.filter(created_by=request.user).select_related('created_by')
        else:
            logger.warning(f"Invalid role {request.user.role} for {request.user.email}")
            return Response({"error": "Invalid role"}, status=status.HTTP_403_FORBIDDEN)

        # Filters
        difficulty = request.query_params.get('difficulty')
        subject_id = request.query_params.get('subject')
        topic_id = request.query_params.get('topic')
        status = request.query_params.get('status')  # Teacher only
        created_after = request.query_params.get('created_after')

        if difficulty and difficulty not in ['E', 'M', 'H']:
            logger.warning(f"Invalid difficulty filter: {difficulty}")
            return Response({"error": "Difficulty must be E, M, or H"}, status=status.HTTP_400_BAD_REQUEST)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        if subject_id:
            try:
                Subject.objects.get(id=subject_id)
                queryset = queryset.filter(topics__subject_id=subject_id)
            except Subject.DoesNotExist:
                logger.warning(f"Invalid subject_id: {subject_id}")
                return Response({"error": "Subject not found"}, status=status.HTTP_400_BAD_REQUEST)

        if topic_id:
            try:
                topic = Topic.objects.get(id=topic_id)
                if subject_id and topic.subject_id != int(subject_id):
                    logger.warning(f"Topic {topic_id} does not belong to subject {subject_id}")
                    return Response({"error": "Topic does not belong to specified subject"}, status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(topics__id=topic_id)
            except Topic.DoesNotExist:
                logger.warning(f"Invalid topic_id: {topic_id}")
                return Response({"error": "Topic not found"}, status=status.HTTP_400_BAD_REQUEST)

        if status and request.user.role == User.Role.TEACHER:
            if status not in ['PENDING', 'APPROVED', 'REJECTED']:
                logger.warning(f"Invalid status filter: {status}")
                return Response({"error": "Status must be PENDING, APPROVED, or REJECTED"}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(approval__status=status)

        if created_after:
            try:
                queryset = queryset.filter(created_at__gte=created_after)
            except ValueError:
                logger.warning(f"Invalid created_after: {created_after}")
                return Response({"error": "Invalid date format for created_after"}, status=status.HTTP_400_BAD_REQUEST)

        # Pagination
        paginator = Paginator(queryset.distinct(), 20)
        page = request.query_params.get('page', 1)
        try:
            questions = paginator.page(page)
        except EmptyPage:
            logger.warning(f"Invalid page {page} for question list by {request.user.email}")
            return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = QuestionSerializer(questions, many=True)
        logger.info(f"Question list retrieved by {request.user.email} (role: {request.user.role})")
        return Response({
            "count": paginator.count,
            "results": serializer.data
        })


class QuestionUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [TokenAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def put(self, request, pk):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to update question {pk}")
            return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            question = Question.objects.get(pk=pk, created_by=request.user)
        except Question.DoesNotExist:
            logger.warning(f"Question {pk} not found or not owned by {request.user.email}")
            return Response({"error": "Question not found or not owned by you"}, status=status.HTTP_404_NOT_FOUND)

        serializer = QuestionSerializer(question, data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_question = serializer.save()
            send_question_notification_task.delay(
                updated_question.id, request.user.email, action="updated"
            )
            flag_reason = updated_question.approval.flag_reason if updated_question.approval.flagged_by_system else "Question updated"
            notify_admin_approval_task.delay(updated_question.id, flag_reason)
            logger.info(f"Question {updated_question.id} updated by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.warning(f"Question update failed for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuestionDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [TokenAuthentication]
    throttle_classes = [CustomUserRateThrottle]

    def delete(self, request, pk):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to delete question {pk}")
            return Response({"error": "Account not active or verified"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            question = Question.objects.get(pk=pk, created_by=request.user)
        except Question.DoesNotExist:
            logger.warning(f"Question {pk} not found or not owned by {request.user.email}")
            return Response({"error": "Question not found or not owned by you"}, status=status.HTTP_404_NOT_FOUND)

        if question.approval.status == 'APPROVED':
            logger.warning(f"Attempt to delete approved question {pk} by {request.user.email}")
            return Response({"error": "Cannot delete approved questions"}, status=status.HTTP_403_FORBIDDEN)

        question.delete()  # Cascades to QuestionApproval
        send_question_notification_task.delay(
            pk, request.user.email, action="deleted"
        )
        logger.info(f"Question {pk} deleted by {request.user.email}")
        return Response(status=status.HTTP_204_NO_CONTENT)



