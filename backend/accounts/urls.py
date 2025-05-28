# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    # Add these missing URL patterns for forgot password functionality
    path('login/forgot-password/', views.forgot_password, name='forgot_password'),
    path('resend-reset-otp/', views.resend_reset_otp, name='resend_reset_otp'),
]