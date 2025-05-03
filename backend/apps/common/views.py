from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class CSRFTokenView(APIView):
    authentication_classes=[]
    permission_classes=[AllowAny]
    def get(self, request):
        return Response({'csrf_token': get_token(request)})