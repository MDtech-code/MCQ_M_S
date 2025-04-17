from django.urls import path
from .views import SignupView, LoginView, LogoutView,VerifyEmailView,ResendVerificationEmailView,ForgotPasswordView,ResetPasswordView,ProfileUpdateView,ChangePasswordView,DeleteAccountView,UpdateEmailView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('update-email/', UpdateEmailView.as_view(), name='update_email'),
    path('profile/', ProfileUpdateView.as_view(), name='profile_update'),
    
]
