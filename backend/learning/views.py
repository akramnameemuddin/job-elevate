from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, F, Sum
from django.views.decorators.http import require_http_methods
import json

from .models import Course, SkillGap, LearningPath, LearningPathCourse, CourseProgress
from assessments.models import UserSkillProfile, Skill, UserSkillScore, AssessmentAttempt
from recruiter.models import Job


@login_required
def learning_dashboard(request):
    """Main learning dashboard showing paths, skills, and progress"""
    user = request.user

    # ---- Learning Paths (with course counts) ----
    learning_paths = (
        LearningPath.objects.filter(user=user)
        .select_related('skill_gap', 'skill_gap__skill')
        .prefetch_related('courses')
        .annotate(num_courses=Count('learningpathcourse'))
    )

    # Enrich each path with computed completions
    for path in learning_paths:
        lpc_qs = LearningPathCourse.objects.filter(learning_path=path)
        path.total_courses = lpc_qs.count()
        path.completed_courses = lpc_qs.filter(is_completed=True).count()
        path.real_progress = (
            round(path.completed_courses / path.total_courses * 100)
            if path.total_courses > 0 else 0
        )
        path.total_hours = sum(
            lpc.course.duration_hours
            for lpc in lpc_qs.select_related('course')
        )

    # ---- Skill Scores (from assessments) ----
    user_skill_scores = (
        UserSkillScore.objects.filter(user=user)
        .select_related('skill', 'skill__category')
        .order_by('-verified_level')
    )
    verified_skills = user_skill_scores.filter(status='verified')
    claimed_skills = user_skill_scores.filter(status='claimed')

    # ---- Assessment Stats ----
    total_assessments = AssessmentAttempt.objects.filter(user=user, status='completed').count()
    passed_assessments = AssessmentAttempt.objects.filter(user=user, status='completed', passed=True).count()

    # ---- Skill Gaps ----
    skill_gaps_qs = SkillGap.objects.filter(user=user, is_addressed=False).select_related('skill')
    critical_gaps = skill_gaps_qs.filter(priority__in=['critical', 'high']).order_by('-gap_value')[:6]
    total_gaps = skill_gaps_qs.count()

    # ---- Course Progress ----
    in_progress_courses = CourseProgress.objects.filter(
        user=user, status='in_progress'
    ).select_related('course', 'course__skill')[:5]

    completed_courses_count = CourseProgress.objects.filter(user=user, status='completed').count()
    enrolled_count = CourseProgress.objects.filter(user=user).exclude(status='completed').count()

    total_learning_hours = (
        CourseProgress.objects.filter(user=user)
        .aggregate(total=Sum('time_spent_hours'))['total'] or 0
    )

    # ---- Top Skills for Radar ----
    top_skills = list(verified_skills[:8].values_list('skill__name', 'verified_level'))

    context = {
        'learning_paths': learning_paths,
        'in_progress_courses': in_progress_courses,
        'completed_courses_count': completed_courses_count,
        'enrolled_count': enrolled_count,
        'total_learning_hours': total_learning_hours,
        'critical_gaps': critical_gaps,
        'total_gaps': total_gaps,
        'user_skill_scores': user_skill_scores,
        'verified_skills': verified_skills,
        'claimed_skills': claimed_skills,
        'total_assessments': total_assessments,
        'passed_assessments': passed_assessments,
        'total_paths': learning_paths.count(),
        'active_paths': learning_paths.filter(status__in=['not_started', 'in_progress']).count(),
        'top_skills': top_skills,
    }

    return render(request, 'learning/learning_dashboard.html', context)


@login_required
def skill_gaps(request):
    """Show all skill gaps with job matching"""
    user = request.user

    # ── User skills ──
    user_skills = UserSkillScore.objects.filter(
        user=user,
    ).select_related('skill', 'skill__category').order_by('-verified_level')

    verified_skills = user_skills.filter(status='verified')
    total_skills = user_skills.count()

    # ── Skill gaps ──
    all_gaps = SkillGap.objects.filter(user=user).select_related(
        'skill', 'skill__category', 'related_job',
    ).order_by('-priority_score', '-gap_value')

    open_gaps = all_gaps.filter(is_addressed=False)
    addressed_gaps = all_gaps.filter(is_addressed=True)

    # Priority breakdown for chart
    priority_counts = {
        'critical': open_gaps.filter(priority='critical').count(),
        'high': open_gaps.filter(priority='high').count(),
        'moderate': open_gaps.filter(priority='moderate').count(),
        'low': open_gaps.filter(priority='low').count(),
    }
    total_open = open_gaps.count()

    # Total learning hours needed
    total_hours_needed = open_gaps.aggregate(h=Sum('estimated_learning_hours'))['h'] or 0

    # Average gap severity
    avg_severity = open_gaps.aggregate(a=Avg('gap_severity'))['a'] or 0
    avg_severity_pct = round(avg_severity * 100)

    # Skill readiness score: verified_skills avg level vs 10
    avg_verified = verified_skills.aggregate(a=Avg('verified_level'))['a'] or 0
    readiness_pct = round(avg_verified * 10)  # 0-100

    # ── Radar data (top 8 skills: current vs required) ──
    radar_gaps = open_gaps[:8]
    radar_labels = [g.skill.name for g in radar_gaps]
    radar_current = [float(g.current_level) for g in radar_gaps]
    radar_required = [float(g.required_level) for g in radar_gaps]

    # ── Courses recommended per gap ──
    for gap in open_gaps:
        gap.courses = Course.objects.filter(
            skill=gap.skill, is_active=True,
        ).order_by('-rating')[:3]

    # ── Available jobs for comparison ──
    available_jobs = Job.objects.filter(status='Open').distinct()[:50]

    # ── Filter support ──
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        filtered_gaps = open_gaps.filter(priority=priority_filter)
    else:
        filtered_gaps = open_gaps

    context = {
        'user_skills': user_skills,
        'verified_skills': verified_skills,
        'total_skills': total_skills,
        'skill_gaps': filtered_gaps,
        'open_gaps_count': total_open,
        'addressed_count': addressed_gaps.count(),
        'priority_counts': priority_counts,
        'total_hours_needed': total_hours_needed,
        'avg_severity_pct': avg_severity_pct,
        'readiness_pct': readiness_pct,
        'avg_verified': round(avg_verified, 1),
        'radar_labels': json.dumps(radar_labels),
        'radar_current': json.dumps(radar_current),
        'radar_required': json.dumps(radar_required),
        'available_jobs': available_jobs,
        'priority_filter': priority_filter,
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
