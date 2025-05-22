from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

def assessments(request):
    user = request.user
    if user.is_authenticated:
        if user.user_type == 'student':
            return render(request, 'assessments/assessment_dashboard.html', {'user': user})
        elif user.user_type == 'professional':
            return