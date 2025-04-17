import logging
from django.contrib.auth import authenticate, login, logout
from django.forms import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, UserLoginSerializer,StudentProfileSerializer,TeacherProfileSerializer,ForgotPasswordSerializer,ResetPasswordSerializer,ChangePasswordSerializer,DeleteAccountSerializer,UpdateEmailSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from apps.accounts.signals import user_signed_up
from .models import EmailVerificationToken,PasswordResetToken,User,StudentProfile
from .tasks import send_verification_email_task,send_password_reset_email_task,send_deletion_confirmation_email_task
from django.contrib.auth import password_validation



# Get a logger for this module.
logger = logging.getLogger(__name__)

class SignupView(APIView):
    """
    API endpoint for user registration.
    """
    permission_classes = [AllowAny]
    def post(self, request):
        logger.info("Signup request received with data: %s", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
            user_signed_up.send(sender=self.__class__, user=user)
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
    authentication_classes=[]
    permission_classes=[AllowAny]
    def post(self, request):
        logger.info("Login attempt for username: %s", request.data.get('username'))
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Get or create a token for the user
                token, created = Token.objects.get_or_create(user=user)
                logger.info("User '%s' logged in successfully.", username)
                return Response(
                    {"message": "Login successful.",
                      "token": token.key,
                    "user_id": user.pk, 
                    "email": user.email, 
                    "role": user.role},
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
    API endpoint for user logout (Token Authentication).
    Deletes the user's authentication token from the server.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        username = request.user.username # User is guaranteed to be authenticated here
        try:
            # Simply delete the token associated with the request
            # request.auth is the token object instance used for authentication
            if request.auth:
                request.auth.delete()
                logger.info("Token for user '%s' deleted successfully.", username)
            else:
                 # This case should ideally not happen if TokenAuthentication is enforced
                 logger.warning("No token found for authenticated user '%s' during logout.", username)

            # logout(request) # <-- REMOVE THIS - Not needed for token auth

            return Response(
                {"message": "Logout successful. Token invalidated."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error("Error during logout for user '%s': %s", username, str(e))
            return Response(
                {"error": "An error occurred during logout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        






class VerifyEmailView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
    
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            logger.warning("No token provided for email verification")
            return Response(
                {"error": "Token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token_obj = EmailVerificationToken.objects.get(token=token)
            if not token_obj.is_valid():
                logger.warning(f"Expired token {token} for {token_obj.user.email}")
                return Response(
                    {"error": "Token has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user = token_obj.user
            if user.is_verified:
                logger.info(f"Email already verified for {user.email}")
                return Response(
                    {"message": "Email already verified"},
                    status=status.HTTP_200_OK
                )
            user.is_verified = True
            user.save()
            token_obj.delete()  # One-time use
            logger.info(f"Email verified for {user.email}")
            return Response(
                {"message": "Email verified successfully"},
                status=status.HTTP_200_OK
            )
        except EmailVerificationToken.DoesNotExist:
            logger.warning(f"Invalid token {token}")
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        



class ResendVerificationEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[TokenAuthentication]

    def post(self, request):
        user = request.user
        if user.is_verified:
            logger.info(f"User {user.email} already verified, resend rejected")
            return Response(
                {"message": "Email already verified"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Delete old tokens
        EmailVerificationToken.objects.filter(user=user).delete()
        # Create new token
        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email_task.delay(user.id, token.token)
        logger.info(f"Resent verification email for {user.email}")
        return Response(
            {"message": "Verification email sent"},
            status=status.HTTP_200_OK
        )
    
# apps/accounts/views.py


class ForgotPasswordView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                PasswordResetToken.objects.filter(user=user).delete()
                token = PasswordResetToken.objects.create(user=user)
                send_password_reset_email_task.delay(user.id, token.token)
                logger.info(f"Password reset email triggered for {email}")
            except User.DoesNotExist:
                pass  # Silent to avoid leaking
            return Response({"message": "Password reset email sent"})
        logger.warning(f"Forgot password failed: {serializer.errors}")
        return Response(serializer.errors, status=400)
    
    



# apps/accounts/views.py




class ResetPasswordView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
  

    def post(self, request):
        # Extract token from query params
        token = request.query_params.get('token')
        if not token:
            logger.warning("No token provided in query parameters")
            return Response(
                {"error": "Token is required in query parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Combine token with POST data
        data = {
            'token': token,
            'password': request.data.get('password'),
            'password2': request.data.get('password2')
        }

        serializer = ResetPasswordSerializer(data=data)
        if serializer.is_valid():
            try:
                token_obj = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
                user = token_obj.user
                user.set_password(serializer.validated_data['password'])
                user.save()
                token_obj.delete()  # One-time use
                logger.info(f"Password reset for {user.email}")
                # Delete DRF auth token to log out user
                if request.auth:
                    request.auth.delete()
                    logger.info(f"Auth token deleted for user {user.email}")
                else:
                    logger.warning(f"No auth token found for user {user.email}")
                return Response(
                    {"message": "Password reset successfully"},
                    status=status.HTTP_200_OK
                )
            except PasswordResetToken.DoesNotExist:
                logger.warning(f"Invalid reset token {serializer.validated_data['token']}")
                return Response(
                    {"error": "Invalid token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        logger.warning(f"Reset password failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            # Optional: Delete auth token to force re-login
            if request.auth:
                request.auth.delete()
                logger.info(f"Auth token deleted for {user.email} after password change")
            logger.info(f"Password changed for {user.email}")
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        logger.warning(f"Change password failed for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# apps/accounts/views.py
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            email = user.email  # Store for email task
            role = user.role

            if role == User.Role.STUDENT:
                # Hard delete for students
                try:
                    # Delete related data (adjust based on your models)
                    StudentProfile.objects.filter(user=user).delete()
                    # Example: Delete test attempts
                    # TestAttempt.objects.filter(user=user).delete()
                    user.delete()  # Deletes User and cascades to related models
                    logger.info(f"Hard deletion completed for student {email}")
                    # Send confirmation email
                    send_deletion_confirmation_email_task.delay(email, role=User.Role.STUDENT)
                    return Response(
                        {"message": "Student account deleted permanently"},
                        status=status.HTTP_200_OK
                    )
                except Exception as e:
                    logger.error(f"Hard deletion failed for {email}: {str(e)}")
                    return Response(
                        {"error": "Failed to delete account"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:  # TEACHER or ADMIN
                # Soft delete for teachers (and admins, if applicable)
                user.is_active = False
                user.save()
                logger.info(f"Soft deletion completed for {role} {email}")
                # Send confirmation email
                send_deletion_confirmation_email_task.delay(email, role=role)
                # Delete auth token
                if request.auth:
                    request.auth.delete()
                    logger.info(f"Auth token deleted for {email}")
                return Response(
                    {"message": f"{role} account deactivated successfully"},
                    status=status.HTTP_200_OK
                )
        logger.warning(f"Account deletion failed for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# apps/accounts/views.py

class UpdateEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = UpdateEmailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            new_email = serializer.validated_data['new_email']
            user.email = new_email
            user.is_verified = False  # Require re-verification
            user.save()
            # Send verification email
            EmailVerificationToken.objects.filter(user=user).delete()
            token = EmailVerificationToken.objects.create(user=user)
            send_verification_email_task.delay(user.id, token.token)
            logger.info(f"Email updated to {new_email}, verification email sent")
            return Response({"message": "Email updated, please verify new email"}, status=status.HTTP_200_OK)
        logger.warning(f"Email update failed for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[TokenAuthentication]

    def get(self, request):
        user = request.user
        profile = user.get_profile()
        if not profile:
            logger.warning(f"No profile found for {user.email}")
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = (
            StudentProfileSerializer(profile)
            if user.role == User.Role.STUDENT
            else TeacherProfileSerializer(profile)
        )
        logger.info(f"Retrieved profile for {user.email}")
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        profile = user.get_profile()
        if not profile:
            logger.warning(f"No profile found for {user.email}")
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = (
            StudentProfileSerializer(profile, data=request.data, partial=True)
            if user.role == User.Role.STUDENT
            else TeacherProfileSerializer(profile, data=request.data, partial=True)
        )
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Updated profile for {user.email}")
            return Response(serializer.data)
        logger.warning(f"Profile update failed for {user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


