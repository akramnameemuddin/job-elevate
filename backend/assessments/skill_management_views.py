"""
Skill management views.
Placeholder for compatibility with existing URLs.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Skill, UserSkillScore
import json


@login_required
def browse_skills(request):
    """Browse all available skills"""
    from .models import SkillCategory
    
    skills = Skill.objects.filter(is_active=True).select_related('category')
    
    # Get user's verified skills
    user_scores = UserSkillScore.objects.filter(
        user=request.user
    ).select_related('skill')
    
    verified_skill_ids = set(
        score.skill_id for score in user_scores if score.status == 'verified'
    )
    
    context = {
        'skills': skills,
        'verified_skill_ids': verified_skill_ids,
    }
    
    return render(request, 'assessments/browse_skills.html', context)


@login_required
@require_http_methods(["POST"])
def claim_skill(request):
    """Claim a skill with self-rating"""
    try:
        data = json.loads(request.body)
        skill_id = data.get('skill_id')
        self_rating = float(data.get('self_rating', 5))
        
        skill = get_object_or_404(Skill, id=skill_id, is_active=True)
        
        skill_score, created = UserSkillScore.objects.get_or_create(
            user=request.user,
            skill=skill,
            defaults={
                'self_rated_level': self_rating,
                'status': 'claimed'
            }
        )
        
        if not created:
            skill_score.self_rated_level = self_rating
            skill_score.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Skill {skill.name} claimed! Take an assessment to verify it.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def skill_profile(request):
    """Show user's skill profile"""
    user_scores = UserSkillScore.objects.filter(
        user=request.user
    ).select_related('skill', 'skill__category').order_by('-verified_level')
    
    context = {
        'user_scores': user_scores,
        'verified_count': user_scores.filter(status='verified').count(),
        'total_count': user_scores.count(),
    }
    
    return render(request, 'assessments/skill_profile.html', context)
