from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.forms import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from .serializers import UserSerializer, UserLoginSerializer,StudentProfileSerializer,TeacherProfileSerializer,ForgotPasswordSerializer,ResetPasswordSerializer,ChangePasswordSerializer,DeleteAccountSerializer,UpdateEmailSerializer,UserUpdateSerializer,ApprovalRequestSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from apps.common.authentication import CookieTokenAuthentication
from rest_framework.authtoken.models import Token
from apps.accounts.signals import user_signed_up
from .models import EmailVerificationToken,PasswordResetToken,User,StudentProfile,ApprovalRequest
from .tasks import send_verification_email_task,send_password_reset_email_task,send_deletion_confirmation_email_task,send_approval_request_notification
from django.contrib.auth import password_validation
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from django.contrib import messages
from apps.common.permissions import IsTeacher,IsStudent,IsApprovedTeacher,IsAdmin,IsVerifiedTeacher

import logging
logger = logging.getLogger(__name__)







@method_decorator(ensure_csrf_cookie, name='dispatch')
class SignupView(APIView):
    """
    API endpoint for user registration.
    """
    renderer_classes = [JSONRenderer,TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    authentication_classes=[SessionAuthentication]

    def get(self,request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='accounts/auth/signup.html')
        return Response({"message": "Signup endpoint (GET)"}, status=200)

    
    def post(self, request):
        logger.info("Signup request received with data: %s", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("User created successfully: %s (ID: %s)", user.username, user.id)
            user_signed_up.send(sender=self.__class__, user=user)


           
            
            token, _ = Token.objects.get_or_create(user=user)

            
                
            response_data={
                 "user": {
                     "id": user.id,
                     "username": user.username,
                     "email": user.email,
                     'role':user.role
                 },
                 "message": "User created successfully"
             }
             
            if request.accepted_renderer.format == 'html':
                login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
                
                messages.success(request, "User created successfully.")
                response =redirect('home')
            else:
                response =Response(response_data,status=status.HTTP_201_CREATED)        
            response.set_cookie(
                key='auth_token',
                value=token.key,
                httponly=True,
                samesite='Lax',
                max_age=86400
            )
            return response
            
        else:
            logger.warning("Signup validation errors: %s", serializer.errors)
            if request.accepted_renderer.format == 'html':
                return Response(
                    {"errors": serializer.errors, "form_data": request.data},
                    template_name='accounts/auth/signup.html',
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    """
    API endpoint for user login.
    """
    authentication_classes=[SessionAuthentication]
    permission_classes=[AllowAny]
    renderer_classes = [JSONRenderer,TemplateHTMLRenderer]

    def get(self,request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='accounts/auth/login.html')
        return Response({"message": "Login endpoint (GET)"}, status=200)

    def post(self, request):
        logger.info("Login attempt for username: %s", request.data.get('username'))
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                token, _ = Token.objects.get_or_create(user=user)
                logger.info("User '%s' logged in successfully.", username)
                response_data = {
                    "message": "Login successful",
                    "user_id": user.pk,
                    "email": user.email,
                    "role": user.role
                }
                if request.accepted_renderer.format == 'html':
                    login(request, user,backend='apps.accounts.backends.EmailOrUsernameBackend')
                    messages.success(request, "User login successfully.")
                    response=redirect('home')
                else:
                    response = Response(
                        response_data,
                        status=status.HTTP_200_OK
                    )
                if request.data.get('remember'):
                    cookie_max_age=30 * 24 * 3600
                else:
                    cookie_max_age=None
                # Set cookie for all response types
                response.set_cookie(
                    key='auth_token',
                    value=token.key,
                    httponly=True,
                    samesite='Lax',
                    max_age=cookie_max_age
                )
                return response
            else:
                logger.warning("Invalid credentials for username: %s", username)
                error_response = {"errors": {"non_field_errors": ["Invalid credentials"]}}
                if request.accepted_renderer.format == 'html':
                   return Response(
                    {"errors": error_response["errors"], "form_data": request.data},
                    template_name="accounts/auth/login.html",
                    status=status.HTTP_401_UNAUTHORIZED
                )
                return Response(error_response,status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.warning("Login serializer errors: %s", serializer.errors)
            if request.accepted_renderer.format == 'html':
                return Response(
                {"errors": serializer.errors, "form_data": request.data},
                template_name="accounts/auth/login.html",
                status=status.HTTP_400_BAD_REQUEST
            )
            return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LogoutView(APIView):
    """
    API endpoint for user logout (Token Authentication).
    Deletes the user's authentication token from the server.
    """
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer,TemplateHTMLRenderer]

    def post(self, request, *args, **kwargs):
        username = request.user.username
        logger.info("Logout initiated for user '%s'", username)
        try:
            if request.auth:
                request.auth.delete()
                logger.info("Token for user '%s' deleted successfully.", username)
            else:
                 logger.warning("No token found for authenticated user '%s' during logout.", username)

            
            if request.accepted_renderer.format == "html":
                logout(request)
                response=redirect('home')
            else:
                response=Response({'message':'logout successfully'},status=status.HTTP_200_OK)
                
            response.delete_cookie('auth_token')
            response.delete_cookie('csrftoken')
            return response
        except Exception as e:
            logger.error("Error during logout for user '%s': %s", username, str(e))
            if request.accepted_renderer.format == "html":
                return Response(
                    {"error": "An error occurred during logout."},
                    template_name="home/home.html",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response({"error": "An error occurred during logout."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        






# class VerifyEmailView(APIView):
#     permission_classes=[AllowAny]
#     authentication_classes=[]
    
#     def get(self, request):
#         token = request.query_params.get('token')
#         if not token:
#             logger.warning("No token provided for email verification")
#             return Response(
#                 {"error": "Token is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         try:
#             token_obj = EmailVerificationToken.objects.get(token=token)
#             if not token_obj.is_valid():
#                 logger.warning(f"Expired token {token} for {token_obj.user.email}")
#                 return Response(
#                     {"error": "Token has expired"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#             user = token_obj.user
#             if user.is_verified:
#                 logger.info(f"Email already verified for {user.email}")
#                 return Response(
#                     {"message": "Email already verified"},
#                     status=status.HTTP_200_OK
#                 )
#             user.is_verified = True
#             user.save()
#             token_obj.delete()  # One-time use
#             logger.info(f"Email verified for {user.email}")
#             return Response(
#                 {"message": "Email verified successfully"},
#                 status=status.HTTP_200_OK
#             )
#         except EmailVerificationToken.DoesNotExist:
#             logger.warning(f"Invalid token {token}")
#             return Response(
#                 {"error": "Invalid token"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
@method_decorator(ensure_csrf_cookie, name='dispatch')
class VerifyEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication,SessionAuthentication]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request, token):
        try:
            
            token_obj = EmailVerificationToken.objects.get(token=token)
            login(request, request.user,backend='apps.accounts.backends.EmailOrUsernameBackend')
            if not token_obj.is_valid():
                logger.warning(f"Expired token {token} for {token_obj.user.email}")
                if request.accepted_renderer.format == 'html':
                    messages.error(request, "Verification link has expired.")
                    return Response({},template_name='accounts/verify_email.html', status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": "Token has expired"}, status=status.HTTP_400_BAD_REQUEST)
            user = token_obj.user
            originally_verified=user.is_verified
            if token_obj.new_email:
                user.email = token_obj.new_email
                user.is_verified = True
                logger.info(f"Updated email to {user.email} and verified")
            else:
                user.is_verified = True
                logger.info(f"Email verified for {user.email}")

            user.save()
            token_obj.delete()
            if originally_verified and  not token_obj.new_email:
                print('mia triger ho gai')
                logger.info(f"Email already verified for {user.email}")
                if request.accepted_renderer.format == 'html':
                    messages.info(request, "Email already verified.")
                    
                    return redirect('profile')
                return Response({"message": "Email already verified"}, status=status.HTTP_200_OK)
            if request.accepted_renderer.format == 'html':
                print('mia bi ho gia')
                messages.success(request, "Email verified successfully.")
                
                return Response({},template_name='accounts/verify_email.html')
            return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)
        except EmailVerificationToken.DoesNotExist:
            logger.warning(f"Invalid token {token}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Invalid verification link.")
                return Response({},template_name='accounts/verify_email.html', status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


# class ResendVerificationEmailView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes=[CookieTokenAuthentication]

#     def post(self, request):
#         user = request.user
#         if user.is_verified:
#             logger.info(f"User {user.email} already verified, resend rejected")
#             return Response(
#                 {"message": "Email already verified"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         # Delete old tokens
#         EmailVerificationToken.objects.filter(user=user).delete()
#         # Create new token
#         token = EmailVerificationToken.objects.create(user=user)
#         send_verification_email_task.delay(user.id, token.token)
#         logger.info(f"Resent verification email for {user.email}")
#         return Response(
#             {"message": "Verification email sent"},
#             status=status.HTTP_200_OK
#         )
    
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResendVerificationEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def post(self, request):
        user = request.user
        if user.is_verified:
            logger.info(f"User {user.email} already verified, resend rejected")
            if request.accepted_renderer.format == 'html':
                messages.info(request, "Your email is already verified.")
                return redirect('home')
            return Response({"message": "Email already verified"}, status=status.HTTP_400_BAD_REQUEST)
        EmailVerificationToken.objects.filter(user=user).delete()
        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email_task.delay(user.id, token.token)
        logger.info(f"Resent verification email for {user.email}")
        if request.accepted_renderer.format == 'html':
            messages.success(request, "Verification email sent.")
            return redirect('home')
        return Response({"message": "Verification email sent"}, status=status.HTTP_200_OK)
# apps/accounts/views.py


# class ForgotPasswordView(APIView):
#     permission_classes=[AllowAny]
#     authentication_classes=[]
#     def post(self, request):
#         serializer = ForgotPasswordSerializer(data=request.data)
#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             try:
#                 user = User.objects.get(email=email)
#                 PasswordResetToken.objects.filter(user=user).delete()
#                 token = PasswordResetToken.objects.create(user=user)
#                 send_password_reset_email_task.delay(user.id, token.token)
#                 logger.info(f"Password reset email triggered for {email}")
#             except User.DoesNotExist:
#                 pass  # Silent to avoid leaking
#             return Response({"message": "Password reset email sent"})
#         logger.warning(f"Forgot password failed: {serializer.errors}")
#         return Response(serializer.errors, status=400)
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='accounts/password_reset_request.html')
        return Response({"message": "Forgot password endpoint (GET)"}, status=200)

    def post(self, request):
        print(request.data)
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
                pass  # Silent
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Password reset email sent. Check your inbox.")
                return Response(template_name='accounts/password_reset_done.html')
            return Response({"message": "Password reset email sent"}, status=status.HTTP_200_OK)
        logger.warning(f"Forgot password failed: %s", serializer.errors)
        if request.accepted_renderer.format == 'html':
            return Response(
                {"errors": serializer.errors, "form_data": request.data},
                template_name='accounts/password_reset_request.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



# apps/accounts/views.py




# class ResetPasswordView(APIView):
#     permission_classes=[AllowAny]
#     authentication_classes=[]
  

#     def post(self, request):
#         # Extract token from query params
#         token = request.query_params.get('token')
#         if not token:
#             logger.warning("No token provided in query parameters")
#             return Response(
#                 {"error": "Token is required in query parameters"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Combine token with POST data
#         data = {
#             'token': token,
#             'password': request.data.get('password'),
#             'password2': request.data.get('password2')
#         }

#         serializer = ResetPasswordSerializer(data=data)
#         if serializer.is_valid():
#             try:
#                 token_obj = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
#                 user = token_obj.user
#                 user.set_password(serializer.validated_data['password'])
#                 user.save()
#                 token_obj.delete()  # One-time use
#                 logger.info(f"Password reset for {user.email}")
#                 # Delete DRF auth token to log out user
#                 if request.auth:
#                     request.auth.delete()
#                     logger.info(f"Auth token deleted for user {user.email}")
#                 else:
#                     logger.warning(f"No auth token found for user {user.email}")
#                 return Response(
#                     {"message": "Password reset successfully"},
#                     status=status.HTTP_200_OK
#                 )
#             except PasswordResetToken.DoesNotExist:
#                 logger.warning(f"Invalid reset token {serializer.validated_data['token']}")
#                 return Response(
#                     {"error": "Invalid token"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#         logger.warning(f"Reset password failed: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request, token):
        try:
            token_obj = PasswordResetToken.objects.get(token=token)
            if not token_obj.is_valid():
                logger.warning(f"Expired reset token {token}")
                if request.accepted_renderer.format == 'html':
                    messages.error(request, "Password reset link has expired.")
                    return Response(template_name='accounts/password_reset_confirm.html', status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": "Token has expired"}, status=status.HTTP_400_BAD_REQUEST)
            if request.accepted_renderer.format == 'html':
                return Response({'token': token}, template_name='accounts/password_reset_confirm.html')
            return Response({"message": "Valid token"}, status=status.HTTP_200_OK)
        except PasswordResetToken.DoesNotExist:
            logger.warning(f"Invalid reset token {token}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Invalid password reset link.")
                return Response(template_name='accounts/password_reset_confirm.html', status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, token):
        data = {
            'token': token,
            'password': request.data.get('password'),
            'password2': request.data.get('password2')
        }
        serializer = ResetPasswordSerializer(data=data)
        if serializer.is_valid():
            try:
                token_obj = PasswordResetToken.objects.get(token=token)
                user = token_obj.user
                print(token_obj,user)
                user.set_password(serializer.validated_data['password'])
                user.save()
                token_obj.delete()
                logger.info(f"Password reset for {user.email}")
                if request.auth:
                    request.auth.delete()
                    logger.info(f"Auth token deleted for user {user.email}")
                if request.accepted_renderer.format == 'html':
                    messages.success(request, "Password reset successfully.")
                    return Response(template_name='accounts/password_reset_complete.html')
                return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
            except PasswordResetToken.DoesNotExist:
                logger.warning(f"Invalid reset token {token}")
                if request.accepted_renderer.format == 'html':
                    messages.error(request, "Invalid password reset link.")
                    return Response(template_name='accounts/password_reset_confirm.html', status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"Reset password failed: %s", serializer.errors)
        if request.accepted_renderer.format == 'html':
            return Response(
                {"errors": serializer.errors, "form_data": request.data, 'token': token},
                template_name='accounts/password_reset_confirm.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# class ChangePasswordView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def post(self, request):
#         serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             user = request.user
#             user.set_password(serializer.validated_data['new_password'])
#             user.save()
#             # Optional: Delete auth token to force re-login
#             if request.auth:
#                 request.auth.delete()
#                 logger.info(f"Auth token deleted for {user.email} after password change")
#             logger.info(f"Password changed for {user.email}")
#             return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
#         logger.warning(f"Change password failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='accounts/change_password.html')
        return Response({"message": "Change password endpoint (GET)"}, status=200)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            if request.auth:
                request.auth.delete()
                logger.info(f"Auth token deleted for {user.email} after password change")
            logger.info(f"Password changed for {user.email}")
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Password changed successfully. Please log in again.")
                return redirect('login')
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        logger.warning(f"Change password failed for {request.user.email}: %s", serializer.errors)
        if request.accepted_renderer.format == 'html':
            return Response(
                {"errors": serializer.errors, "form_data": request.data},
                template_name='accounts/change_password.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# apps/accounts/views.py
# class DeleteAccountView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def post(self, request):
#         serializer = DeleteAccountSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             user = request.user
#             email = user.email  # Store for email task
#             role = user.role

#             if role == User.Role.STUDENT:
#                 # Hard delete for students
#                 try:
#                     # Delete related data (adjust based on your models)
#                     StudentProfile.objects.filter(user=user).delete()
#                     # Example: Delete test attempts
#                     # TestAttempt.objects.filter(user=user).delete()
#                     user.delete()  # Deletes User and cascades to related models
#                     logger.info(f"Hard deletion completed for student {email}")
#                     # Send confirmation email
#                     send_deletion_confirmation_email_task.delay(email, role=User.Role.STUDENT)
#                     return Response(
#                         {"message": "Student account deleted permanently"},
#                         status=status.HTTP_200_OK
#                     )
#                 except Exception as e:
#                     logger.error(f"Hard deletion failed for {email}: {str(e)}")
#                     return Response(
#                         {"error": "Failed to delete account"},
#                         status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                     )
#             else:  # TEACHER or ADMIN
#                 # Soft delete for teachers (and admins, if applicable)
#                 user.is_active = False
#                 user.save()
#                 logger.info(f"Soft deletion completed for {role} {email}")
#                 # Send confirmation email
#                 send_deletion_confirmation_email_task.delay(email, role=role)
#                 # Delete auth token
#                 if request.auth:
#                     request.auth.delete()
#                     logger.info(f"Auth token deleted for {email}")
#                 return Response(
#                     {"message": f"{role} account deactivated successfully"},
#                     status=status.HTTP_200_OK
#                 )
#         logger.warning(f"Account deletion failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated, ]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='accounts/delete_account.html')
        return Response({"message": "Delete account endpoint (GET)"}, status=200)

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            email = user.email
            role = user.role
            if role == User.Role.STUDENT:
                try:
                    StudentProfile.objects.filter(user=user).delete()
                    user.delete()
                    logger.info(f"Hard deletion completed for student {email}")
                    send_deletion_confirmation_email_task.delay(email, role)
                    if request.accepted_renderer.format == 'html':
                        messages.success(request, "Account deleted permanently.")
                        return redirect('home')
                    return Response({"message": "Student account deleted permanently"}, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"Hard deletion failed for {email}: %s", str(e))
                    if request.accepted_renderer.format == 'html':
                        messages.error(request, "Failed to delete account.")
                        return Response(template_name='accounts/delete_account.html', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    return Response({"error": "Failed to delete account"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                user.is_active = False
                user.save()
                logger.info(f"Soft deletion completed for {role} {email}")
                send_deletion_confirmation_email_task.delay(email, role)
                if request.auth:
                    request.auth.delete()
                    logger.info(f"Auth token deleted for {email}")
                if request.accepted_renderer.format == 'html':
                    messages.success(request, f"{role} account deactivated successfully.")
                    return redirect('home')
                return Response({"message": f"{role} account deactivated successfully"}, status=status.HTTP_200_OK)
        logger.warning(f"Account deletion failed for {request.user.email}: %s", serializer.errors)
        if request.accepted_renderer.format == 'html':
            return Response(
                {"errors": serializer.errors, "form_data": request.data},
                template_name='accounts/delete_account.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# apps/accounts/views.py

# class UpdateEmailView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication]

#     def post(self, request):
#         serializer = UpdateEmailSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             user = request.user
#             new_email = serializer.validated_data['new_email']
#             user.email = new_email
#             user.is_verified = False  # Require re-verification
#             user.save()
#             # Send verification email
#             EmailVerificationToken.objects.filter(user=user).delete()
#             token = EmailVerificationToken.objects.create(user=user)
#             send_verification_email_task.delay(user.id, token.token)
#             logger.info(f"Email updated to {new_email}, verification email sent")
#             return Response({"message": "Email updated, please verify new email"}, status=status.HTTP_200_OK)
#         logger.warning(f"Email update failed for {request.user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UpdateEmailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request):
        if request.accepted_renderer.format == 'html':
            return Response(template_name='accounts/update_email.html')
        return Response({"message": "Update email endpoint (GET)"}, status=200)

    def post(self, request):
        serializer = UpdateEmailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            new_email = serializer.validated_data['new_email']
            EmailVerificationToken.objects.filter(user=user).delete()
            token = EmailVerificationToken.objects.create(user=user, new_email=new_email)

            send_verification_email_task.delay(user.id, token.token, new_email=new_email)
            logger.info(f"Verification email sent to {new_email}")
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Verification email sent to your new email.")
                return redirect('profile')
            return Response({"message": "Verification email sent to your new email"}, status=status.HTTP_200_OK)
        logger.warning(f"Email update failed for {request.user.email}: %s", serializer.errors)
        if request.accepted_renderer.format == 'html':
            return Response(
                {"errors": serializer.errors, "form_data": request.data},
                template_name='accounts/update_email.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# class ProfileUpdateView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes=[CookieTokenAuthentication]

#     def get(self, request):
#         user = request.user
#         profile = user.get_profile()
#         if not profile:
#             logger.warning(f"No profile found for {user.email}")
#             return Response(
#                 {"error": "Profile not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         serializer = (
#             StudentProfileSerializer(profile)
#             if user.role == User.Role.STUDENT
#             else TeacherProfileSerializer(profile)
#         )
#         logger.info(f"Retrieved profile for {user.email}")
#         return Response(serializer.data)

#     def patch(self, request):
#         user = request.user
#         profile = user.get_profile()
#         if not profile:
#             logger.warning(f"No profile found for {user.email}")
#             return Response(
#                 {"error": "Profile not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         serializer = (
#             StudentProfileSerializer(profile, data=request.data, partial=True)
#             if user.role == User.Role.STUDENT
#             else TeacherProfileSerializer(profile, data=request.data, partial=True)
#         )
#         if serializer.is_valid():
#             serializer.save()
#             logger.info(f"Updated profile for {user.email}")
#             return Response(serializer.data)
#         logger.warning(f"Profile update failed for {user.email}: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class ProfileView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

#     def get(self, request):
#         user = request.user
#         profile = user.get_profile()
#         if not profile:
#             logger.warning(f"No profile found for {user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Profile not found.")
#                 return redirect('profile')
#             return Response(
#                 {"error": "Profile not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = (
#             StudentProfileSerializer(profile)
#             if user.role == User.Role.STUDENT
#             else TeacherProfileSerializer(profile)
#         )

#         if request.accepted_renderer.format == 'html':
#             return Response(
#                 {
#                     'user': user,
#                     'profile': profile,
#                     'profile_data': serializer.data,
#                     'is_update': False  # Flag to indicate view mode
#                 },
#                 template_name='account/teacher/profile.html'
#             )
#         logger.info(f"Retrieved profile for {user.email}")
#         return Response(serializer.data)
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class ProfileUpdateView(APIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

#     def get(self, request):
#         user = request.user
#         profile = user.get_profile()
#         if not profile:
#             logger.warning(f"No profile found for {user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Profile not found.")
#                 return redirect('dashboard')  # Redirect to appropriate dashboard
#             return Response(
#                 {"error": "Profile not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = (
#             StudentProfileSerializer(profile)
#             if user.role == User.Role.STUDENT
#             else TeacherProfileSerializer(profile)
#         )

#         if request.accepted_renderer.format == 'html':
#             return Response(
#                 {
#                     'user': user,
#                     'profile': profile,
#                     'form_data': serializer.data,
#                     'is_update': True  # Flag to indicate update mode
#                 },
#                 template_name='account/teacher/profile.html'
#             )
#         logger.info(f"Retrieved profile for {user.email}")
#         return Response(serializer.data)

#     def post(self, request):  # Using POST for HTML form submission
#         user = request.user
#         profile = user.get_profile()
#         if not profile:
#             logger.warning(f"No profile found for {user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.error(request, "Profile not found.")
#                 return redirect('dashboard')
#             return Response(
#                 {"error": "Profile not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # Build Python dict for HTML form data
#         if request.accepted_renderer.format == 'html':
#             raw = request.POST
#             python_data = {
#                 'phone_number': raw.get('phone_number', '').strip(),
#                 'date_of_birth': raw.get('date_of_birth', '').strip() or None,
#                 'gender': raw.get('gender', '').strip() or None,
#             }
#             if user.role == User.Role.STUDENT:
#                 python_data.update({
#                     'grade_level': raw.get('grade_level', '').strip() or None,
#                     'parent_email': raw.get('parent_email', '').strip() or None,
#                 })
#             else:
#                 python_data.update({
#                     'department': raw.get('department', '').strip() or None,
#                     'office_number': raw.get('office_number', '').strip() or None,
#                     'qualifications': raw.get('qualifications', '').strip() or None,
#                 })
#             # Handle avatar file
#             if 'avatar' in request.FILES:
#                 python_data['avatar'] = request.FILES['avatar']
#         else:
#             python_data = request.data  # JSON API: Already a dict

#         serializer = (
#             StudentProfileSerializer(profile, data=python_data, partial=True)
#             if user.role == User.Role.STUDENT
#             else TeacherProfileSerializer(profile, data=python_data, partial=True)
#         )

#         if serializer.is_valid():
#             serializer.save()
#             logger.info(f"Updated profile for {user.email}")
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Profile updated successfully.")
#                 return redirect('profile_view')  # Redirect to profile view
#             return Response(serializer.data)

#         logger.warning(f"Profile update failed for {user.email}: {serializer.errors}")
#         if request.accepted_renderer.format == 'html':
#             return Response(
#                 {
#                     'user': user,
#                     'profile': profile,
#                     'form_data': python_data,
#                     'errors': serializer.errors,
#                     'is_update': True
#                 },
#                 template_name='account/teacher/profile.html',
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request):
        user = request.user
        profile = user.get_profile()
        if not profile:
            logger.warning(f"No profile found for {user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Profile not found.")
                return redirect('home')
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = (
            StudentProfileSerializer(profile) if user.role == User.Role.STUDENT
            else TeacherProfileSerializer(profile)
        )
        user_serializer = UserUpdateSerializer(user)
        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'user': user,
                    'profile': profile,
                    'user_data': user_serializer.data,
                    'profile_data': serializer.data,
                    'is_update': False
                },
                template_name='accounts/profile.html'
            )
        logger.info(f"Retrieved profile for {user.email}")
        return Response({
            'user': user_serializer.data,
            'profile': serializer.data
        })

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated,IsVerifiedTeacher,IsApprovedTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request):
        user = request.user
        profile = user.get_profile()
        if not profile:
            logger.warning(f"No profile found for {user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Profile not found.")
                return redirect('home')
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = (
            StudentProfileSerializer(profile) if user.role == User.Role.STUDENT
            else TeacherProfileSerializer(profile)
        )
        user_serializer = UserUpdateSerializer(user)
        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'user': user,
                    'profile': profile,
                    'user_data': user_serializer.data,
                    'profile_data': serializer.data,
                    'is_update': True
                },
                template_name='accounts/profile.html'
            )
        logger.info(f"Retrieved profile for update for {user.email}")
        return Response({
            'user': user_serializer.data,
            'profile': serializer.data
        })

    def post(self, request):
        user = request.user
        profile = user.get_profile()
        if not profile:
            logger.warning(f"No profile found for {user.email}")
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Profile not found.")
                return redirect('home')
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        if request.accepted_renderer.format == 'html':
            raw = request.POST
            user_data = {}
            if raw.get('first_name') or raw.get('last_name'):
                user_data = {
                    'first_name': raw.get('first_name', '').strip() or None,
                    'last_name': raw.get('last_name', '').strip() or None,
                }
            profile_data = {
                'phone_number': raw.get('phone_number', '').strip() or None,
                'date_of_birth': raw.get('date_of_birth', '').strip() or None,
                'gender': raw.get('gender', '').strip() or None,
            }
            if user.role == User.Role.STUDENT:
                profile_data.update({
                    'grade_level': raw.get('grade_level', '').strip() or None,
                    'parent_email': raw.get('parent_email', '').strip() or None,
                })
            else:
                profile_data.update({
                    'department': raw.get('department', '').strip() or None,
                    'office_number': raw.get('office_number', '').strip() or None,
                    'qualifications': raw.get('qualifications', '').strip() or None,
                })
            if 'avatar' in request.FILES:
                profile_data['avatar'] = request.FILES['avatar']
        else:
            user_data = request.data.get('user', {})
            profile_data = request.data.get('profile', {})
        logger.debug(f"User data: {user_data}")
        logger.debug(f"Profile data: {profile_data}")
        is_valid = True
        if user_data:
            user_serializer = UserUpdateSerializer(user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                is_valid = False
                logger.error(f"User update errors: {user_serializer.errors}")
        profile_serializer = (
            StudentProfileSerializer(profile, data=profile_data, partial=True)
            if user.role == User.Role.STUDENT else TeacherProfileSerializer(profile, data=profile_data, partial=True)
        )
        if profile_serializer.is_valid():
            profile_serializer.save()
        else:
            is_valid = False
            logger.error(f"Profile update errors: {profile_serializer.errors}")
        if is_valid:
            logger.info(f"Updated profile for {user.email}")
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Profile updated successfully.")
                return redirect('profile')
            return Response({
                'user': user_serializer.data if user_data else UserUpdateSerializer(user).data,
                'profile': profile_serializer.data
            })
        logger.error(f"Combined errors: {user_serializer.errors if user_data else {}} | {profile_serializer.errors}")
        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'user': user,
                    'profile': profile,
                    'user_data': user_data,
                    'profile_data': profile_data,
                    'errors': {**(user_serializer.errors if user_data else {}), **profile_serializer.errors},
                    'is_update': True
                },
                template_name='accounts/profile.html',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({**(user_serializer.errors if user_data else {}), **profile_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request):
    #     user = request.user
    #     profile = user.get_profile()
    #     if not profile:
    #         logger.warning(f"No profile found for {user.email}")
    #         if request.accepted_renderer.format == 'html':
    #             messages.error(request, "Profile not found.")
    #             return redirect('home')
    #         return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    #     if request.accepted_renderer.format == 'html':
    #         raw = request.POST
    #         user_data = {
    #             'first_name': raw.get('first_name', '').strip() or None,
    #             'last_name': raw.get('last_name', '').strip() or None,
    #         }
    #         profile_data = {
    #             'phone_number': raw.get('phone_number', '').strip() or None,
    #             'date_of_birth': raw.get('date_of_birth', '').strip() or None,
    #             'gender': raw.get('gender', '').strip() or None,
    #         }
    #         if user.role == User.Role.STUDENT:
    #             profile_data.update({
    #                 'grade_level': raw.get('grade_level', '').strip() or None,
    #                 'parent_email': raw.get('parent_email', '').strip() or None,
    #             })
    #         else:
    #             profile_data.update({
    #                 'department': raw.get('department', '').strip() or None,
    #                 'office_number': raw.get('office_number', '').strip() or None,
    #                 'qualifications': raw.get('qualifications', '').strip() or None,
    #             })
    #         if 'avatar' in request.FILES:
    #             profile_data['avatar'] = request.FILES['avatar']
    #     else:
    #         user_data = request.data.get('user', {})
    #         profile_data = request.data.get('profile', {})
    #     logger.debug(f"User data: {user_data}")
    #     logger.debug(f"Profile data: {profile_data}")

    #     user_serializer = UserUpdateSerializer(user, data=user_data, partial=True)
    #     profile_serializer = (
    #         StudentProfileSerializer(profile, data=profile_data, partial=True)
    #         if user.role == User.Role.STUDENT else TeacherProfileSerializer(profile, data=profile_data, partial=True)
    #     )
    #     is_valid = True
    #     if user_serializer.is_valid():
    #         user_serializer.save()
    #     else:
    #         is_valid = False
    #         logger.warning(f"User update failed for innumerable {user.email}: {user_serializer.errors}")
    #     if profile_serializer.is_valid():
    #         profile_serializer.save()
    #     else:
    #         is_valid = False
    #         logger.warning(f"Profile update failed for {user.email}: {profile_serializer.errors}")
    #     if is_valid:
    #         logger.info(f"Updated profile for {user.email}")
    #         if request.accepted_renderer.format == 'html':
    #             messages.success(request, "Profile updated successfully.")
    #             return redirect('profile')
    #         return Response({
    #             'user': user_serializer.data,
    #             'profile': profile_serializer.data
    #         })
    #     if request.accepted_renderer.format == 'html':
    #         return Response(
    #             {
    #                 'user': user,
    #                 'profile': profile,
    #                 'user_data': user_data,
    #                 'profile_data': profile_data,
    #                 'errors': {**user_serializer.errors, **profile_serializer.errors},
    #                 'is_update': True
    #             },
    #             template_name='accounts/profile.html',
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
    #     return Response({**user_serializer.errors, **profile_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ApprovalRequestView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        # Check for pending or rejected requests
        pending_request = ApprovalRequest.objects.filter(
            user=request.user, status=ApprovalRequest.Status.PENDING
        ).first()
        rejected_request = ApprovalRequest.objects.filter(
            user=request.user, status=ApprovalRequest.Status.REJECTED
        ).order_by('-created_at').first()

        serializer = ApprovalRequestSerializer(pending_request) if pending_request else None
        rejection_reason = rejected_request.rejection_reason if rejected_request else None

        if request.accepted_renderer.format == 'html':
            return Response(
                {
                    'approval_request': serializer.data if serializer else None,
                    'rejection_reason': rejection_reason,
                },
                template_name='accounts/approval_request.html'
            )
        return Response(
            {
                'approval_request': serializer.data if serializer else None,
                'rejection_reason': rejection_reason,
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        pending_request = ApprovalRequest.objects.filter(
            user=request.user, status=ApprovalRequest.Status.PENDING
        ).first()
        if pending_request:
            serializer = ApprovalRequestSerializer(pending_request, data=request.data)
        else:
            serializer = ApprovalRequestSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            approval_request = serializer.save(user=request.user)
            logger.info("Approval request submitted for user: %s (ID: %s)", request.user.username, approval_request.id)
            send_approval_request_notification.delay(approval_request.id)

            if request.accepted_renderer.format == 'html':
                messages.success(request, "Your credentials have been submitted for approval.")
                return redirect('profile')
            return Response(
                {"message": "Credentials submitted successfully."},
                status=status.HTTP_201_CREATED
            )
        else:
            logger.warning("Approval request validation errors: %s", serializer.errors)
            if request.accepted_renderer.format == 'html':
                return Response(
                    {"errors": serializer.errors, "form_data": request.data},
                    template_name='accounts/approval_request.html',
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class ApprovalRequestView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     permission_classes = [IsAuthenticated, IsTeacher]

#     def get(self, request):
#         approval_request = ApprovalRequest.objects.filter(user=request.user, status=ApprovalRequest.Status.PENDING).first()
#         serializer = ApprovalRequestSerializer(approval_request)
#         if request.accepted_renderer.format == 'html':
#             return Response(
#                 {'approval_request': serializer.data if serializer else None},
#                 template_name='accounts/approval_request.html'
#             )
#         return Response(
#             {'approval_request': serializer.data if serializer else None},
#             status=status.HTTP_200_OK
#         )

#     def post(self, request):
#         pending_request = ApprovalRequest.objects.filter(user=request.user, status=ApprovalRequest.Status.PENDING).first()
#         if pending_request:
#             serializer = ApprovalRequestSerializer(pending_request, data=request.data)
#         else:
#             serializer = ApprovalRequestSerializer(data=request.data, context={'request': request})
        
#         if serializer.is_valid():
#             approval_request = serializer.save(user=request.user)
#             logger.info("Approval request submitted for user: %s", request.user.username)
#             send_approval_request_notification.delay(approval_request.id)

#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, "Your credentials have been submitted for approval.")
#                 return redirect('profile')
#             return Response(
#                 {"message": "Credentials submitted successfully."},
#                 status=status.HTTP_201_CREATED
#             )
#         else:
#             logger.warning("Approval request validation errors: %s", serializer.errors)
#             if request.accepted_renderer.format == 'html':
#                 return Response(
#                     {"errors": serializer.errors, "form_data": request.data},
#                     template_name='accounts/approval_request.html',
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#             return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)