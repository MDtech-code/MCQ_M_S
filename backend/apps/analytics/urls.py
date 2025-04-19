# apps/analytics/urls.py
from django.urls import path
from .views import StudentProgressView, TestAnalyticsView

urlpatterns = [
    path('progress/', StudentProgressView.as_view(), name='student-progress'),
    path('test/<int:test_id>/', TestAnalyticsView.as_view(), name='test-analytics'),
]