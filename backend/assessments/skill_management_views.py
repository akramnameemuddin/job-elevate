"""
Skill management views.
Browse skills, claim skills, skill profile.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Skill, SkillCategory, UserSkillScore
from collections import OrderedDict
import json


@login_required
def browse_skills(request):
    """Browse all available skills with search, filter, and category grouping."""
    skills = Skill.objects.filter(is_active=True).select_related('category')
    categories = SkillCategory.objects.all().order_by('name')

    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        skills = skills.filter(name__icontains=search_query)

    # Category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        skills = skills.filter(category__name=category_filter)

    # Job context (optional — linked from job detail)
    job = None
    required_skills = []
    job_id = request.GET.get('job')
    if job_id:
        try:
            from jobs.models import Job
            from recruiter.models import JobSkillRequirement
            job = Job.objects.get(id=job_id)
            reqs = JobSkillRequirement.objects.filter(job=job).select_related('skill')
            user_scores = {
                s.skill_id: s
                for s in UserSkillScore.objects.filter(user=request.user)
            }
            for req in reqs:
                score = user_scores.get(req.skill_id)
                required_skills.append(type('obj', (object,), {
                    'id': req.skill.id,
                    'name': req.skill.name,
                    'description': req.skill.description,
                    'is_verified': score is not None and score.status == 'verified',
                    'is_claimed': score is not None and score.status == 'claimed',
                    'not_in_db': False,
                })())
        except Exception:
            job = None
            required_skills = []

    # User's scores for badge rendering
    user_scores = {
        s.skill_id: s
        for s in UserSkillScore.objects.filter(user=request.user).select_related('skill')
    }
    verified_skill_ids = {sid for sid, s in user_scores.items() if s.status == 'verified'}
    claimed_skill_ids = {sid for sid, s in user_scores.items() if s.status == 'claimed'}

    # Group by category — annotate each skill
    skills_by_category = OrderedDict()
    for skill in skills.order_by('category__name', 'name'):
        cat_name = skill.category.name if skill.category else 'Uncategorised'
        annotated = type('obj', (object,), {
            'id': skill.id,
            'name': skill.name,
            'description': skill.description,
            'is_verified': skill.id in verified_skill_ids,
            'is_claimed': skill.id in claimed_skill_ids,
        })()
        skills_by_category.setdefault(cat_name, []).append(annotated)

    context = {
        'skills_by_category': skills_by_category,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'job': job,
        'required_skills': required_skills,
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
