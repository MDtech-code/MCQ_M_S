from django.urls import path
from .views import MCQGenerationView

urlpatterns = [
    path('generate-mcq/', MCQGenerationView.as_view(), name='generate_mcq'),
   
]