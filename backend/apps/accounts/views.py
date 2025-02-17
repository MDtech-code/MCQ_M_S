import logging
from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSignupSerializer, UserLoginSerializer
from rest_framework.permissions import AllowAny

# Get a logger for this module.
logger = logging.getLogger(__name__)

class SignupView(APIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [AllowAny]
    def post(self, request):
        logger.info("Signup request received with data: %s", request.data)
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
            return Response(
                {"message": "User created successfully."},
                status=status.HTTP_201_CREATED
            )
        else:
            logger.warning("User signup failed with errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    API endpoint for user login.
    """
    def post(self, request):
        logger.info("Login attempt for username: %s", request.data.get('username'))
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info("User '%s' logged in successfully.", username)
                return Response(
                    {"message": "Login successful."},
                    status=status.HTTP_200_OK
                )
            else:
                logger.warning("Invalid credentials for username: %s", username)
                return Response(
                    {"error": "Invalid credentials."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        else:
            logger.warning("Login serializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """
    API endpoint for user logout.
    """
    def post(self, request):
        username = request.user.username if request.user.is_authenticated else "Anonymous"
        logout(request)
        logger.info("User '%s' logged out successfully.", username)
        return Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK
        )
