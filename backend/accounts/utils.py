import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(email, otp):
    """Send OTP to email"""
    subject = 'JobElevate - Email Verification OTP'
    message = f'''
    Hi there!
    
    Your email verification OTP for JobElevate is: {otp}
    
    This OTP will expire in 10 minutes.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    JobElevate Team
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def is_otp_valid(created_at):
    """Check if OTP is still valid (within 10 minutes)"""
    if not created_at:
        return False
    return timezone.now() < created_at + timedelta(minutes=10)