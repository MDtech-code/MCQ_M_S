from django.urls import path
from .views import MCQGenerationView,MCQMLGenerationView

urlpatterns = [
    path('generate-mcq/', MCQGenerationView.as_view(), name='generate_mcq'),
    path('generate/ml/',MCQMLGenerationView.as_view(), name='generate_mcq_ml'),
]