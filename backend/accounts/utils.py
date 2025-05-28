# accounts/utils.py
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_email_otp(email, otp, subject=None, message=None):
    """Send OTP to user's email"""
    if not subject:
        subject = "Your JobElevate Verification Code"
    
    if not message:
        message = f"""
        Hello,
        
        Your verification code is: {otp}
        
        This code will expire in 10 minutes for security reasons.
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        JobElevate Team
        """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send OTP to {email}: {str(e)}")
        return False

def send_password_reset_otp(email, otp):
    """Send password reset OTP to user's email"""
    subject = "Your JobElevate Password Reset Code"
    message = f"""
    Hello,
    
    You requested to reset your password for your JobElevate account.
    
    Your password reset code is: {otp}
    
    This code will expire in 10 minutes for security reasons.
    
    If you didn't request this password reset, please ignore this email and your password will remain unchanged.
    
    Best regards,
    JobElevate Team
    """
    
    return send_email_otp(email, otp, subject=subject, message=message)

def is_otp_valid(otp_created_at):
    """Check if OTP is still valid (within 10 minutes)"""
    if not otp_created_at:
        return False
    
    # Handle both timezone-aware and naive datetime objects
    if isinstance(otp_created_at, str):
        otp_created_at = datetime.fromisoformat(otp_created_at)
    
    # Make sure we're working with timezone-aware datetime
    if timezone.is_naive(otp_created_at):
        otp_created_at = timezone.make_aware(otp_created_at)
    
    expiry_time = otp_created_at + timedelta(minutes=10)
    return timezone.now() < expiry_time