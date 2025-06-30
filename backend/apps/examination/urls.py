from django.urls import path
from .views import TestCreateView, TestListView,TestDetailView, TestUpdateView, TestDeleteView, TestListView, TestAttemptView, StudentResponseView,TestResultsView

urlpatterns = [
    path('tests/', TestListView.as_view(), name='test_list'),
    path('tests/<int:pk>/', TestDetailView.as_view(), name='test_detail'),
    path('tests/create/', TestCreateView.as_view(), name='test_create'),
    path('tests/<int:pk>/update/', TestUpdateView.as_view(), name='test_update'),
    path('tests/<int:pk>/delete/', TestDeleteView.as_view(), name='test_delete'),

    path('attempts/', TestAttemptView.as_view(), name='attempt_list'),
    path('attempts/<int:pk>/', TestAttemptView.as_view(), name='attempt_detail'),
    path('responses/', StudentResponseView.as_view(), name='response_create'),

    path('results/test/<int:test_id>/', TestResultsView.as_view(), name='test_results'),
    path('results/test/detail/<int:pk>/', TestResultsView.as_view(), name='test_results_detail'),
]