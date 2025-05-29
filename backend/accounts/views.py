import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import User
from .utils import generate_otp, send_email_otp, is_otp_valid, send_password_reset_otp
from datetime import timedelta, datetime
from django.contrib.auth.hashers import make_password


# Homepage
def home(request):
    return render(request, 'accounts/index.html')


# Signup with OTP verification
def signup(request):
    if request.method == "POST":
        try:
            step = request.POST.get('step', '1')
            
            if step == '1':
                # First step - collect user data and send OTP
                return handle_signup_step1(request)
            elif step == '2':
                # Second step - verify OTP and create user
                return handle_signup_step2(request)
        except Exception as e:
            print(f"[SIGNUP] Error in signup view: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'An error occurred. Please try again.'
                })
            else:
                messages.error(request, 'An error occurred. Please try again.')
                return render(request, 'accounts/signup.html')
    
    return render(request, 'accounts/signup.html')


def handle_signup_step1(request):
    """Handle first step of signup - validate data and send OTP"""
    try:
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
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'All required fields must be filled.'
                })
            messages.error(request, "All required fields must be filled.")
            return render(request, 'accounts/signup.html', {'form_data': form_data})

        if password != confirm_password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'Passwords do not match.'
                })
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/signup.html', {'form_data': form_data})

        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            error_msg = "Password must be at least 8 characters long and contain letters and numbers."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': error_msg
                })
            messages.error(request, error_msg)
            return render(request, 'accounts/signup.html', {'form_data': form_data})

        # Email validation
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            error_msg = "Please enter a valid email address."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': error_msg
                })
            messages.error(request, error_msg)
            return render(request, 'accounts/signup.html', {'form_data': form_data})

        # Check if email already exists and is verified
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.email_verified:
            error_msg = "Email already exists and is verified."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': error_msg
                })
            messages.error(request, error_msg)
            return render(request, 'accounts/signup.html', {'form_data': form_data})

        # Check username (only if it doesn't belong to unverified user with same email)
        username_user = User.objects.filter(username=username).first()
        if username_user and (username_user.email != email or username_user.email_verified):
            error_msg = "Username already exists."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': error_msg
                })
            messages.error(request, error_msg)
            return render(request, 'accounts/signup.html', {'form_data': form_data})

        # Check phone number (only if it doesn't belong to unverified user with same email)
        phone_user = User.objects.filter(phone_number=phone_number).first()
        if phone_user and (phone_user.email != email or phone_user.email_verified):
            error_msg = "Phone number already exists."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': error_msg
                })
            messages.error(request, error_msg)
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
            
    except Exception as e:
        print(f"[SIGNUP STEP1] Error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'An error occurred during registration. Please try again.'
        })


def handle_signup_step2(request):
    """Handle second step of signup - verify OTP and create user"""
    try:
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
            
        # Double-check if email already exists and is verified
        if User.objects.filter(email=signup_data['email'], email_verified=True).exists():
            return JsonResponse({
                'success': False, 
                'message': 'Email already exists and is verified.'
            })

        # Check if username is taken by another user
        if User.objects.filter(username=signup_data['username']).exclude(email=signup_data['email']).exists():
            return JsonResponse({
                'success': False, 
                'message': 'Username is already taken.'
            })
            
        # Create user
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
                except (ValueError, TypeError):
                    pass
        
        elif signup_data['user_type'] == 'professional':
            if signup_data.get('job_title'):
                user.job_title = signup_data['job_title']
            if signup_data.get('organization'):
                user.organization = signup_data['organization']
            if signup_data.get('experience'):
                try:
                    user.experience = int(signup_data['experience'])
                except (ValueError, TypeError):
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
        print(f"[SIGNUP STEP2] IntegrityError: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Failed to create account. Username, email or phone number might already exist.'
        })

    except Exception as e:
        print(f"[SIGNUP STEP2] Unexpected error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Failed to create account. Please try again.'
        })


@require_http_methods(["POST"])
def resend_otp(request):
    """Resend OTP to email"""
    try:
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return JsonResponse({
                'success': False, 
                'message': 'Session expired. Please start registration again.'
            })
        
        new_otp = generate_otp()
        if send_email_otp(signup_data['email'], new_otp):
            # Update session with new OTP and timestamp
            signup_data['email_otp'] = new_otp
            signup_data['otp_created_at'] = timezone.now().isoformat()
            request.session['signup_data'] = signup_data
            
            return JsonResponse({
                'success': True, 
                'message': 'New OTP sent successfully to your email.'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Failed to send OTP. Please try again.'
            })
            
    except Exception as e:
        print(f"[RESEND OTP] Error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Failed to send OTP. Please try again.'
        })



def login(request):
    if request.method == "POST":
        try:
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            
            if not email or not password:
                messages.error(request, "Please fill in all fields.")
                return render(request, 'accounts/login.html')
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                messages.error(request, "Invalid email or password.")
                return render(request, 'accounts/login.html')
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if hasattr(user, 'email_verified') and not user.email_verified:
                    messages.error(request, "Please verify your email before logging in.")
                    return render(request, 'accounts/login.html')

                auth_login(request, user)
                messages.success(request, f"Welcome back, {getattr(user, 'full_name', user.username)}!")

                if user.user_type == 'recruiter':
                    return redirect('recruiter:recruiter_dashboard')
                else:
                    return redirect('dashboard:home')

            else:
                messages.error(request, "Invalid email or password.")
                return render(request, 'accounts/login.html')

        except Exception as e:
            print(f"[LOGIN ERROR] {str(e)}")
            messages.error(request, "An error occurred during login. Please try again.")
            return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')
# Logout view
@login_required
def logout_user(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')


# Profile view
@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


# Delete account view
@login_required
def delete_account(request):
    if request.method == "POST":
        try:
            user = request.user
            auth_logout(request)
            user.delete()
            messages.success(request, "Your account has been deleted successfully.")
            return redirect('accounts:home')
        except Exception as e:
            print(f"[DELETE ACCOUNT] Error: {str(e)}")
            messages.error(request, "An error occurred while deleting your account.")
            return redirect('accounts:profile')
    
    return redirect('accounts:profile')


def forgot_password(request):
    if request.method == "POST":
        try:
            step = request.POST.get('step', '1')
            
            # Step 1: Email submission
            if step == '1':
                email = request.POST.get('email', '').strip()
                
                if not email:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Please enter your email address.'
                        })
                    messages.error(request, "Please enter your email address.")
                    return render(request, 'accounts/login.html')
                
                # Check if user exists and is verified
                try:
                    user = User.objects.get(email=email, email_verified=True)
                except User.DoesNotExist:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'No verified account found with this email address.'
                        })
                    messages.error(request, "No verified account found with this email address.")
                    return render(request, 'accounts/login.html')
                
                # Generate and send reset OTP
                reset_otp = generate_otp()
                
                if send_password_reset_otp(email, reset_otp):
                    # Store reset data in session
                    request.session['password_reset_data'] = {
                        'email': email,
                        'otp': reset_otp,
                        'otp_created_at': timezone.now().isoformat(),
                    }
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True, 
                            'message': f'Password reset code sent to {email}. Please check your email.',
                            'email': email
                        })
                    messages.success(request, f"Password reset code sent to {email}. Please check your email.")
                    return render(request, 'accounts/login.html', {'email': email})
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Failed to send reset code. Please try again.'
                        })
                    messages.error(request, "Failed to send reset code. Please try again.")
                    return render(request, 'accounts/login.html')
            
            # Step 2: OTP verification
            elif step == '2':
                reset_data = request.session.get('password_reset_data')
                if not reset_data:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Session expired. Please start the password reset process again.'
                        })
                    messages.error(request, "Session expired. Please start over.")
                    return render(request, 'accounts/login.html')
                
                entered_otp = request.POST.get('otp', '').strip()
                
                if not entered_otp:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Please enter the verification code.'
                        })
                    messages.error(request, "Please enter the verification code.")
                    return render(request, 'accounts/login.html')
                
                # Check if OTP is valid
                otp_created_at = datetime.fromisoformat(reset_data['otp_created_at'])
                if not is_otp_valid(otp_created_at):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Verification code has expired. Please request a new one.'
                        })
                    messages.error(request, "Verification code has expired.")
                    return render(request, 'accounts/login.html')
                
                # Check if OTP matches
                if entered_otp != reset_data['otp']:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Invalid verification code. Please try again.'
                        })
                    messages.error(request, "Invalid verification code.")
                    return render(request, 'accounts/login.html')
                
                # OTP is valid, mark it as verified
                reset_data['otp_verified'] = True
                request.session['password_reset_data'] = reset_data
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'message': 'Code verified successfully. Please set your new password.'
                    })
                messages.success(request, "Code verified successfully.")
                return render(request, 'accounts/login.html')
            
            # Step 3: Password reset
            elif step == '3':
                reset_data = request.session.get('password_reset_data')
                if not reset_data or not reset_data.get('otp_verified'):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Session expired or OTP not verified. Please start over.'
                        })
                    messages.error(request, "Session expired. Please start over.")
                    return render(request, 'accounts/login.html')
                
                new_password = request.POST.get('new_password', '').strip()
                confirm_password = request.POST.get('confirm_password', '').strip()
                
                if not new_password or not confirm_password:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Please enter both password fields.'
                        })
                    messages.error(request, "Please enter both password fields.")
                    return render(request, 'accounts/login.html')
                
                if new_password != confirm_password:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Passwords do not match.'
                        })
                    messages.error(request, "Passwords do not match.")
                    return render(request, 'accounts/login.html')
                
                if len(new_password) < 8:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Password must be at least 8 characters long.'
                        })
                    messages.error(request, "Password must be at least 8 characters long.")
                    return render(request, 'accounts/login.html')
                
                try:
                    # Update user password
                    user = User.objects.get(email=reset_data['email'])
                    user.password = make_password(new_password)
                    user.save()
                    
                    # Clear session data
                    if 'password_reset_data' in request.session:
                        del request.session['password_reset_data']
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True, 
                            'message': 'Password reset successfully! You can now login with your new password.',
                            'redirect_url': '/accounts/login/'
                        })
                    messages.success(request, "Password reset successfully! You can now login.")
                    return redirect('accounts:login')
                    
                except User.DoesNotExist:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'User not found. Please start over.'
                        })
                    messages.error(request, "User not found.")
                    return render(request, 'accounts/login.html')
                
        except Exception as e:
            print(f"[FORGOT PASSWORD] Error: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'An error occurred. Please try again.'
                })
            messages.error(request, "An error occurred. Please try again.")
            return render(request, 'accounts/login.html')
    
    return render(request, 'accounts/login.html')


# Resend reset OTP
@require_http_methods(["POST"])
def resend_reset_otp(request):
    """Resend password reset OTP"""
    try:
        reset_data = request.session.get('password_reset_data')
        if not reset_data:
            return JsonResponse({
                'success': False, 
                'message': 'Session expired. Please start the password reset process again.'
            })
        
        new_otp = generate_otp()
        if send_password_reset_otp(reset_data['email'], new_otp):
            # Update session with new OTP and timestamp
            reset_data['otp'] = new_otp
            reset_data['otp_created_at'] = timezone.now().isoformat()
            # Remove verification flag to require re-verification
            reset_data.pop('otp_verified', None)
            request.session['password_reset_data'] = reset_data
            
            return JsonResponse({
                'success': True, 
                'message': 'New password reset code sent successfully to your email.'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Failed to send reset code. Please try again.'
            })
            
    except Exception as e:
        print(f"[RESEND RESET OTP] Error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Failed to send reset code. Please try again.'
        })