from django.urls import path
from .views import StudentProgressView, TestAnalyticsView, ClassAnalyticsView

urlpatterns = [
    path('progress/', StudentProgressView.as_view(), name='student-progress'),
    path('test/<int:test_id>/', TestAnalyticsView.as_view(), name='test_analytics'),
    path('class/', ClassAnalyticsView.as_view(), name='class_analytics'),
]