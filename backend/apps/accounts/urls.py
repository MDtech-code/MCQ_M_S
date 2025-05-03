from django.urls import path
from .views import SignupView, LoginView, LogoutView,VerifyEmailView,ResendVerificationEmailView,ForgotPasswordView,ResetPasswordView,ProfileUpdateView,ChangePasswordView,DeleteAccountView,UpdateEmailView,ProfileView
from . import views
urlpatterns = [
   


    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('update-email/', UpdateEmailView.as_view(), name='update_email'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('approval/request/', views.ApprovalRequestView.as_view(), name='approval_request'),
    
]
