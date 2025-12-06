from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse

def assessments(request):
    """Assessment dashboard - static for now"""
    user = request.user
    
    # Static response for all users
    context = {
        'user': user,
        'page_title': 'Skill Assessments',
        'coming_soon': True
    }
    
    if user.is_authenticated:
        if user.user_type == 'student':
            return render(request, 'assessments/assessment_dashboard.html', context)
        elif user.user_type == 'professional':
            return render(request, 'assessments/assessment_dashboard.html', context)
        else:
            return render(request, 'assessments/assessment_dashboard.html', context)
    else:
        # Redirect unauthenticated users to login
        return redirect('/login/?next=/assessments/')