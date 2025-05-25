from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('delete/', views.delete_account, name='delete_account'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),  # New URL for resend OTP
]