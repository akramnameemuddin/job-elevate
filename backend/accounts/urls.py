from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('delete/', views.delete_account, name='delete_account'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),  # For signup OTP
    # Add these new URLs for forgot password
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('resend-reset-otp/', views.resend_reset_otp, name='resend_reset_otp'),  # For password reset OTP
]