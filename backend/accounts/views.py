import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.utils import timezone
from django.http import JsonResponse
from .models import User
from .utils import generate_otp, send_email_otp, is_otp_valid
from datetime import timedelta


# Homepage
def home(request):
    return render(request, 'accounts/index.html')


# Signup with OTP verification
def signup(request):
    if request.method == "POST":
        step = request.POST.get('step', '1')
        
        if step == '1':
            # First step - collect user data and send OTP
            return handle_signup_step1(request)
        elif step == '2':
            # Second step - verify OTP and create user
            return handle_signup_step2(request)
    
    return render(request, 'accounts/signup.html')


def handle_signup_step1(request):
    """Handle first step of signup - validate data and send OTP"""
    # Get form data
    full_name = request.POST.get('full_name', '').strip()
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    phone_number = request.POST.get('phone_number', '').strip()
    password = request.POST.get('password', '').strip()
    confirm_password = request.POST.get('confirm_password', '').strip()
    user_type = request.POST.get('user_type', '').strip()

    # Store form data for re-displaying on error
    form_data = {
        'full_name': full_name,
        'username': username,
        'email': email,
        'phone_number': phone_number,
        'user_type': user_type,
        'university': request.POST.get('university', ''),
        'degree': request.POST.get('degree', ''),
        'graduation_year': request.POST.get('graduation_year', ''),
        'job_title': request.POST.get('job_title', ''),
        'organization': request.POST.get('organization', ''),
        'experience': request.POST.get('experience', ''),
        'company_name': request.POST.get('company_name', ''),
        'company_website': request.POST.get('company_website', ''),
        'company_description': request.POST.get('company_description', ''),
    }

    # Validation
    if not all([full_name, username, email, phone_number, password, confirm_password, user_type]):
        messages.error(request, "All required fields must be filled.")
        return render(request, 'accounts/signup.html', {'form_data': form_data})

    if password != confirm_password:
        messages.error(request, "Passwords do not match.")
        return render(request, 'accounts/signup.html', {'form_data': form_data})

    if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        messages.error(request, "Password must be at least 8 characters long and contain letters and numbers.")
        return render(request, 'accounts/signup.html', {'form_data': form_data})

    # Check if email already exists and is verified
    existing_user = User.objects.filter(email=email).first()
    if existing_user and existing_user.email_verified:
        messages.error(request, "Email already exists and is verified.")
        return render(request, 'accounts/signup.html', {'form_data': form_data})

    # Check username (only if it doesn't belong to unverified user with same email)
    username_user = User.objects.filter(username=username).first()
    if username_user and (username_user.email != email or username_user.email_verified):
        messages.error(request, "Username already exists.")
        return render(request, 'accounts/signup.html', {'form_data': form_data})

    # Check phone number (only if it doesn't belong to unverified user with same email)
    phone_user = User.objects.filter(phone_number=phone_number).first()
    if phone_user and (phone_user.email != email or phone_user.email_verified):
        messages.error(request, "Phone number already exists.")
        return render(request, 'accounts/signup.html', {'form_data': form_data})

    # Delete existing unverified user with same email if exists
    if existing_user and not existing_user.email_verified:
        existing_user.delete()

    # Generate and send OTP
    email_otp = generate_otp()
    
    if send_email_otp(email, email_otp):
        # Store data in session
        request.session['signup_data'] = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone_number': phone_number,
            'password': password,
            'user_type': user_type,
            'email_otp': email_otp,
            'otp_created_at': timezone.now().isoformat(),
            # Store user-type specific fields
            'university': request.POST.get('university', ''),
            'degree': request.POST.get('degree', ''),
            'graduation_year': request.POST.get('graduation_year', ''),
            'job_title': request.POST.get('job_title', ''),
            'organization': request.POST.get('organization', ''),
            'experience': request.POST.get('experience', ''),
            'company_name': request.POST.get('company_name', ''),
            'company_website': request.POST.get('company_website', ''),
            'company_description': request.POST.get('company_description', ''),
        }
        
        return JsonResponse({
            'success': True, 
            'message': f'OTP sent to {email}. Please check your email and enter the verification code.',
            'email': email
        })
    else:
        return JsonResponse({
            'success': False, 
            'message': 'Failed to send OTP. Please check your email address and try again.'
        })


def handle_signup_step2(request):
    """Handle second step of signup - verify OTP and create user"""
    signup_data = request.session.get('signup_data')
    if not signup_data:
        return JsonResponse({
            'success': False, 
            'message': 'Session expired. Please start registration again.'
        })
    
    email_otp_input = request.POST.get('email_otp', '').strip()
    
    if not email_otp_input:
        return JsonResponse({
            'success': False, 
            'message': 'Please enter the OTP.'
        })
    
    # Check OTP expiration
    otp_created_at = timezone.datetime.fromisoformat(signup_data['otp_created_at'])
    
    if not is_otp_valid(otp_created_at):
        return JsonResponse({
            'success': False, 
            'message': 'OTP has expired. Please request a new one.'
        })
    
    # Verify OTP
    if email_otp_input != signup_data['email_otp']:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid OTP. Please try again.'
        })
    if User.objects.filter(email=signup_data['email'], email_verified=True).exists():
        return JsonResponse({'success': False, 'message': 'Email already exists and is verified.'})

    if User.objects.filter(username=signup_data['username']).exclude(email=signup_data['email']).exists():
        return JsonResponse({'success': False, 'message': 'Username is already taken.'})
        
    # Create user
    try:
        user = User.objects.create_user(
            username=signup_data['username'],
            email=signup_data['email'],
            password=signup_data['password'],
            full_name=signup_data['full_name'],
            phone_number=signup_data['phone_number'],
            user_type=signup_data['user_type'],
            email_verified=True  # Mark email as verified
        )
        
        # Set user-type specific fields
        if signup_data['user_type'] == 'student':
            if signup_data.get('university'):
                user.university = signup_data['university']
            if signup_data.get('degree'):
                user.degree = signup_data['degree']
            if signup_data.get('graduation_year'):
                try:
                    user.graduation_year = int(signup_data['graduation_year'])
                except ValueError:
                    pass
        
        elif signup_data['user_type'] == 'professional':
            if signup_data.get('job_title'):
                user.job_title = signup_data['job_title']
            if signup_data.get('organization'):
                user.organization = signup_data['organization']
            if signup_data.get('experience'):
                try:
                    user.experience = int(signup_data['experience'])
                except ValueError:
                    pass
        
        elif signup_data['user_type'] == 'recruiter':
            if signup_data.get('company_name'):
                user.company_name = signup_data['company_name']
            if signup_data.get('company_website'):
                user.company_website = signup_data['company_website']
            if signup_data.get('company_description'):
                user.company_description = signup_data['company_description']
        
        user.save()
        
        # Clear session data
        if 'signup_data' in request.session:
            del request.session['signup_data']
        
        return JsonResponse({
            'success': True, 
            'message': 'Account created successfully! Your email has been verified. Redirecting to login...',
            'redirect_url': '/login/'
        })
        
    except IntegrityError as e:
        print(f"[SIGNUP] IntegrityError: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Failed to create account. Username or email might already exist.'
        })

    except Exception as e:
        print(f"[SIGNUP] Unexpected error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Failed to create account. Please try again.'
        })



def resend_otp(request):
    """Resend OTP to email"""
    if request.method == "POST":
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return JsonResponse({'success': False, 'message': 'Session expired. Please start registration again.'})
        
        try:
            new_otp = generate_otp()
            if send_email_otp(signup_data['email'], new_otp):
                # Update session with new OTP and timestamp
                signup_data['email_otp'] = new_otp
                signup_data['otp_created_at'] = timezone.now().isoformat()
                request.session['signup_data'] = signup_data
                
                return JsonResponse({'success': True, 'message': 'New OTP sent successfully to your email.'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


# Login with email verification check
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, 'accounts/login.html')

        try:
            user = User.objects.get(email=email)
            
            # Check if email is verified
            if not user.email_verified:
                messages.error(request, "Please verify your email address before logging in.")
                return render(request, 'accounts/login.html')
            
            auth_user = authenticate(request, username=user.username, password=password)

            if auth_user:
                auth_login(request, auth_user)

                if auth_user.user_type == 'recruiter':
                    return redirect('/recruiter/')
                else:
                    return redirect('dashboard:home')
            else:
                messages.error(request, "Incorrect password.")
                
        except User.DoesNotExist:
            messages.error(request, "User not found.")

    return render(request, 'accounts/login.html')


# Logout
def logout_user(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('accounts:login')


# Profile
@login_required
def profile(request):
    user = request.user

    if request.method == 'POST':
        try:
            user.full_name = request.POST.get('full_name', user.full_name)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.linkedin_profile = request.POST.get('linkedin_profile', user.linkedin_profile)
            user.github_profile = request.POST.get('github_profile', user.github_profile)
            user.portfolio_website = request.POST.get('portfolio_website', user.portfolio_website)
            user.objective = request.POST.get('objective', user.objective)
            user.profile_photo = request.FILES.get('profile_photo', user.profile_photo)
            user.save()
            messages.success(request, "Profile updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")

    return render(request, 'accounts/profile.html', {'user': user})


# Delete Account
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        if hasattr(user, 'recruiterprofile'):
            user.recruiterprofile.delete()
        auth_logout(request)
        user.delete()
        return redirect('accounts:home')
    return redirect('accounts:profile')

# Add these new functions to your existing views.py

def forgot_password(request):
    """Handle forgot password - send OTP to email"""
    if request.method == "POST":
        step = request.POST.get('step', '1')
        
        if step == '1':
            # First step - validate email and send OTP
            return handle_forgot_password_step1(request)
        elif step == '2':
            # Second step - verify OTP
            return handle_forgot_password_step2(request)
        elif step == '3':
            # Third step - reset password
            return handle_forgot_password_step3(request)
    
    return render(request, 'accounts/forgot_password.html')


def handle_forgot_password_step1(request):
    """Send OTP to user's email for password reset"""
    email = request.POST.get('email', '').strip()
    
    if not email:
        return JsonResponse({
            'success': False,
            'message': 'Please enter your email address.'
        })
    
    try:
        user = User.objects.get(email=email, email_verified=True)
        
        # Generate and send OTP
        reset_otp = generate_otp()
        
        if send_email_otp(email, reset_otp):
            # Store OTP and timestamp in user model
            user.email_otp = reset_otp
            user.otp_created_at = timezone.now()
            user.save()
            
            # Store email in session for next steps
            request.session['reset_email'] = email
            
            return JsonResponse({
                'success': True,
                'message': f'Password reset OTP sent to {email}. Please check your email.',
                'email': email
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to send OTP. Please try again.'
            })
            
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No account found with this email address.'
        })


def handle_forgot_password_step2(request):
    """Verify OTP for password reset"""
    reset_email = request.session.get('reset_email')
    if not reset_email:
        return JsonResponse({
            'success': False,
            'message': 'Session expired. Please start the password reset process again.'
        })
    
    otp_input = request.POST.get('otp', '').strip()
    
    if not otp_input:
        return JsonResponse({
            'success': False,
            'message': 'Please enter the OTP.'
        })
    
    try:
        user = User.objects.get(email=reset_email, email_verified=True)
        
        # Check OTP expiration
        if not is_otp_valid(user.otp_created_at):
            return JsonResponse({
                'success': False,
                'message': 'OTP has expired. Please request a new one.'
            })
        
        # Verify OTP
        if otp_input != user.email_otp:
            return JsonResponse({
                'success': False,
                'message': 'Invalid OTP. Please try again.'
            })
        
        # OTP verified successfully
        return JsonResponse({
            'success': True,
            'message': 'OTP verified successfully. You can now reset your password.'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Invalid session. Please start again.'
        })


def handle_forgot_password_step3(request):
    """Reset user password after OTP verification"""
    reset_email = request.session.get('reset_email')
    if not reset_email:
        return JsonResponse({
            'success': False,
            'message': 'Session expired. Please start the password reset process again.'
        })
    
    new_password = request.POST.get('new_password', '').strip()
    confirm_password = request.POST.get('confirm_password', '').strip()
    
    if not new_password or not confirm_password:
        return JsonResponse({
            'success': False,
            'message': 'Please fill in both password fields.'
        })
    
    if new_password != confirm_password:
        return JsonResponse({
            'success': False,
            'message': 'Passwords do not match.'
        })
    
    if len(new_password) < 8 or not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
        return JsonResponse({
            'success': False,
            'message': 'Password must be at least 8 characters long and contain letters and numbers.'
        })
    
    try:
        user = User.objects.get(email=reset_email, email_verified=True)
        
        # Reset password
        user.set_password(new_password)
        user.email_otp = None  # Clear OTP
        user.otp_created_at = None  # Clear OTP timestamp
        user.save()
        
        # Clear session
        if 'reset_email' in request.session:
            del request.session['reset_email']
        
        return JsonResponse({
            'success': True,
            'message': 'Password reset successfully! You can now login with your new password.',
            'redirect_url': '/login/'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Invalid session. Please start again.'
        })


def resend_reset_otp(request):
    """Resend OTP for password reset"""
    if request.method == "POST":
        reset_email = request.session.get('reset_email')
        if not reset_email:
            return JsonResponse({
                'success': False,
                'message': 'Session expired. Please start the password reset process again.'
            })
        
        try:
            user = User.objects.get(email=reset_email, email_verified=True)
            
            # Generate new OTP
            new_otp = generate_otp()
            
            if send_email_otp(reset_email, new_otp):
                # Update user with new OTP
                user.email_otp = new_otp
                user.otp_created_at = timezone.now()
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'New OTP sent successfully to your email.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to send OTP. Please try again.'
                })
                
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid session. Please start again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})