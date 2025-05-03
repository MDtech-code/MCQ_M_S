from django.urls import path
from .views import CSRFTokenView

urlpatterns = [
    path('get-csrf/', CSRFTokenView.as_view(), name='csrf-token'),
]