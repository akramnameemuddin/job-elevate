"""
Skill intelligence and analytics views.
Placeholder for compatibility with existing URLs.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def skill_intelligence_placeholder(request):
    """Placeholder view"""
    return render(request, 'assessments/coming_soon.html', {
        'feature': 'Skill Intelligence'
    })
