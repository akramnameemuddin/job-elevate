from django.shortcuts import render
from django.shortcuts import render, redirect


# Create your views here.
def community(request):
    user = request.user
    if user.is_authenticated:
        if user.user_type == 'student':
            return render(request, 'community/community_dashboard.html', {'user': user})
        elif user.user_type == 'professional':
            return render(request, 'community/community_dashboard.html', {'user': user})
        elif user.user_type == 'recruiter':
            return render(request, 'community/recruiter_dashboard.html', {'user': user})
    else:
        return redirect('accounts:login')