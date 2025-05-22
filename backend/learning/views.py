from django.shortcuts import render
from django.shortcuts import render, redirect


# Create your views here.
def learning(request):  
    user = request.user
    if user.is_authenticated:
        if user.user_type == 'student':
            return render(request, 'learning/learning_dashboard.html', {'user': user})
        elif user.user_type == 'professional':
            return render(request, 'learning/learning_dashboard.html', {'user': user})
        elif user.user_type == 'recruiter':
            return render(request, 'learning/recruiter_dashboard.html', {'user': user})
    else:
        return redirect('accounts:login')