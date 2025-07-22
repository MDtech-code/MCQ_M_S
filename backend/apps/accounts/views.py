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
from apps.common.permissions import IsTeacher,IsStudent,IsApprovedTeacher,IsAdmin,IsVerified,IsNotAuthenticated,RoleBasedProfilePermission
from apps.accounts.service.auth_service import AuthService
from apps.accounts.service.profile_service import ProfileService
from apps.common.api.base import BaseAPIView
import logging
logger = logging.getLogger(__name__)
















#! Signup 
@method_decorator(ensure_csrf_cookie, name='dispatch')
class SignupView(BaseAPIView):
    template_name='accounts/auth/signup.html'
    permission_classes = [IsNotAuthenticated]
    authentication_classes = [SessionAuthentication]


    def get(self, request):
        return self.render_response(data={"message": "Signup endpoint (GET)"}, status_code=status.HTTP_200_OK, template_name=self.template_name)

    def post(self, request):
        auth_service = AuthService()
        user, token, errors = auth_service.signup(request)
        if errors:
            return self.render_response(data={"errors": errors},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message="Signup failed. Please check your input.",message_level= 'error',html_context={"form_data": request.data})
        response_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
        }
        response = self.render_response(data=response_data, status_code=status.HTTP_201_CREATED, template_name='redirect:home', message="User created successfully.")
        response.set_cookie(
            key='auth_token',
            value=token,
            httponly=True,
            samesite='Lax',
            max_age=86400
        )
        return response
    


#! login
@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(BaseAPIView):
    template_name='accounts/auth/login.html'
    permission_classes = [IsNotAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        return self.render_response(data={"message": "Login endpoint (GET)"}, status_code=status.HTTP_200_OK, template_name=self.template_name)

    def post(self, request):
        auth_service = AuthService()
        user, token, errors = auth_service.login(request)
        if errors:
            return self.render_response(
                data={"errors": errors},
                status_code=status.HTTP_401_UNAUTHORIZED,
                template_name=self.template_name,
                message="Invalid credentials. Please try again.",
                message_level='error',
                html_context={"form_data": request.data}
            )
        response_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        }
        cookie_max_age = 30 * 24 * 3600 if request.data.get('remember') else None
        response = self.render_response(data=response_data, status_code=status.HTTP_200_OK, template_name='redirect:home', message="User login successfully.")
        response.set_cookie(
            key='auth_token',
            value=token,
            httponly=True,
            samesite='Lax',
            max_age=cookie_max_age
        )
        return response



#! logout view
@method_decorator(ensure_csrf_cookie, name='dispatch')
class LogoutView(BaseAPIView):
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        username = request.user.username
        logger.info("Logout initiated for user '%s'", username)
        
        try:
            # Token deletion (for API clients)
            if request.auth:
                request.auth.delete()
                logger.info("Token for user '%s' deleted successfully.", username)
            else:
                logger.warning("No token found for authenticated user '%s' during logout.", username)

            # Session termination (for all clients)
            logout(request)
            
            # Create response using base view - it handles both HTML/JSON automatically
            response = self.render_response(
                data={},
                status_code=status.HTTP_200_OK,
                template_name='redirect:home',  # Redirect HTML clients
                message="You have been logged out successfully.",
            )
            
            # Delete authentication cookies
            response.delete_cookie('auth_token')
            
           
            return response
            
        except Exception as e:
            logger.error("Error during logout for user '%s': %s", username, str(e))
            return self.render_response(
                data={},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                template_name='home/home.html',
                message="An error occurred during logout.",
                message_level='error',
            )





@method_decorator(ensure_csrf_cookie, name='dispatch')
class VerifyEmailView(BaseAPIView):
    template_name='accounts/verify_email.html'
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            token_obj = EmailVerificationToken.objects.get(token=token)
            user = token_obj.user

            # Validate token expiry
            if not token_obj.is_valid():
                logger.warning(f"Expired token {token} for {token_obj.user.email}")
                return self.render_response(
                    data={},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    template_name=self.template_name,
                    message="Verification link has expired.",
                    message_level='error'
                )
            
            originally_verified = user.is_verified
            if token_obj.new_email:
                user.email = token_obj.new_email
                user.is_verified = True
                logger.info(f"Updated email to {user.email} and verified")
            else:
                user.is_verified = True
                logger.info(f"Email verified for {user.email}")

            user.save()
            token_obj.delete()
            login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')

            if originally_verified and not token_obj.new_email:
                logger.info(f"Email already verified for {user.email}")
                return self.render_response(
                    data={},
                    status_code=status.HTTP_200_OK,
                    template_name='redirect:profile',
                    message="Email already verified.",
                    message_level='info'
                )
            
            # Successful verification
            return self.render_response(
                data={},
                status_code=status.HTTP_200_OK,
                template_name=self.template_name, 
                message="Email verified successfully.",
                message_level='success'
            )
            
        except EmailVerificationToken.DoesNotExist:
            logger.warning(f"Invalid token {token}")
            return self.render_response(
                data={},
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name,
                message="Invalid verification link.",
                message_level='error'
            )




@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResendVerificationEmailView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]


    def post(self, request):
        user = request.user
        if user.is_verified:
            logger.info(f"User {user.email} already verified, resend rejected")
            return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name='redirect:home',message="Email already verified",message_level='info')
        
        EmailVerificationToken.objects.filter(user=user).delete()
        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email_task.delay(user.id, token.token)
        logger.info(f"Resent verification email for {user.email}")
        return self.render_response(data={},status_code=status.HTTP_200_OK,template_name='redirect:home',message="Verification email sent")
    


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ForgotPasswordView(BaseAPIView):
    template_name='accounts/password_reset_request.html'
    permission_classes = [IsNotAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        return self.render_response(data={"message": "Forgot password endpoint (GET)"},status_code=status.HTTP_200_OK,template_name=self.template_name)

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
            return self.render_response(data={},status_code=status.HTTP_200_OK,template_name='accounts/password_reset_done.html',message="Password reset email sent. Check your inbox.")
        logger.warning(f"Forgot password failed: %s", serializer.errors)
        return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message='Error accour during password reset .',errors=serializer.errors,message_level='error',html_context={"form_data": request.data})
    



#! Password reset view
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResetPasswordView(BaseAPIView):
    template_name='accounts/password_reset_confirm.html'
    permission_classes = [IsNotAuthenticated]
    authentication_classes = [SessionAuthentication]


    def get(self, request, token):
        try:
            token_obj = PasswordResetToken.objects.get(token=token)
            if not token_obj.is_valid():
                logger.warning(f"Expired reset token {token}")
                return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message="Password reset link has expired.",message_level='error')
            return self.render_response(data={"message": "Valid token"},status_code=status.HTTP_200_OK,template_name=self.template_name,html_context={'token': token})
        except PasswordResetToken.DoesNotExist:
            logger.warning(f"Invalid reset token {token}")
            return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message="Invalid password reset link.",message_level='error')

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
                return self.render_response(data={},status_code=status.HTTP_200_OK,template_name='accounts/password_reset_complete.html',message="Password reset successfully.")
              
            except PasswordResetToken.DoesNotExist:
                logger.warning(f"Invalid reset token {token}")
                return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message="Invalid password reset link.",message_level='error')
        logger.warning(f"Reset password failed: %s", serializer.errors)
        return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message='Error accour during password reset',errors=serializer.errors,message_level='error',html_context={"form_data": request.data, 'token': token})

#! password change view
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ChangePasswordView(BaseAPIView):
    template_name='accounts/change_password.html'
    permission_classes = [IsAuthenticated,IsVerified]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication] 
    

    def get(self, request):
        
        return self.render_response(data={"message": "Change password endpoint (GET)"},status_code=status.HTTP_200_OK,template_name=self.template_name)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        response = None 
        if serializer.is_valid():
       
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            if request.auth:
                request.auth.delete()
                logger.info(f"Auth token deleted for {user.email} after password change")

            # Logout the user for session-based authentication
            logout(request)
            logger.info(f"Password changed for {user.email}")

            # Create response and remove authentication cookies
            response=self.render_response(data={},status_code=status.HTTP_200_OK,template_name='redirect:login',message="Password changed successfully. Please log in again.")
            response.delete_cookie('auth_token')
            response.delete_cookie('csrftoken')
            
            return response
        logger.warning(f"Change password failed for {request.user.email}: %s", serializer.errors)
        return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message='Error accour during password change.',errors=serializer.errors,message_level='error',html_context={ "form_data": request.data})

    
#! accouts delete view 
@method_decorator(ensure_csrf_cookie, name='dispatch')
class DeleteAccountView(BaseAPIView):
    template_name='accounts/delete_account.html'
    permission_classes = [IsAuthenticated,IsVerified ]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    

    def get(self, request):
        return self.render_response(data={"message": "Delete account endpoint (GET)"},status_code=status.HTTP_200_OK,template_name=self.template_name)

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
                    return self.render_response(data={},status_code=status.HTTP_200_OK,template_name='redirect:home',message="Account deleted permanently.")
                except Exception as e:
                    logger.error(f"Hard deletion failed for {email}: %s", str(e))
                    return self.render_response(data={},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,template_name=self.template_name,message= "Failed to delete account.",message_level='error')
            else:
                user.is_active = False
                user.save()
                logger.info(f"Soft deletion completed for {role} {email}")
                send_deletion_confirmation_email_task.delay(email, role)
                if request.auth:
                    request.auth.delete()
                    logger.info(f"Auth token deleted for {email}")
                return self.render_response(data={},status_code=status.HTTP_200_OK,template_name='redirect:home',message=f"{role} account deactivated successfully.")
        logger.warning(f"Account deletion failed for {request.user.email}: %s", serializer.errors)
        return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message='Error accour during account deletion.',errors=serializer.errors,message_level='error',html_context={"form_data": request.data})



#! Email Update view
@method_decorator(ensure_csrf_cookie, name='dispatch')
class UpdateEmailView(BaseAPIView):
    template_name='accounts/update_email.html'
    permission_classes = [IsAuthenticated,IsVerified]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request):
        return self.render_response(data={"message": "Update email endpoint (GET)"},status_code=status.HTTP_200_OK,template_name=self.template_name)


    def post(self, request):
        serializer = UpdateEmailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            new_email = serializer.validated_data['new_email']
            EmailVerificationToken.objects.filter(user=user).delete()
            token = EmailVerificationToken.objects.create(user=user, new_email=new_email)

            send_verification_email_task.delay(user.id, token.token, new_email=new_email)
            logger.info(f"Verification email sent to {new_email}")
            return self.render_response(data={},status_code=status.HTTP_200_OK,template_name='redirect:profile',message="Verification email sent to your new email.")

        logger.warning(f"Email update failed for {request.user.email}: %s", serializer.errors)
        return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message='error occur during email update',errors=serializer.errors,message_level='error',html_context={"form_data": request.data})





#! profile view 
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProfileView(BaseAPIView):
    template_name='accounts/profile.html'
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        profile_data = ProfileService.get_profile(user)
        if not profile_data:
            logger.warning("Profile view: no profile found for user %s", user.username)
            return self.render_response(
                data={},
                status_code=status.HTTP_404_NOT_FOUND,
                template_name='redirect:home',
                message= "Profile not found.",
                message_level='error'
            )
        user_serializer = UserUpdateSerializer(user)
        return self.render_response(
           data= {
                'user': user,
                'profile': profile_data,
                'user_data': user_serializer.data,
                'profile_data': profile_data,
                'is_update': False
            },
            status_code=status.HTTP_200_OK,
            template_name=self.template_name
        )

#! profile Update view
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProfileUpdateView(BaseAPIView):
    template_name='accounts/profile.html'
    permission_classes = [IsAuthenticated, RoleBasedProfilePermission]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        profile_data = ProfileService.get_profile(user)
        if not profile_data:
            logger.warning("Profile update view: no profile found for user %s", user.username)
            return self.render_response(
                data={},
                status_code=status.HTTP_404_NOT_FOUND,
                template_name='redirect:home',
                message="Profile not found.",
                message_level='error'
            )
        user_serializer = UserUpdateSerializer(user)
        return self.render_response(
            data={
                'user': user,
                'profile': profile_data,
                'user_data': user_serializer.data,
                'profile_data': profile_data,
                'is_update': True
            },
            status_code=status.HTTP_200_OK,
            template_name=self.template_name,
            
        )

    def post(self, request):
        user = request.user
        user_data = (
            {
                'first_name': request.POST.get('first_name', '').strip() or None,
                'last_name': request.POST.get('last_name', '').strip() or None,
            } if request.accepted_renderer.format == 'html'
            else request.data.get('user', request.data)
        )
        profile_data, errors = ProfileService.update_profile(user, request.data, request.FILES)
        if errors:
            return self.render_response(
                data={},
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name,
                message="Profile update failed.",
                errors=errors,
                message_level='error',
                html_context={'form_data': request.data}
                
            )
        user_serializer = UserUpdateSerializer(user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            logger.info("User data updated successfully for user %s", user.username)
        else:
            logger.warning("User data validation errors for user %s: %s", user.username, user_serializer.errors)
            return self.render_response(
                data={},
                status_code=status.HTTP_400_BAD_REQUEST,
                template_name=self.template_name,
                message="User data update failed.",
                errors=user_serializer.errors,
                message_level='error',
                html_context={'form_data': request.data}
            )
        
        return self.render_response(
            data={'user':request.user,
                'user_data': user_serializer.data,
                'profile': profile_data
            },
            status_code=status.HTTP_200_OK,
            template_name=self.template_name,
            message="Profile updated successfully."
        )


# self.render_response(data=,status_code=,template_name=,message=,message_level=,html_context=)
#! Approval Request View 
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ApprovalRequestView(BaseAPIView):
    template_name='accounts/approval_request.html'
    permission_classes = [IsAuthenticated, IsTeacher]
    authentication_classes = [CookieTokenAuthentication, SessionAuthentication]

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

       
        Response_data= {
                    'approval_request': serializer.data if serializer else None,
                    'rejection_reason': rejection_reason,
                }
        return self.render_response(data=Response_data,status_code=status.HTTP_200_OK,template_name=self.template_name)

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
            return self.render_response(data={},status_code=status.HTTP_201_CREATED,template_name='redirect:profile',message="Your credentials have been submitted for approval.")
        
        else:
            logger.warning("Approval request validation errors: %s", serializer.errors)
            return self.render_response(data={},status_code=status.HTTP_400_BAD_REQUEST,template_name=self.template_name,message='Error during credentials submission',errors=serializer.errors,message_level='error',html_context={"form_data": request.data})

