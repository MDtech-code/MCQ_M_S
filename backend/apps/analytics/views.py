from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.common.authentication import CookieTokenAuthentication
from .models import StudentProgress, TestAnalytics, TestAttemptHistory
from .serializers import StudentProgressSerializer, TestAnalyticsSerializer, TestAttemptHistorySerializer
from apps.accounts.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from apps.common.permissions import IsTeacher
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.authentication import SessionAuthentication
from apps.common.throttles import CustomUserRateThrottle
from django.contrib import messages
from django.shortcuts import redirect
from apps.examination.models import Test
import logging


logger = logging.getLogger(__name__)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class StudentProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        if request.user.role != User.Role.STUDENT:
            logger.warning(f"Unauthorized access by {request.user.email} (role: {request.user.role})")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Only students can view progress.")
                return redirect('student_dashboard')
            return Response({"error": "Only students can view progress"}, status=status.HTTP_403_FORBIDDEN)

        progress = StudentProgress.objects.filter(student=request.user)
        progress_serializer = StudentProgressSerializer(progress, many=True)
        
        # Get historical test attempts
        history = TestAttemptHistory.objects.filter(student=request.user).order_by('completed_at')
        history_serializer = TestAttemptHistorySerializer(history, many=True)

        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'progress': progress_serializer.data,
                    'history': history_serializer.data,
                    'user': request.user
                },
                template_name='analytics/student/progress.html'
            )
        return Response({
            'progress': progress_serializer.data,
            'history': history_serializer.data
        })

@method_decorator(ensure_csrf_cookie, name='dispatch')
class TestAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request, test_id):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to view analytics for test {test_id}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('public:teacher_dashboard')
            return Response(
                {"error": "Account not active or verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            analytics = TestAnalytics.objects.get(
                test_id=test_id,
                test__created_by=request.user
            )
        except TestAnalytics.DoesNotExist:
            logger.warning(f"Analytics for test {test_id} not found or not owned by {request.user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Test analytics not found or not owned by you.")
                return redirect('test_list')
            return Response(
                {"error": "Test analytics not found or not owned by you"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TestAnalyticsSerializer(analytics)
        logger.info(f"Analytics for test {test_id} retrieved by {request.user.email}")

        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'analytics': serializer.data,
                    'test': analytics.test,
                    'user': request.user
                },
                template_name='analytics/teacher/test_analytics.html'
            )
        return Response(serializer.data, status=status.HTTP_200_OK)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ClassAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        if not request.user.is_active or not request.user.is_verified:
            logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to view class analytics")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Your account is not active or verified.")
                return redirect('public:teacher_dashboard')
            return Response(
                {"error": "Account not active or verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all tests created by the teacher
        tests = Test.objects.filter(created_by=request.user)
        analytics = TestAnalytics.objects.filter(test__in=tests)
        analytics_serializer = TestAnalyticsSerializer(analytics, many=True)

        # Get student progress for students in teacher's tests
        student_progress = StudentProgress.objects.filter(
            student__attempts__test__in=tests
        ).distinct()
        progress_serializer = StudentProgressSerializer(student_progress, many=True)

        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'analytics': analytics_serializer.data,
                    'progress': progress_serializer.data,
                    'user': request.user
                },
                template_name='analytics/teacher/class_dashboard.html'
            )
        return Response({
            'analytics': analytics_serializer.data,
            'progress': progress_serializer.data
        })
# # apps/analytics/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions
# from apps.common.authentication import CookieTokenAuthentication
# from .models import StudentProgress, TestAnalytics
# from .serializers import StudentProgressSerializer, TestAnalyticsSerializer
# from apps.accounts.models import User
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import ensure_csrf_cookie
# from apps.common.permissions import IsTeacher
# from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
# from rest_framework.authentication import SessionAuthentication
# from apps.common.throttles import CustomUserRateThrottle
# from django.contrib import messages
# from django.shortcuts import redirect
# import logging
# logger = logging.getLogger(__name__)

# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class StudentProgressView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def get(self, request):
#         if request.user.role != User.Role.STUDENT:
#             logger.warning(f"Unauthorized access by {request.user.email} (role: {request.user.role})")
#             return Response({"error": "Only students can view progress"}, status=status.HTTP_403_FORBIDDEN)
#         progress = StudentProgress.objects.filter(student=request.user)
#         serializer = StudentProgressSerializer(progress, many=True)
#         return Response(serializer.data)

# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class TestAnalyticsView(APIView):
#     permission_classes = [permissions.IsAuthenticated, IsTeacher]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     throttle_classes = [CustomUserRateThrottle]

#     def get(self, request, test_id):
#         if not request.user.is_active or not request.user.is_verified:
#             logger.warning(f"Inactive/unverified teacher {request.user.email} attempted to view analytics for test {test_id}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Your account is not active or verified.")
#                 return redirect('public:teacher_dashboard')
#             return Response(
#                 {"error": "Account not active or verified"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             analytics = TestAnalytics.objects.get(
#                 test_id=test_id,
#                 test__created_by=request.user
#             )
#         except TestAnalytics.DoesNotExist:
#             logger.warning(f"Analytics for test {test_id} not found or not owned by {request.user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Test analytics not found or not owned by you.")
#                 return redirect('test_list')
#             return Response(
#                 {"error": "Test analytics not found or not owned by you"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = TestAnalyticsSerializer(analytics)
#         logger.info(f"Analytics for test {test_id} retrieved by {request.user.email}")

#         if request.accepted_renderer.format == 'html':
#             return Response(
#                 {'analytics': serializer.data},
#                 template_name='analytics/teacher/test_analytics.html'
#             )
#         return Response(serializer.data, status=status.HTTP_200_OK)