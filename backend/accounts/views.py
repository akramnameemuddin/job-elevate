import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .models import User


# Homepage
def home(request):
    return render(request, 'accounts/index.html')


# Signup
def signup(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        user_type = request.POST.get('user_type', '').strip()

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/signup.html')

        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            messages.error(request, "Password must be at least 8 characters long and contain letters and numbers.")
            return render(request, 'accounts/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'accounts/signup.html')

        if User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "Phone number already exists.")
            return render(request, 'accounts/signup.html')

        try:
            user = User.objects.create_user(
                full_name=full_name,
                username=username,
                email=email,
                phone_number=phone_number,
                user_type=user_type,
                password=password
            )

            if user_type in ['student']:
                user.university = request.POST.get('university', '').strip()
                user.degree = request.POST.get('degree', '').strip()
                user.graduation_year = request.POST.get('graduation_year', '').strip()

            if user_type == 'professional':
                user.job_title = request.POST.get('job_title', '').strip()
                user.organization = request.POST.get('organization', '').strip()
                user.experience = request.POST.get('experience', '').strip()

            if user_type == 'recruiter':
                user.company_name = request.POST.get('company_name', '').strip()
                user.company_website = request.POST.get('company_website', '').strip()
                user.company_description = request.POST.get('company_description', '').strip()

            user.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('accounts:login')

        except IntegrityError:
            messages.error(request, "Something went wrong. Please try again.")
            return render(request, 'accounts/signup.html')

    return render(request, 'accounts/signup.html')


# Login
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, 'accounts/login.html')

        try:
            user = User.objects.get(email=email)
            auth_user = authenticate(request, username=user.username, password=password)

            if auth_user:
                auth_login(request, auth_user)

                if auth_user.user_type == 'recruiter':
                    return redirect('/recruiter/')  # Use absolute URL path with leading slash
                else:
                    return redirect('dashboard:home')  # General users go here
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
