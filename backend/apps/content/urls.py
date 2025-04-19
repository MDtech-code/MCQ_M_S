from django.urls import path
from .views import (
    
    QuestionCreateView,QuestionListView,QuestionDeleteView,QuestionUpdateView
)
#SubjectCreateView, SubjectListView, TopicCreateView, TopicListView,
urlpatterns = [
    
    path('questions/', QuestionListView.as_view(), name='question_list'),
    path('questions/create/', QuestionCreateView.as_view(), name='question_create'),
    path('questions/<int:pk>/update/', QuestionUpdateView.as_view(), name='question_update'),
    path('questions/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    
]