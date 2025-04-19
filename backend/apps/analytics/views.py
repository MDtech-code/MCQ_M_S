# apps/analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from .models import StudentProgress, TestAnalytics
from .serializers import StudentProgressSerializer, TestAnalyticsSerializer
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)

class StudentProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        if request.user.role != User.Role.STUDENT:
            logger.warning(f"Unauthorized access by {request.user.email} (role: {request.user.role})")
            return Response({"error": "Only students can view progress"}, status=status.HTTP_403_FORBIDDEN)
        progress = StudentProgress.objects.filter(student=request.user)
        serializer = StudentProgressSerializer(progress, many=True)
        return Response(serializer.data)

class TestAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, test_id):
        if request.user.role != User.Role.TEACHER:
            logger.warning(f"Unauthorized access by {request.user.email} (role: {request.user.role})")
            return Response({"error": "Only teachers can view test analytics"}, status=status.HTTP_403_FORBIDDEN)
        try:
            analytics = TestAnalytics.objects.get(test_id=test_id)
            serializer = TestAnalyticsSerializer(analytics)
            return Response(serializer.data)
        except TestAnalytics.DoesNotExist:
            return Response({"error": "Analytics not found"}, status=status.HTTP_404_NOT_FOUND)