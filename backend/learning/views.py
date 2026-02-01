from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.views.decorators.http import require_http_methods
import json

from .models import Course, SkillGap, LearningPath, LearningPathCourse, CourseProgress
from assessments.models import UserSkillProfile, Skill
from recruiter.models import Job


@login_required
def learning_dashboard(request):
    """Main learning dashboard showing paths and progress"""
    # Get user's learning paths
    learning_paths = LearningPath.objects.filter(
        user=request.user
    ).select_related('skill_gap', 'skill_gap__skill').prefetch_related('courses')
    
    # Get in-progress courses
    in_progress_courses = CourseProgress.objects.filter(
        user=request.user,
        status='in_progress'
    ).select_related('course', 'course__skill')[:5]
    
    # Get completed courses count
    completed_count = CourseProgress.objects.filter(
        user=request.user,
        status='completed'
    ).count()
    
    # Get skill gaps
    critical_gaps = SkillGap.objects.filter(
        user=request.user,
        is_addressed=False,
        priority__in=['critical', 'high']
    ).select_related('skill')[:5]
    
    # Get user skills
    skill_profiles = UserSkillProfile.objects.filter(
        user=request.user
    ).select_related('skill')
    
    context = {
        'learning_paths': learning_paths,
        'in_progress_courses': in_progress_courses,
        'completed_count': completed_count,
        'critical_gaps': critical_gaps,
        'skill_profiles': skill_profiles,
        'total_paths': learning_paths.count(),
        'active_paths': learning_paths.filter(status__in=['not_started', 'in_progress']).count(),
    }
    
    return render(request, 'learning/learning_dashboard.html', context)


@login_required
def skill_gaps(request):
    """Show all skill gaps with job matching"""
    # Get user skills
    user_skills = UserSkillProfile.objects.filter(
        user=request.user
    ).select_related('skill', 'skill__category')
    
    # Get skill gaps
    skill_gaps = SkillGap.objects.filter(
        user=request.user
    ).select_related('skill', 'skill__category', 'related_job').order_by('-priority', '-gap_value')
    
    # Get available jobs for gap analysis
    available_jobs = Job.objects.filter(status='Open').distinct()
    
    context = {
        'user_skills': user_skills,
        'skill_gaps': skill_gaps,
        'available_jobs': available_jobs,
    }
    
    return render(request, 'learning/skill_gaps.html', context)


@login_required
@require_http_methods(["POST"])
def analyze_job_gaps(request):
    """Analyze skill gaps for a target job"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            job_id = data.get('job_id')
        else:
            job_id = request.POST.get('job_id')
        
        if not job_id:
            return JsonResponse({'success': False, 'error': 'job_id is required'}, status=400)
        
        job = get_object_or_404(Job, id=job_id)
        
        # Get user's current skills
        user_skills = UserSkillProfile.objects.filter(
            user=request.user
        ).values_list('skill__name', 'verified_level')
        
        user_skill_dict = {skill[0].lower(): skill[1] for skill in user_skills}
        
        # Analyze gaps
        gaps_created = 0
        for required_skill in job.skills:
            # Find matching skill in database
            skill_obj = Skill.objects.filter(name__iexact=required_skill).first()
            
            if skill_obj:
                current_level = user_skill_dict.get(required_skill.lower(), 0)
                required_level = 6.0  # Default required level
                
                if current_level < required_level:
                    SkillGap.objects.update_or_create(
                        user=request.user,
                        skill=skill_obj,
                        target_job_title=job.title,
                        defaults={
                            'current_level': current_level,
                            'required_level': required_level,
                            'is_addressed': False
                        }
                    )
                    gaps_created += 1
        
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': f'Identified {gaps_created} skill gaps for {job.title}',
                'gaps_count': gaps_created
            })
        else:
            # Regular form submission - redirect to skill gaps page
            messages.success(request, f'Identified {gaps_created} skill gaps for {job.title}')
            return redirect('learning:skill_gaps')
        
    except Job.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Job not found'}, status=404)
        messages.error(request, 'Job not found')
        return redirect('learning:skill_gaps')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        messages.error(request, f'Error analyzing gaps: {str(e)}')
        return redirect('learning:skill_gaps')


@login_required
def learning_path_detail(request, path_id):
    """Show detailed learning path"""
    learning_path = get_object_or_404(
        LearningPath,
        id=path_id,
        user=request.user
    )
    
    # Get courses in order with their progress
    path_courses = LearningPathCourse.objects.filter(
        learning_path=learning_path
    ).select_related('course', 'course__skill').order_by('order')
    
    # Get course progress for each course
    course_ids = [pc.course.id for pc in path_courses]
    progress_dict = {
        cp.course_id: cp
        for cp in CourseProgress.objects.filter(user=request.user, course_id__in=course_ids)
    }
    
    # Attach progress and completion status to each path course
    for pc in path_courses:
        pc.course_progress = progress_dict.get(pc.course.id)
        pc.is_completed = pc.course_progress and pc.course_progress.completed if pc.course_progress else False
    
    # Calculate stats
    total_hours = sum(pc.course.duration_hours for pc in path_courses)
    completed_courses = sum(1 for pc in path_courses if pc.is_completed)
    
    # Get targeted skills
    skill_gap = learning_path.skill_gap if hasattr(learning_path, 'skill_gap') else None
    targeted_skills = []
    if skill_gap:
        targeted_skills = [{
            'name': skill_gap.skill.name,
            'category': skill_gap.skill.category,
            'current_level': skill_gap.current_level,
            'target_level': skill_gap.required_level,
        }]
    
    context = {
        'learning_path': learning_path,
        'path_courses': path_courses,
        'total_hours': total_hours,
        'completed_courses': completed_courses,
        'targeted_skills': targeted_skills,
    }
    
    return render(request, 'learning/learning_path_detail.html', context)


@login_required
@require_http_methods(["POST"])
def generate_learning_path(request):
    """Generate learning paths for user's skill gaps"""
    try:
        data = json.loads(request.body) if request.body else {}
        gap_id = data.get('gap_id')
        
        # If specific gap provided, create path for it
        if gap_id:
            gap = get_object_or_404(SkillGap, id=gap_id, user=request.user)
            gaps_to_process = [gap]
        else:
            # Generate paths for all unaddressed critical/high priority gaps
            gaps_to_process = SkillGap.objects.filter(
                user=request.user,
                is_addressed=False
            ).select_related('skill')[:5]  # Limit to top 5 gaps
        
        if not gaps_to_process:
            return JsonResponse({
                'success': False,
                'error': 'No skill gaps found to address'
            }, status=400)
        
        paths_created = 0
        for gap in gaps_to_process:
            # Check if path already exists for this gap
            existing_path = LearningPath.objects.filter(
                user=request.user,
                skill_gap=gap
            ).exists()
            
            if existing_path:
                continue
            
            # Find suitable courses
            courses = Course.objects.filter(
                skill=gap.skill,
                is_active=True
            ).order_by('difficulty_level', '-created_at')[:4]
            
            if not courses:
                continue
            
            # Create learning path
            path_title = f"{gap.skill.name} Development Path"
            
            learning_path = LearningPath.objects.create(
                user=request.user,
                skill_gap=gap,
                title=path_title,
                description=f"Personalized learning path to improve your {gap.skill.name} skills",
                target_skill_level=gap.required_level,
                status='not_started'
            )
            
            # Add courses to path
            for i, course in enumerate(courses, 1):
                LearningPathCourse.objects.create(
                    learning_path=learning_path,
                    course=course,
                    order=i
                )
            
            paths_created += 1
        
        return JsonResponse({
            'success': True,
            'message': f'{paths_created} learning path(s) created successfully!',
            'paths_created': paths_created
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def course_catalog(request):
    """Browse all available courses"""
    skill_filter = request.GET.get('skill')
    difficulty = request.GET.get('difficulty')
    platform = request.GET.get('platform')
    
    courses = Course.objects.filter(is_active=True).select_related('skill', 'skill__category')
    
    if skill_filter:
        courses = courses.filter(skill__id=skill_filter)
    if difficulty:
        courses = courses.filter(difficulty_level=difficulty)
    if platform:
        courses = courses.filter(platform=platform)
    
    # Get user's enrolled courses
    enrolled_course_ids = list(CourseProgress.objects.filter(
        user=request.user
    ).values_list('course_id', flat=True))
    
    # Get filters
    all_skills = Skill.objects.filter(is_active=True).select_related('category')
    platforms = Course.objects.values_list('platform', flat=True).distinct()
    
    context = {
        'courses': courses,
        'all_skills': all_skills,
        'platforms': platforms,
        'enrolled_course_ids': enrolled_course_ids,
    }
    
    return render(request, 'learning/course_catalog.html', context)


@login_required
@require_http_methods(["POST"])
def enroll_course(request):
    """Enroll in a course"""
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        learning_path_id = data.get('learning_path_id')
        
        course = get_object_or_404(Course, id=course_id, is_active=True)
        
        # Check if already enrolled
        existing = CourseProgress.objects.filter(
            user=request.user,
            course=course
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'error': 'Already enrolled in this course'
            }, status=400)
        
        # Create enrollment
        learning_path = None
        if learning_path_id:
            learning_path = LearningPath.objects.filter(
                id=learning_path_id,
                user=request.user
            ).first()
        
        CourseProgress.objects.create(
            user=request.user,
            course=course,
            learning_path=learning_path,
            status='enrolled'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully enrolled in {course.title}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def my_courses(request):
    """Show user's enrolled courses"""
    # Get all course progress
    progress_list = CourseProgress.objects.filter(
        user=request.user
    ).select_related('course', 'course__skill', 'learning_path').order_by('-last_accessed_at')
    
    # Get statistics
    active_courses = progress_list.exclude(status='completed').count()
    completed_courses = progress_list.filter(status='completed').count()
    total_hours = sum([p.time_spent_hours for p in progress_list])
    certificates_earned = progress_list.filter(status='completed', certificate_url__isnull=False).count()
    
    context = {
        'progress_list': progress_list,
        'active_courses': active_courses,
        'completed_courses': completed_courses,
        'total_hours': total_hours,
        'certificates_earned': certificates_earned,
    }
    
    return render(request, 'learning/my_courses.html', context)


@login_required
@require_http_methods(["POST"])
def update_course_progress(request):
    """Update course progress"""
    try:
        data = json.loads(request.body)
        progress_id = data.get('progress_id')
        progress_percentage = data.get('progress_percentage')
        completed = data.get('completed')
        update_access = data.get('update_access', False)
        
        course_progress = get_object_or_404(
            CourseProgress,
            id=progress_id,
            user=request.user
        )
        
        # Update last accessed time if requested
        if update_access:
            course_progress.last_accessed = timezone.now()
            course_progress.save()
            return JsonResponse({
                'success': True,
                'message': 'Access time updated'
            })
        
        # Update progress
        if progress_percentage is not None:
            course_progress.progress_percentage = float(progress_percentage)
        
        if completed is not None:
            course_progress.completed = completed
            if completed:
                course_progress.completed_at = timezone.now()
                course_progress.progress_percentage = 100
        
        course_progress.last_accessed = timezone.now()
        course_progress.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Progress updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
