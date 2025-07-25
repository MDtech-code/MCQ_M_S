from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from apps.accounts.models import User, ApprovalRequest
from apps.accounts.serializers import UserSerializer, ApprovalRequestSerializer
# from apps.accounts.signals import user_signed_up
from apps.accounts.tasks import send_approval_request_notification
from apps.notifications.models import Notification
import logging

logger = logging.getLogger(__name__)




@method_decorator(ensure_csrf_cookie, name='dispatch')
class NotificationsView(APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter notifications based on user role
        notification_filter = {}
        if request.user.role == User.Role.STUDENT:
            notification_filter['notification_type__in'] = ['STUDENT_TEST', 'GENERAL']
        elif request.user.role == User.Role.TEACHER:
            notification_filter['notification_type__in'] = ['TEACHER_APPROVAL', 'GENERAL']

        notifications = Notification.objects.filter(
            user=request.user, **notification_filter
        ).order_by('-created_at')[:10]
        unread_count = Notification.objects.filter(
            user=request.user, is_read=False, **notification_filter
        ).count()

        return Response(
            {
                'notifications': [
                    {
                        'id': n.id,
                        'message': n.message,
                        'notification_type': n.notification_type,
                        'is_read': n.is_read,
                        'created_at': n.created_at
                    }
                    for n in notifications
                ],
                'unread_count': unread_count,
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        notification_ids = request.data.get('notification_ids', [])
        if notification_ids:
            Notification.objects.filter(
                user=request.user, id__in=notification_ids
            ).update(is_read=True)
            logger.info(f"Marked notifications as read for user {request.user.username}: {notification_ids}")
        return Response({"message": "Notifications marked as read."}, status=status.HTTP_200_OK)