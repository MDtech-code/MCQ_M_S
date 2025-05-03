# from django.shortcuts import render




# # Create your views here.
# def index_view(request):
#     return render(request, "home/home.html")

# def teacher_landing(request):
#     return render(request, "home/landing/teacher_landing.html")

# def student_landing(request):
#     return render(request, "home/landing/student_landing.html")
# def contact_view(request):
#     return render(request, "pages/contact.html")
# def about_view(request):
#     return render(request, "pages/about.html")

# apps/public/views.py
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from apps.accounts.models import User
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.common.authentication import CookieTokenAuthentication
from apps.examination.models import Test, TestAttempt
from apps.common.permissions import IsAdmin,IsStudent,IsTeacher
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

class PublicHomeView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes=[AllowAny]
    authentication_classes=[SessionAuthentication]

    def get(self, request):
        # 1) if logged in, send them to THEIR dashboard
        if request.user.is_authenticated:
            if request.user.role == 'TE':
                return redirect('teacher_dashboard')
            elif request.user.role == 'ST':
                return redirect('student_dashboard')

        # 2) otherwise show the public home page
        return Response(template_name='home/home.html')
    

@method_decorator(ensure_csrf_cookie, name='dispatch')
class TeacherDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        user = request.user
        profile = user.get_profile()
        # Fetch recent tests (last 5 created by the teacher)
        recent_tests = Test.objects.filter(created_by=user).order_by('-created_at')[:5]
        logger.info(f"Rendered teacher dashboard for {user.email}")
        return Response(
            {
                'user': user,
                'profile': profile,
                'recent_tests': recent_tests
            },
            template_name='home/teacher/teacher_dashboard.html'
        )

@method_decorator(ensure_csrf_cookie, name='dispatch')
class StudentDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        user = request.user
        profile = user.get_profile()
        # Fetch available tests (tests not yet completed by the student)
        completed_tests = TestAttempt.objects.filter(student=user).values_list('test_id', flat=True)
        available_tests = Test.objects.exclude(id__in=completed_tests)[:5]
        # Fetch recent results (last 5 attempts)
        recent_results = TestAttempt.objects.filter(student=user)
        logger.info(f"Rendered student dashboard for {user.email}")
        return Response(
            {
                'user': user,
                'profile': profile,
                'available_tests': available_tests,
                'recent_results': recent_results
            },
            template_name='home/student/student_dashboard.html'
        )
    




class AboutView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    permission_classes=[]
    def get(self, request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='pages/about.html')
        return Response({'message': 'Welcome to MCQ Master API'})
    
class ContactView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    permission_classes=[]
    def get(self, request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='pages/contact.html')
        return Response({'message': 'Welcome to MCQ Master API'})
class StudentHomeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]
    def get(self, request):
        if request.user.role != User.Role.STUDENT:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return Response(template_name='student/home.html')

class TeacherHomeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]
    def get(self, request):
        if request.user.role != User.Role.TEACHER:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return Response(template_name='teacher/home.html')
    


# views.py
def settings_dashboard(request, section='profile'):
    template_map = {
        'profile': 'accounts/profile.html',
        'password': 'accounts/change_password.html',
        'email': 'accounts/update_email.html',
        'delete_account': 'accounts/delete_account.html',
    }
    
    context = {
        'active_section': section
    }
    
    return render(request, 'public/settings/settings_base.html', {
        **context,
        'settings_content': template_map.get(section, 'public/settings/settings_profile.html')
    })