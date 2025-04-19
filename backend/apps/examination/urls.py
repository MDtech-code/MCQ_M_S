from django.urls import path
from .views import TestCreateView, TestListView, TestUpdateView, TestDeleteView, TestListView, TestAttemptView, StudentResponseView

urlpatterns = [
    path('tests/', TestListView.as_view(), name='test_list'),
    path('tests/create/', TestCreateView.as_view(), name='test_create'),
    path('tests/<int:pk>/update/', TestUpdateView.as_view(), name='test_update'),
    path('tests/<int:pk>/delete/', TestDeleteView.as_view(), name='test_delete'),

    path('attempts/', TestAttemptView.as_view(), name='attempt-list'),
    path('attempts/<int:pk>/', TestAttemptView.as_view(), name='attempt-detail'),
    path('responses/', StudentResponseView.as_view(), name='response-create'),
]