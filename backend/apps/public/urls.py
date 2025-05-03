# apps/public/urls.py
from django.urls import path
from .views import PublicHomeView, StudentHomeView, TeacherHomeView,AboutView,ContactView,TeacherDashboardView,StudentDashboardView
from . import views
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


# @login_required
# def dashboard_redirect(request):
#     if request.user.role == 'TEACHER':
#         return redirect('teacher_dashboard')
#     elif request.user.role == 'STUDENT':
#         return redirect('student_dashboard')
#     return redirect('admin:index')


urlpatterns = [
    path('', PublicHomeView.as_view(), name='home'),
    # path('dashboard/', dashboard_redirect, name='dashboard'),
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('settings/',views.settings_dashboard,name='settings_dashboard'),
    
    path('about/', AboutView.as_view(), name='about'),  # Add later
    path('contact/', ContactView.as_view(), name='contact'),  # Add later
]