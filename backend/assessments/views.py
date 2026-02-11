"""
Production-Ready Assessment Views
Trigger: User clicks "Fill Gap" button from job detail page
Flow: Job Detail → Start Assessment → Take → Submit → Update Score → Redirect
"""
import json
import logging
import random
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import (
    Skill, SkillCategory, QuestionBank, AssessmentAttempt, 
    UserAnswer, UserSkillScore
)
from .ai_service import question_generator
from recruiter.models import Job, JobSkillRequirement

logger = logging.getLogger(__name__)


@login_required
def start_assessment_from_job(request, job_id, skill_id):
    """
    ENTRY POINT: Start assessment for a specific skill gap from job detail page.
    
    Workflow:
    1. Check if user needs this skill for the job
    2. Fetch questions from QuestionBank
    3. Generate via AI ONLY if QuestionBank is empty
    4. Shuffle questions and options (anti-cheating)
    5. Create AssessmentAttempt
    6. Render assessment page
    """
    job = get_object_or_404(Job, id=job_id, status='Open')
    skill = get_object_or_404(Skill, id=skill_id, is_active=True)
    
    # Verify this skill is required for the job
    try:
        job_requirement = JobSkillRequirement.objects.get(job=job, skill=skill)
    except JobSkillRequirement.DoesNotExist:
        messages.error(request, f"Skill {skill.name} is not required for this job.")
        return redirect('jobs:job_detail', job_id=job.id)
    
    # Check for existing in-progress attempt
    existing_attempt = AssessmentAttempt.objects.filter(
        user=request.user,
        skill=skill,
        status='in_progress'
    ).first()
    
    if existing_attempt:
        messages.info(request, f"Resuming your {skill.name} assessment...")
        return redirect('assessments:take_assessment', attempt_id=existing_attempt.id)
    
    # Fetch or generate questions
    questions = _get_or_generate_questions(skill)
    
    if not questions:
        messages.error(
            request,
            f"Unable to generate assessment for {skill.name}. Please try again later."
        )
        return redirect('jobs:job_detail', job_id=job.id)
    
    # Select questions (mix of difficulties)
    selected_questions = _select_balanced_questions(questions)
    
    if len(selected_questions) < 20:
        logger.warning(
            f"Only {len(selected_questions)} questions available for {skill.name}. "
            f"Recommended: 20 questions (8 easy, 6 medium, 6 hard)."
        )
    
    # Create new attempt
    attempt = _create_assessment_attempt(request.user, skill, selected_questions, job)
    
    messages.success(
        request,
        f"Assessment started! {len(selected_questions)} questions on {skill.name}."
    )
    return redirect('assessments:take_assessment', attempt_id=attempt.id)


@login_required
def start_assessment_direct(request, skill_id):
    """
    Alternative entry point: Start assessment directly (not from job).
    Used for skill diagnostic dashboard.
    """
    skill = get_object_or_404(Skill, id=skill_id, is_active=True)
    
    # Check for existing in-progress attempt
    existing_attempt = AssessmentAttempt.objects.filter(
        user=request.user,
        skill=skill,
        status='in_progress'
    ).first()
    
    if existing_attempt:
        messages.info(request, f"Resuming your {skill.name} assessment...")
        return redirect('assessments:take_assessment', attempt_id=existing_attempt.id)
    
    # Fetch or generate questions
    questions = _get_or_generate_questions(skill)
    
    if not questions:
        messages.error(
            request,
            f"Unable to generate assessment for {skill.name}. Please try again later."
        )
        return redirect('assessments:skill_intake_dashboard')
    
    # Select questions
    selected_questions = _select_balanced_questions(questions)
    
    # Create new attempt
    attempt = _create_assessment_attempt(request.user, skill, selected_questions)
    
    messages.success(
        request,
        f"Assessment started! {len(selected_questions)} questions on {skill.name}."
    )
    return redirect('assessments:take_assessment', attempt_id=attempt.id)


@login_required
def take_assessment(request, attempt_id):
    """
    Display assessment questions with shuffled options.
    NEVER sends correct answers to frontend.
    """
    attempt = get_object_or_404(
        AssessmentAttempt,
        id=attempt_id,
        user=request.user,
        status='in_progress'
    )
    
    # Get questions for this attempt
    question_ids = attempt.question_ids
    
    # If question_ids is empty, regenerate questions
    if not question_ids:
        logger.warning(f"Attempt {attempt_id} has no questions. Regenerating...")
        questions_queryset = _get_or_generate_questions(attempt.skill)
        if not questions_queryset.exists():
            messages.error(request, f"No questions available for {attempt.skill.name}. Please try again.")
            return redirect('assessments:skill_intake_dashboard')
        
        selected_questions = _select_balanced_questions(questions_queryset)
        
        # Update attempt with questions
        attempt.question_ids = [q.id for q in selected_questions]
        attempt.max_score = sum(q.points for q in selected_questions)
        
        # Shuffle options for each question
        shuffled_options = {}
        for question in selected_questions:
            options = question.options.copy()
            random.shuffle(options)
            shuffled_options[str(question.id)] = options
        attempt.shuffled_options = shuffled_options
        attempt.save()
        
        question_ids = attempt.question_ids
    
    questions = QuestionBank.objects.filter(id__in=question_ids).order_by('?')
    
    # Prepare questions with shuffled options
    questions_data = []
    for question in questions:
        # Get shuffled options for this question (stored in attempt)
        shuffled_options = attempt.shuffled_options.get(str(question.id), question.options)
        
        questions_data.append({
            'id': question.id,
            'question_text': question.question_text,
            'options': shuffled_options,  # SHUFFLED, correct answer hidden
            'difficulty': question.difficulty,
            'points': question.points,
            'question_type': 'mcq',  # Add question type for template
        })
    
    # Get user's existing answers
    answered_questions = set(
        UserAnswer.objects.filter(attempt=attempt)
        .values_list('question_bank_id', flat=True)
    )
    
    # Calculate time remaining in seconds
    elapsed_time = (timezone.now() - attempt.started_at).total_seconds()
    duration_seconds = attempt.assessment.duration_minutes * 60
    time_remaining = max(0, int(duration_seconds - elapsed_time))
    
    context = {
        'attempt': attempt,
        'skill': attempt.skill,
        'questions': questions_data,
        'total_questions': len(questions_data),
        'answered_count': len(answered_questions),
        'max_score': attempt.max_score,
        'time_remaining': time_remaining,
    }
    
    return render(request, 'assessments/take_assessment.html', context)


@login_required
@require_http_methods(["POST"])
def submit_answer(request, attempt_id):
    """
    Save user's answer for a single question.
    Backend validates correctness (NEVER trust frontend).
    """
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        selected_answer = data.get('selected_answer')
        
        # Validate that answer is provided
        if not selected_answer:
            return JsonResponse(
                {'success': False, 'error': 'No answer provided'},
                status=400
            )
        
        attempt = get_object_or_404(
            AssessmentAttempt,
            id=attempt_id,
            user=request.user,
            status='in_progress'
        )
        
        question = get_object_or_404(QuestionBank, id=question_id)
        
        # Check if answer already exists
        user_answer, created = UserAnswer.objects.get_or_create(
            attempt=attempt,
            question_bank=question,
            defaults={
                'selected_answer': selected_answer,
                'user_answer': {'answer': selected_answer},  # JSON field
            }
        )
        
        if not created:
            # Update existing answer
            user_answer.selected_answer = selected_answer
            user_answer.user_answer = {'answer': selected_answer}
        
        # SERVER-SIDE VALIDATION: Check if answer is correct
        is_correct = (selected_answer == question.correct_answer)
        user_answer.is_correct = is_correct
        user_answer.points_earned = question.points if is_correct else 0
        user_answer.save()
        
        # Update question statistics
        question.times_used += 1
        if is_correct:
            question.times_correct += 1
        else:
            question.times_incorrect += 1
        question.save()
        
        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'points_earned': user_answer.points_earned,
        })
    
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def submit_assessment(request, attempt_id):
    """
    Complete assessment and calculate final score.
    Update UserSkillScore with verified proficiency level.
    Redirect back to job detail page (if came from job).
    """
    attempt = get_object_or_404(
        AssessmentAttempt,
        id=attempt_id,
        user=request.user,
        status='in_progress'
    )
    
    # Retry logic for database locks (SQLite issue with concurrent writes)
    max_retries = 3
    retry_delay = 0.5  # Start with 500ms
    skill_score = None  # Initialize to avoid UnboundLocalError
    
    for attempt_num in range(max_retries):
        try:
            with transaction.atomic():
                # Calculate final score
                user_answers = UserAnswer.objects.filter(attempt=attempt)
                total_score = sum(answer.points_earned for answer in user_answers)
                
                # Update attempt
                attempt.score = total_score
                attempt.total_score = total_score  # Backward compatibility
                attempt.completed_at = timezone.now()
                attempt.status = 'completed'
                attempt.calculate_percentage()
                
                # Update proficiency level and passed status (backward compatibility)
                attempt.proficiency_level = round((attempt.percentage / 100) * 10, 1)
                attempt.passed = attempt.percentage >= 60
                
                # Calculate time spent
                time_delta = attempt.completed_at - attempt.started_at
                attempt.time_spent_seconds = int(time_delta.total_seconds())
                attempt.save()
                
                # Update or create UserSkillScore
                skill_score, created = UserSkillScore.objects.get_or_create(
                    user=request.user,
                    skill=attempt.skill,
                    defaults={
                        'verified_level': 0,
                    }
                )
                
                # Update with new assessment results
                skill_score.update_from_attempt(attempt)
                
                # Auto-add passed skill to user profile
                if attempt.passed:
                    user = request.user
                    # Get current technical skills (CSV string)
                    current_skills = user.get_skills_list() if hasattr(user, 'get_skills_list') else []
                    skill_name = attempt.skill.name.strip()
                    
                    # Add skill if not already present (case-insensitive check)
                    skill_exists = any(s.lower() == skill_name.lower() for s in current_skills)
                    
                    if not skill_exists:
                        current_skills.append(skill_name)
                        # Update technical_skills field (CSV string)
                        user.technical_skills = ','.join(current_skills)
                        user.save(update_fields=['technical_skills'])
                        logger.info(f"✓ Auto-added '{skill_name}' to {user.username}'s profile")
            
            # Success - break out of retry loop
            break
            
        except Exception as e:
            if 'database is locked' in str(e) and attempt_num < max_retries - 1:
                logger.warning(f"Database locked, retrying in {retry_delay}s... (attempt {attempt_num + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                # Final attempt failed or non-lock error
                logger.error(f"Failed to submit assessment: {str(e)}")
                messages.error(request, "Error submitting assessment. Please try again.")
                return redirect('assessments:take_assessment', attempt_id=attempt.id)
    
    # Log result (only if skill_score was successfully created)
    if skill_score:
        logger.info(
            f"Assessment completed: {request.user.username} - {attempt.skill.name} - "
            f"{attempt.percentage}% ({attempt.score}/{attempt.max_score}) - "
            f"Proficiency: {skill_score.verified_level}/10"
        )
    
    # Determine redirect target
    redirect_url = request.POST.get('redirect_to')
    if redirect_url and 'job_detail' in redirect_url:
        messages.success(
            request,
            f"Assessment completed! Your {attempt.skill.name} proficiency is now "
            f"{skill_score.verified_level}/10. Check your updated match score below."
        )
        return redirect(redirect_url)
    
    return redirect('assessments:assessment_result', attempt_id=attempt.id)


@login_required
def assessment_result(request, attempt_id):
    """
    Display assessment results with detailed breakdown.
    """
    attempt = get_object_or_404(
        AssessmentAttempt,
        id=attempt_id,
        user=request.user
    )
    
    # If not completed, show warning but still display results
    if attempt.status != 'completed':
        messages.warning(
            request,
            "Assessment not fully completed. Showing results based on answered questions."
        )
    
    # Get all answers with question details
    user_answers = UserAnswer.objects.filter(attempt=attempt).select_related('question_bank')
    
    # Calculate statistics
    correct_count = sum(1 for answer in user_answers if answer.is_correct)
    incorrect_count = len(user_answers) - correct_count
    total_count = len(user_answers)
    
    # Get updated skill score
    try:
        skill_score = UserSkillScore.objects.get(user=request.user, skill=attempt.skill)
        proficiency_level = skill_score.verified_level
    except UserSkillScore.DoesNotExist:
        skill_score = None
        proficiency_level = 0
    
    # Calculate grade based on percentage
    percentage = attempt.percentage
    if percentage >= 90:
        grade = 'A'
    elif percentage >= 80:
        grade = 'B'
    elif percentage >= 70:
        grade = 'C'
    elif percentage >= 60:
        grade = 'D'
    else:
        grade = 'F'
    
    # Calculate difficulty breakdown
    difficulty_stats = {'easy': [], 'medium': [], 'hard': []}
    for answer in user_answers:
        if answer.question_bank:
            difficulty = answer.question_bank.difficulty
            difficulty_stats[difficulty].append(answer.is_correct)
    
    difficulty_breakdown = []
    difficulty_config = {
        'easy': {'name': 'Easy Questions', 'icon': 'bx-smile', 'color': 'success', 'description': 'Basic concepts'},
        'medium': {'name': 'Medium Questions', 'icon': 'bx-meh', 'color': 'warning', 'description': 'Intermediate skills'},
        'hard': {'name': 'Hard Questions', 'icon': 'bx-tired', 'color': 'danger', 'description': 'Advanced topics'}
    }
    
    for difficulty, answers in difficulty_stats.items():
        if answers:
            config = difficulty_config.get(difficulty, {})
            correct = sum(answers)
            total = len(answers)
            percentage_val = round((correct / total * 100) if total > 0 else 0, 1)
            difficulty_breakdown.append({
                'name': config.get('name', difficulty.title()),
                'icon': config.get('icon', 'bx-question-mark'),
                'color': config.get('color', 'info'),
                'description': config.get('description', ''),
                'correct': correct,
                'total': total,
                'percentage': percentage_val
            })
    
    # Calculate time spent
    time_spent_minutes = round(attempt.time_spent_seconds / 60, 1) if attempt.time_spent_seconds else 0
    
    # Calculate score circle dasharray for SVG animation
    circumference = 2 * 3.14159 * 50  # radius = 50
    score_dasharray = f"{(percentage / 100) * circumference}, {circumference}"
    
    # Check cooldown status
    in_cooldown = False
    cooldown_hours = 0
    if not attempt.is_passing():
        last_attempts = AssessmentAttempt.objects.filter(
            user=request.user,
            skill=attempt.skill,
            status='completed'
        ).order_by('-completed_at')[:2]
        
        if len(last_attempts) >= 2:
            time_since_last = timezone.now() - last_attempts[0].completed_at
            cooldown_hours = 12 - (time_since_last.total_seconds() / 3600)
            in_cooldown = cooldown_hours > 0
    
    # Get learning path if failed
    learning_path = None
    if not attempt.is_passing():
        from learning.models import LearningPath
        learning_path = LearningPath.objects.filter(
            user=request.user,
            skill_gap__skill=attempt.skill
        ).order_by('-created_at').first()
    
    # Get matching jobs
    matching_jobs = []
    if attempt.is_passing():
        try:
            from recruiter.models import JobSkillRequirement
            job_reqs = JobSkillRequirement.objects.filter(
                skill=attempt.skill
            ).select_related('job')[:5]
            
            for req in job_reqs:
                if req.required_proficiency <= proficiency_level:
                    matching_jobs.append({
                        'job': req.job,
                        'match_percentage': round(min(100, (proficiency_level / req.required_proficiency) * 100), 0)
                    })
        except Exception as e:
            logger.warning(f"Could not fetch matching jobs: {str(e)}")
            matching_jobs = []
    
    context = {
        'attempt': attempt,
        'skill': attempt.skill,
        'skill_name': attempt.skill.name,
        'skill_score': skill_score,
        'user_answers': user_answers,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'total_count': total_count,
        'passed': attempt.is_passing(),
        'percentage': round(percentage, 1),
        'grade': grade,
        'proficiency_level': round(proficiency_level, 1),
        'difficulty_breakdown': difficulty_breakdown,
        'time_spent_minutes': time_spent_minutes,
        'score_dasharray': score_dasharray,
        'in_cooldown': in_cooldown,
        'cooldown_hours': round(cooldown_hours, 1),
        'learning_path': learning_path,
        'matching_jobs': matching_jobs,
    }
    
    return render(request, 'assessments/assessment_results.html', context)


# ================== HELPER FUNCTIONS ==================

def _get_or_generate_questions(skill):
    """
    NEW 100-QUESTION SYSTEM
    
    Strategy:
    - First 5 users per skill: Generate 20 questions each and store (builds to 100)
    - User 6+: Randomly select 20 from the 100-question bank
    - Questions tagged with proficiency levels for skill gap analysis
    
    Returns: QuerySet of QuestionBank objects (20 questions)
    """
    from .ai_service import get_questions_for_assessment
    
    # Use smart allocation system
    questions = get_questions_for_assessment(skill)
    
    if not questions or questions.count() == 0:
        logger.error(f"Failed to get questions for {skill.name}")
        return None
    
    logger.info(f"✓ Allocated {questions.count()} questions for {skill.name} (Skill has {skill.question_count}/100)")
    return questions


def _create_template_questions_for_difficulty(skill, difficulty, count):
    """
    Create template questions for a specific difficulty level.
    Used as fallback when AI generation fails.
    """
    templates = {
        'easy': [
            {
                'question_text': f'What is the primary purpose of {skill.name}?',
                'options': ['Software development', 'Gaming', 'Entertainment', 'Education'],
                'correct_answer': 'Software development',
                'difficulty': 'easy',
                'explanation': f'{skill.name} is primarily used in software development.'
            },
            {
                'question_text': f'Which field commonly uses {skill.name}?',
                'options': ['Technology', 'Agriculture', 'Fashion', 'Sports'],
                'correct_answer': 'Technology',
                'difficulty': 'easy',
                'explanation': f'{skill.name} is commonly used in technology.'
            },
        ],
        'medium': [
            {
                'question_text': f'What is a practical application of {skill.name}?',
                'options': ['Building software solutions', 'Cooking', 'Painting', 'Dancing'],
                'correct_answer': 'Building software solutions',
                'difficulty': 'medium',
                'explanation': f'{skill.name} is used to build software solutions.'
            },
            {
                'question_text': f'How is {skill.name} typically learned?',
                'options': ['Practice and study', 'Watching TV', 'Sleeping', 'Guessing'],
                'correct_answer': 'Practice and study',
                'difficulty': 'medium',
                'explanation': f'{skill.name} requires practice and study to master.'
            },
        ],
        'hard': [
            {
                'question_text': f'What distinguishes an expert in {skill.name}?',
                'options': ['Deep knowledge and problem-solving ability', 'Years only', 'Certification only', 'Luck'],
                'correct_answer': 'Deep knowledge and problem-solving ability',
                'difficulty': 'hard',
                'explanation': 'Experts have comprehensive understanding and can solve complex problems.'
            },
            {
                'question_text': f'How do professionals stay current with {skill.name}?',
                'options': ['Continuous learning and practice', 'Never updating', 'Only reading', 'Ignoring changes'],
                'correct_answer': 'Continuous learning and practice',
                'difficulty': 'hard',
                'explanation': 'Staying current requires ongoing effort and practice.'
            },
        ]
    }
    
    # Get templates for this difficulty and extend if needed
    base_templates = templates.get(difficulty, templates['easy'])
    result = []
    
    for i in range(count):
        # Cycle through templates if we need more than available
        template = base_templates[i % len(base_templates)].copy()
        # Add variation to question text if repeating
        if i >= len(base_templates):
            template['question_text'] = f"Question {i+1}: {template['question_text']}"
        result.append(template)
    
    return result


def _generate_fallback_questions(skill):
    """
    Generate basic fallback questions when AI is unavailable and no templates exist.
    Creates 14 simple questions to allow assessment to proceed.
    These are basic but functional - better than nothing!
    """
    logger.info(f"Creating fallback questions for {skill.name}")
    
    fallback_data = [
        # 6 Easy questions
        {
            'question': f'What is {skill.name} primarily used for?',
            'options': ['Professional software development', 'Gaming', 'Word processing', 'Email'],
            'correct_answer': 'Professional software development',
            'difficulty': 'easy',
            'points': 5
        },
        {
            'question': f'Which category best describes {skill.name}?',
            'options': ['Technical skill', 'Soft skill', 'Management skill', 'Sales skill'],
            'correct_answer': 'Technical skill',
            'difficulty': 'easy',
            'points': 5
        },
        {
            'question': f'Is {skill.name} relevant in modern software development?',
            'options': ['Yes, widely used', 'No, obsolete', 'Only in legacy systems', 'Not applicable'],
            'correct_answer': 'Yes, widely used',
            'difficulty': 'easy',
            'points': 5
        },
        {
            'question': f'What type of projects typically require {skill.name}?',
            'options': ['Software/Technical projects', 'Art projects', 'Sports projects', 'Music projects'],
            'correct_answer': 'Software/Technical projects',
            'difficulty': 'easy',
            'points': 5
        },
        {
            'question': f'Which industry commonly requires {skill.name} skills?',
            'options': ['Technology/IT industry', 'Food industry', 'Fashion industry', 'Agriculture'],
            'correct_answer': 'Technology/IT industry',
            'difficulty': 'easy',
            'points': 5
        },
        {
            'question': f'Learning {skill.name} is beneficial for which career?',
            'options': ['Software development career', 'Chef career', 'Teacher career', 'Driver career'],
            'correct_answer': 'Software development career',
            'difficulty': 'easy',
            'points': 5
        },
        
        # 4 Medium questions
        {
            'question': f'What level of expertise is needed for {skill.name}?',
            'options': ['Ranges from beginner to expert', 'Only experts can use it', 'No expertise needed', 'Deprecated technology'],
            'correct_answer': 'Ranges from beginner to expert',
            'difficulty': 'medium',
            'points': 10
        },
        {
            'question': f'How would you rate the importance of {skill.name} in your field?',
            'options': ['Very important for relevant roles', 'Somewhat important', 'Not important', 'Unknown'],
            'correct_answer': 'Very important for relevant roles',
            'difficulty': 'medium',
            'points': 10
        },
        {
            'question': f'What is the best way to learn {skill.name}?',
            'options': ['Hands-on practice and projects', 'Only reading', 'Only watching videos', 'No learning needed'],
            'correct_answer': 'Hands-on practice and projects',
            'difficulty': 'medium',
            'points': 10
        },
        {
            'question': f'In a professional setting, {skill.name} is used for:',
            'options': ['Building and maintaining technical solutions', 'Personal entertainment', 'Decoration', 'Cooking'],
            'correct_answer': 'Building and maintaining technical solutions',
            'difficulty': 'medium',
            'points': 10
        },
        
        # 4 Hard questions
        {
            'question': f'What distinguishes an expert in {skill.name} from a beginner?',
            'options': ['Deep understanding, problem-solving ability, and real-world experience', 'Just reading books', 'Memorizing syntax', 'Knowing shortcuts'],
            'correct_answer': 'Deep understanding, problem-solving ability, and real-world experience',
            'difficulty': 'hard',
            'points': 15
        },
        {
            'question': f'How does {skill.name} integrate with other technologies?',
            'options': ['Often works with complementary tools and frameworks', 'Works completely isolated', 'Cannot integrate', 'Replaces all other tools'],
            'correct_answer': 'Often works with complementary tools and frameworks',
            'difficulty': 'hard',
            'points': 15
        },
        {
            'question': f'What is the career growth potential for {skill.name} professionals?',
            'options': ['Strong demand and growth opportunities', 'Limited opportunities', 'Declining field', 'No career path'],
            'correct_answer': 'Strong demand and growth opportunities',
            'difficulty': 'hard',
            'points': 15
        },
        {
            'question': f'Which best practices apply when working with {skill.name}?',
            'options': ['Code quality, testing, documentation, and collaboration', 'Work alone always', 'Never document', 'Avoid testing'],
            'correct_answer': 'Code quality, testing, documentation, and collaboration',
            'difficulty': 'hard',
            'points': 15
        },
    ]
    
    # Create QuestionBank entries
    created_count = 0
    for q_data in fallback_data:
        try:
            QuestionBank.objects.create(
                skill=skill,
                question_text=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data['correct_answer'],
                difficulty=q_data['difficulty'],
                points=q_data['points'],
                explanation=f'Fallback question for {skill.name} - consider adding specific questions via admin or populate command',
                created_by_ai=False
            )
            created_count += 1
        except Exception as e:
            logger.error(f"Error creating fallback question: {e}")
            continue
    
    logger.info(f"✓ Created {created_count} fallback questions for {skill.name}")
    return created_count


def _generate_batch_for_skill(skill, count=20, required=False):
    """
    Generate a batch of questions for a skill.
    
    Args:
        skill: Skill object
        count: Number of questions to generate (default: 20)
        required: If True, blocks until generation completes. If False, attempts but doesn't block.
    
    Returns: True if successful, False otherwise
    """
    try:
        # Calculate difficulty distribution for this batch
        # 40% easy, 30% medium, 30% hard
        easy_count = int(count * 0.4)  # 8 questions
        medium_count = int(count * 0.3)  # 6 questions
        hard_count = count - easy_count - medium_count  # 6 questions
        
        generated_questions = []
        
        # Generate for each difficulty level with retry and fallback
        for difficulty, batch_count in [('easy', easy_count), ('medium', medium_count), ('hard', hard_count)]:
            if batch_count == 0:
                continue
            
            # Try AI generation with retries
            max_retries = 2
            questions_data = None
            
            for retry in range(max_retries):
                try:
                    questions_data = question_generator.generate_questions(
                        skill_name=skill.name,
                        skill_description=skill.description,
                        difficulty=difficulty,
                        count=batch_count
                    )
                    
                    if questions_data:
                        break  # Success, exit retry loop
                    else:
                        logger.warning(f"Attempt {retry + 1}/{max_retries}: No {difficulty} questions generated for {skill.name}")
                        if retry < max_retries - 1:
                            time.sleep(2)  # Wait before retry
                        
                except Exception as e:
                    logger.error(f"Attempt {retry + 1}/{max_retries}: Error generating {difficulty} questions for {skill.name}: {str(e)}")
                    if retry < max_retries - 1:
                        time.sleep(2)
                    else:
                        # Final retry failed, use template questions
                        logger.warning(f"All AI attempts failed for {difficulty} questions, using templates")
                        questions_data = _create_template_questions_for_difficulty(skill, difficulty, batch_count)
            
            # Store generated or template questions
            if questions_data:
                for q_data in questions_data:
                    # Map points based on difficulty
                    points = {'easy': 5, 'medium': 10, 'hard': 15}.get(difficulty, 10)
                    
                    question = QuestionBank.objects.create(
                        skill=skill,
                        question_text=q_data.get('question_text', q_data.get('question', '')),
                        options=q_data['options'],
                        correct_answer=q_data['correct_answer'],
                        difficulty=difficulty,
                        points=points,
                        explanation=q_data.get('explanation', ''),
                    )
                    generated_questions.append(question)
                
                logger.info(f"✓ Stored {len(questions_data)} {difficulty} questions for {skill.name}")
            else:
                logger.error(f"❌ Failed to generate {difficulty} questions for {skill.name}")
                if required and difficulty == 'easy':
                    # If easy questions fail and it's required, propagate error
                    raise Exception(f"Failed to generate required {difficulty} questions")
        
        if generated_questions:
            logger.info(f"Successfully generated {len(generated_questions)} questions for {skill.name}")
            return True
        else:
            logger.warning(f"No questions generated for {skill.name}")
            return False
            
    except Exception as e:
        logger.error(f"Batch generation failed for {skill.name}: {str(e)}")
        return False


def _select_balanced_questions(questions_queryset, total=20):
    """
    Select a balanced mix of questions by difficulty.
    Distribution: 40% easy (8), 30% medium (6), 30% hard (6)
    """
    # Convert to list if it's a sliced queryset to avoid filtering errors
    if hasattr(questions_queryset, '_result_cache') or isinstance(questions_queryset, list):
        # Already evaluated or is a list
        questions_list = list(questions_queryset) if not isinstance(questions_queryset, list) else questions_queryset
        
        # Separate by difficulty
        easy = [q for q in questions_list if q.difficulty == 'easy'][:8]
        medium = [q for q in questions_list if q.difficulty == 'medium'][:6]
        hard = [q for q in questions_list if q.difficulty == 'hard'][:6]
        
        selected = easy + medium + hard
        
        # Fill remaining if needed
        if len(selected) < total:
            remaining_needed = total - len(selected)
            used_ids = {q.id for q in selected}
            remaining = [q for q in questions_list if q.id not in used_ids][:remaining_needed]
            selected.extend(remaining)
    else:
        # It's an unevaluated queryset - use database filtering
        easy = list(questions_queryset.filter(difficulty='easy').order_by('?')[:8])
        medium = list(questions_queryset.filter(difficulty='medium').order_by('?')[:6])
        hard = list(questions_queryset.filter(difficulty='hard').order_by('?')[:6])
        
        # Combine and shuffle
        selected = easy + medium + hard
        
        # If not enough questions, fill with random ones
        if len(selected) < total:
            remaining_needed = total - len(selected)
            remaining = list(questions_queryset.exclude(
                id__in=[q.id for q in selected]
            ).order_by('?')[:remaining_needed])
            selected.extend(remaining)
    
    random.shuffle(selected)
    return selected[:total]


def _create_assessment_attempt(user, skill, questions, job=None):
    """
    Create new AssessmentAttempt with shuffled options (anti-cheating).
    """
    question_ids = [q.id for q in questions]
    max_score = sum(q.points for q in questions)
    
    # Shuffle options for each question (anti-cheating)
    shuffled_options = {}
    for question in questions:
        options = question.options.copy()
        random.shuffle(options)
        shuffled_options[str(question.id)] = options
    
    # Create a dummy assessment for backward compatibility
    # (database requires assessment_id to be NOT NULL)
    from .models import Assessment
    assessment, _ = Assessment.objects.get_or_create(
        title=f"{skill.name} Assessment",
        skill=skill,
        defaults={
            'description': f'Auto-generated assessment for {skill.name}',
            'difficulty_level': 'mixed',
            'is_active': True,
        }
    )
    
    attempt = AssessmentAttempt.objects.create(
        user=user,
        skill=skill,
        assessment=assessment,
        question_ids=question_ids,
        selected_question_ids=json.dumps(question_ids),  # For backward compatibility
        shuffled_options=shuffled_options,
        max_score=max_score,
        total_score=0,  # Will be updated when completed
        score=0,
        percentage=0,
        proficiency_level=0,
        passed=False,
        status='in_progress',
        started_at=timezone.now(),
        time_spent_seconds=0,
    )
    
    return attempt


@login_required
def skill_intake_dashboard(request):
    """
    Skill Intake Dashboard - Landing page for direct assessment access.
    Shows all available skills organized by category with gap analysis.
    Users can browse and start assessments for any skill.
    """
    from .models import SkillCategory
    from recruiter.models import JobSkillRequirement
    from django.db.models import Count, Avg, Q
    
    # Get all categories with their active skills
    categories = SkillCategory.objects.all().prefetch_related('skills')
    
    # Get user's skill scores for marking completed skills
    user_skill_scores = UserSkillScore.objects.filter(
        user=request.user
    ).select_related('skill', 'skill__category')
    
    # Get verified skills only
    verified_skills = user_skill_scores.filter(status='verified')
    
    # Calculate statistics
    total_skills = Skill.objects.filter(is_active=True).count()
    verified_count = verified_skills.count()
    completion_percentage = round((verified_count / total_skills * 100) if total_skills > 0 else 0, 1)
    avg_proficiency = round(verified_skills.aggregate(Avg('verified_level'))['verified_level__avg'] or 0, 1)
    
    # Organize skills by category with completion status
    skills_by_category = {}
    
    # Prepare category progress data
    category_progress = []
    for category in categories:
        active_skills = category.skills.filter(is_active=True)
        user_verified_in_category = verified_skills.filter(skill__category=category).count()
        total_in_category = active_skills.count()
        
        if total_in_category > 0:
            category_progress.append({
                'name': category.name,
                'total_skills': total_in_category,
                'user_verified': user_verified_in_category,
                'percentage': round((user_verified_in_category / total_in_category * 100), 1)
            })
        
        # Build skills list for this category
        category_skills = []
        for skill in active_skills:
            score = user_skill_scores.filter(skill=skill).first()
            
            skill_data = {
                'id': skill.id,
                'name': skill.name,
                'description': skill.description,
                'category': category.name,
                'verified_level': score.verified_level if score else 0,
                'status': score.status if score else 'not_started',
                'last_assessment_date': score.last_assessment_date if score else None,
                'is_verified': score and score.status == 'verified',
            }
            
            category_skills.append(skill_data)
        
        if category_skills:
            skills_by_category[category.name] = category_skills
    
    # Get skill gaps - skills in high demand but user doesn't have OR is below required
    user_skill_map = {s.skill_id: s for s in user_skill_scores}
    user_skill_ids = set(user_skill_map.keys())
    skill_gaps = []
    
    try:
        # All skills required by at least one job
        all_required = JobSkillRequirement.objects.values(
            'skill__name', 'skill__category__name', 'skill_id'
        ).annotate(
            jobs_requiring=Count('job', distinct=True),
            avg_level_required=Avg('required_proficiency')
        ).filter(jobs_requiring__gte=1).order_by('-avg_level_required', '-jobs_requiring')

        for demand in all_required:
            sid = demand['skill_id']
            required = round(demand['avg_level_required'], 1)
            user_score = user_skill_map.get(sid)
            current = round(user_score.verified_level, 1) if user_score else 0.0
            gap_val = round(max(0, required - current), 1)

            if gap_val <= 0:
                continue  # user already meets/exceeds requirement

            severity = 'critical' if gap_val >= 5 else ('high' if gap_val >= 3 else 'moderate')
            skill_gaps.append({
                'skill_name': demand['skill__name'],
                'category': demand['skill__category__name'] or 'General',
                'jobs_requiring': demand['jobs_requiring'],
                'avg_level_required': required,
                'current_level': current,
                'gap_value': gap_val,
                'severity': severity,
                'skill_id': sid,
            })
    except Exception as e:
        logger.warning(f"Could not fetch skill gaps: {str(e)}")
        skill_gaps = []

    total_gaps_count = len(skill_gaps)
    displayed_gaps = skill_gaps[:6]  # Show first 6 in sidebar

    # Build enriched list of ALL user skills (verified + claimed) sorted by level desc
    all_user_skills = []
    for score in user_skill_scores.order_by('-verified_level'):
        all_user_skills.append({
            'id': score.skill_id,
            'name': score.skill.name,
            'category': score.skill.category.name if score.skill.category else 'General',
            'level': round(score.verified_level, 1),
            'status': score.status,  # 'verified' or 'claimed'
            'is_verified': score.status == 'verified',
            'last_assessment_date': score.last_assessment_date,
        })
    
    # Get recent assessment attempts
    recent_attempts = AssessmentAttempt.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('skill', 'assessment').order_by('-completed_at')[:5]
    
    context = {
        'skills_by_category': skills_by_category,
        'total_skills': total_skills,
        'total_skills_available': total_skills,
        'verified_count': verified_count,
        'remaining_count': total_skills - verified_count,
        'completion_percentage': completion_percentage,
        'avg_proficiency': avg_proficiency,
        'verified_skills': verified_skills,
        'all_user_skills': all_user_skills,
        'all_user_skills_count': len(all_user_skills),
        'categories': category_progress,
        'skill_gaps': skill_gaps,
        'displayed_gaps': displayed_gaps,
        'total_gaps_count': total_gaps_count,
        'recent_attempts': recent_attempts,
    }
    
    return render(request, 'assessments/skill_diagnostic_landing.html', context)


@login_required
def job_skill_gap_analysis(request, job_id):
    """
    Job-specific skill gap analysis page.
    Shows required skills vs user's verified skills for a specific job.
    """
    job = get_object_or_404(Job, id=job_id)
    
    # Get all required skills for this job
    job_requirements = JobSkillRequirement.objects.filter(
        job=job
    ).select_related('skill', 'skill__category')
    
    # Get user's skill scores (both verified and claimed)
    user_skill_scores = {
        score.skill_id: score 
        for score in UserSkillScore.objects.filter(
            user=request.user
        ).select_related('skill')
    }
    
    # Also get user profile skills for broader matching
    user_profile_skills_lower = [s.lower() for s in request.user.get_all_skills_list()]
    
    # Analyze gaps and create objects matching my_skill_gaps.html template expectations
    matched_skills = []
    partial_skills = []
    all_gaps = []
    
    def _make_gap_obj(skill, current_level, required_level):
        """Build a gap object with all fields the template needs."""
        return type('obj', (object,), {
            'skill': skill,
            'skill_id': skill.id,
            'skill_name': skill.name,
            'current_level': current_level,
            'required_level': required_level,
            'user_level': current_level,
            'gap_value': max(0, required_level - current_level),
            'priority_score': (required_level - current_level) * (required_level / 10),
            'has_skill': current_level > 0,
            'meets_requirement': current_level >= required_level,
            'related_job': job,
        })()

    if job_requirements.exists():
        # ── Path A: detailed JobSkillRequirement records exist ────
        for requirement in job_requirements:
            skill = requirement.skill
            user_score = user_skill_scores.get(skill.id)
            current_level = user_score.verified_level if user_score else 0
            required_level = requirement.required_proficiency

            gap_obj = _make_gap_obj(skill, current_level, required_level)

            if gap_obj.meets_requirement:
                matched_skills.append(gap_obj)
            elif gap_obj.has_skill:
                partial_skills.append(gap_obj)
            else:
                all_gaps.append(gap_obj)
    elif job.skills:
        # ── Path B: fallback to job.skills JSON list ──────────────
        default_category, _ = SkillCategory.objects.get_or_create(
            name='Technical', defaults={'description': 'Technical skills'},
        )
        for skill_data in job.skills:
            skill_name = skill_data.get('name') if isinstance(skill_data, dict) else skill_data
            if not skill_name:
                continue

            # Look up or create the Skill row
            skill = Skill.objects.filter(name__iexact=skill_name).first()
            if not skill:
                skill, _ = Skill.objects.get_or_create(
                    name=skill_name, category=default_category,
                    defaults={'description': f'{skill_name} skill', 'is_active': True},
                )

            # Determine user's current level
            user_score = user_skill_scores.get(skill.id)
            current_level = user_score.verified_level if user_score else 0
            if current_level == 0 and skill.name.lower() in user_profile_skills_lower:
                current_level = 3.0  # Profile-claimed baseline

            # Use a sensible default required level (7/10) for JSON-only skills
            required_level = 7.0

            gap_obj = _make_gap_obj(skill, current_level, required_level)

            if gap_obj.meets_requirement:
                matched_skills.append(gap_obj)
            elif gap_obj.has_skill:
                partial_skills.append(gap_obj)
            else:
                all_gaps.append(gap_obj)
    
    total_skills_required = len(matched_skills) + len(partial_skills) + len(all_gaps)
    match_score = (len(matched_skills) / total_skills_required * 100) if total_skills_required else 0
    
    # Categorize ALL non-matching skills (including partial) by priority for my_skill_gaps.html template
    all_skill_gaps = all_gaps + partial_skills  # Include both missing and partial skills as gaps
    critical_gaps = [g for g in all_skill_gaps if g.required_level >= 8]
    high_gaps = [g for g in all_skill_gaps if 5 <= g.required_level < 8]
    moderate_gaps = [g for g in all_skill_gaps if g.required_level < 5]
    
    context = {
        'job': job,
        'matched_skills': matched_skills,
        'partial_skills': partial_skills,
        'missing_skills': all_gaps,
        'skill_gaps': all_skill_gaps,  # For template conditional check
        'critical_gaps': critical_gaps,
        'high_gaps': high_gaps,
        'moderate_gaps': moderate_gaps,
        'total_gaps': len(all_skill_gaps),
        'match_score': round(match_score, 1),
        'total_skills_required': total_skills_required,
    }
    
    return render(request, 'assessments/my_skill_gaps.html', context)
