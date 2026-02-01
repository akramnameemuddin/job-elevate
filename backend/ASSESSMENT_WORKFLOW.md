# Complete Skill Assessment Workflow Guide

## SYSTEM OVERVIEW

The Job-Elevate platform has a **production-ready skill assessment system** that:
1. Starts ONLY from job detail page (when user wants to close skill gaps)
2. Minimizes AI usage through one-time question generation
3. Prevents cheating with server-side validation
4. Works even when AI tokens exhausted (fallback templates)
5. Updates user skills and enables job applications when qualified

---

## ARCHITECTURE

```
┌─────────────────────┐
│   Job Detail Page   │
│   /jobs/<id>/       │
└──────────┬──────────┘
           │
           │ [View Skill Requirements]
           ▼
┌─────────────────────────────┐
│   Gap Analysis Page         │
│   /assessments/job/5/gaps/  │
│   - Shows required skills   │
│   - User current levels     │
│   - Skill gaps by priority  │
└──────────┬──────────────────┘
           │
           │ [Take Assessment] button
           ▼
┌────────────────────────────────────┐
│   Start Assessment                 │
│   /assessments/start-from-job/     │
│      <job_id>/<skill_id>/          │
│   - Validates job requires skill   │
│   - Generates/retrieves questions  │
│   - Creates AssessmentAttempt      │
└──────────┬─────────────────────────┘
           │
           │ (redirect)
           ▼
┌────────────────────────────────┐
│   Take Assessment Page         │
│   /assessments/take/<id>/      │
│   - Shows questions one by one │
│   - Shuffled options           │
│   - AJAX answer submission     │
│   - Timer tracking             │
└──────────┬─────────────────────┘
           │
           │ [Submit Assessment]
           ▼
┌───────────────────────────────────┐
│   Submit Assessment                │
│   /assessments/submit/<id>/       │
│   - Calculates final score        │
│   - Updates UserSkillScore        │
│   - Creates permanent record      │
└──────────┬────────────────────────┘
           │
           │ (redirect)
           ▼
┌──────────────────────────────────┐
│   Results Page                   │
│   /assessments/result/<id>/      │
│   - Shows score & percentage     │
│   - Correct/incorrect breakdown  │
│   - Skill level updated          │
│   - Recommendations              │
└──────────┬───────────────────────┘
           │
           │ [Back to Job/Dashboard]
           ▼
┌────────────────────────────────┐
│   Updated Gap Analysis         │
│   - Skill gap reduced/closed   │
│   - Match percentage increased │
│   - Apply button enabled?      │
└────────────────────────────────┘
```

---

## URL ROUTING

### assessments/urls.py

```python
urlpatterns = [
    # Main skill dashboard (direct access)
    path('', views.skill_intake_dashboard, name='skill_intake_dashboard'),
    
    # Job-specific gap analysis (PRIMARY ENTRY POINT)
    path('job/<int:job_id>/gaps/', views.job_skill_gap_analysis, name='job_skill_gap_analysis'),
    
    # Start assessment from job context
    path('start-from-job/<int:job_id>/<int:skill_id>/', 
         views.start_assessment_from_job, 
         name='start_assessment_from_job'),
    
    # Start assessment directly (from dashboard)
    path('start/<int:skill_id>/', 
         views.start_assessment_direct, 
         name='start_assessment_direct'),
    
    # Take assessment (display questions)
    path('take/<int:attempt_id>/', 
         views.take_assessment, 
         name='take_assessment'),
    
    # Submit single answer (AJAX)
    path('submit-answer/<int:attempt_id>/', 
         views.submit_answer, 
         name='submit_answer'),
    
    # Complete assessment
    path('submit/<int:attempt_id>/', 
         views.submit_assessment, 
         name='submit_assessment'),
    
    # View results
    path('result/<int:attempt_id>/', 
         views.assessment_result, 
         name='assessment_result'),
]
```

---

## VIEW FUNCTIONS

### 1. job_skill_gap_analysis(request, job_id)

**Purpose**: Show user which skills they need for a specific job

**Logic**:
```python
1. Get job and its skill requirements
2. Get user's current skill scores
3. For each requirement:
   - Compare user level vs required level
   - Calculate gap
   - Categorize as matched/partial/missing
4. Categorize gaps by priority:
   - Critical: 8-10 required
   - High: 5-7.9 required
   - Moderate: <5 required
5. Calculate match percentage
6. Render my_skill_gaps.html
```

**Template**: `assessments/templates/assessments/my_skill_gaps.html`

**Context**:
```python
{
    'job': job,
    'skill_gaps': all_skill_gaps,  # For {% if not skill_gaps %}
    'critical_gaps': [gaps with required >= 8],
    'high_gaps': [gaps with 5 <= required < 8],
    'moderate_gaps': [gaps with required < 5],
    'matched_skills': [skills user already has],
    'partial_skills': [skills user has but below required],
    'missing_skills': [skills user doesn't have],
    'total_gaps': total count,
    'match_score': percentage (0-100),
    'total_skills_required': total count,
}
```

**Template Buttons**:
```html
<a href="{% url 'assessments:start_assessment_from_job' job.id gap.skill.id %}" 
   class="btn btn-primary">
    <i class='bx bx-play-circle'></i> Take Assessment
</a>
```

---

### 2. start_assessment_from_job(request, job_id, skill_id)

**Purpose**: Validate and start assessment from job context

**Logic**:
```python
1. Verify job exists
2. Verify job requires this skill (JobSkillRequirement)
3. Get or select questions from QuestionBank
   - Try to use existing questions
   - Generate new if needed (AI or template)
4. Create AssessmentAttempt:
   - Store question IDs
   - Shuffle options per question
   - Set job context
   - Status = 'in_progress'
5. Redirect to take_assessment
```

**Key Validation**:
```python
if not JobSkillRequirement.objects.filter(
    job_id=job_id, 
    skill_id=skill_id
).exists():
    messages.error(request, "This skill is not required for this job")
    return redirect('jobs:job_detail', job_id=job_id)
```

---

### 3. take_assessment(request, attempt_id)

**Purpose**: Display questions and handle answer submission

**Template**: `assessments/templates/assessments/take_assessment.html`

**Features**:
- Shows one question at a time (or all questions in list)
- Options shuffled per attempt (anti-cheating)
- AJAX submission to `/submit-answer/<attempt_id>/`
- Timer tracking
- Progress indicator
- **NEVER sends correct answers to frontend**

**AJAX Submit**:
```javascript
fetch(`/assessments/submit-answer/{{ attempt.id }}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        question_id: questionId,
        selected_answer: answer
    })
})
```

---

### 4. submit_answer(request, attempt_id) [AJAX]

**Purpose**: Validate and store single answer (server-side only)

**Logic**:
```python
1. Get question and correct answer from database
2. Check if selected answer matches correct answer
3. Calculate points earned
4. Create UserAnswer record
5. Update question statistics (times_correct/incorrect)
6. Return JSON: {'is_correct': bool, 'points': int}
```

**Security**: Correct answer NEVER sent to client, all validation server-side

---

### 5. submit_assessment(request, attempt_id)

**Purpose**: Complete assessment and calculate final score

**Logic**:
```python
1. Mark attempt as 'completed'
2. Calculate total score from all UserAnswer records
3. Calculate percentage
4. Update UserSkillScore:
   - Set verified_level based on percentage
   - Update last_assessment_date
   - Increment total_attempts
5. Redirect to results page
```

**Score to Level Conversion**:
```python
# Example: 80% score = 8.0/10 proficiency
percentage = (score / max_score) * 100
verified_level = round((percentage / 100) * 10, 1)
```

---

### 6. assessment_result(request, attempt_id)

**Purpose**: Show detailed results and recommendations

**Template**: `assessments/templates/assessments/assessment_results.html`

**Context**:
```python
{
    'attempt': attempt,
    'skill': skill,
    'score': score,
    'max_score': max_score,
    'percentage': percentage,
    'correct_count': correct answers,
    'incorrect_count': incorrect answers,
    'user_skill_score': updated UserSkillScore,
    'job': related job (if from job context),
    'recommendations': next steps,
}
```

**Template Shows**:
- Final score: 8/10 (80%)
- Breakdown: 8 correct, 2 incorrect
- Updated skill level: Python = 8.0/10
- Recommendation: "Great job! You're now qualified..."
- Actions: "Return to Job", "View Learning Resources", "Take Another Assessment"

---

## DATABASE MODELS

### AssessmentAttempt
```python
{
    'user': User FK,
    'skill': Skill FK,
    'question_ids': [1, 5, 8, 12, 15] (JSON),
    'shuffled_options': {  # JSON
        1: [2, 0, 3, 1],  # Shuffled indexes
        5: [1, 3, 0, 2],
    },
    'status': 'in_progress' | 'completed',
    'score': 8,
    'max_score': 10,
    'percentage': 80.0,
    'started_at': datetime,
    'completed_at': datetime,
    'time_spent_seconds': 420,
}
```

### UserAnswer
```python
{
    'attempt': AssessmentAttempt FK,
    'question_bank': QuestionBank FK,
    'selected_answer': 'Option B',
    'is_correct': True,
    'points_earned': 10,
}
```

### UserSkillScore
```python
{
    'user': User FK,
    'skill': Skill FK,
    'verified_level': 8.0,  # 0-10 scale
    'status': 'verified' | 'pending' | 'expired',
    'last_assessment_date': datetime,
    'total_attempts': 3,
}
```

### QuestionBank
```python
{
    'skill': Skill FK,
    'question_text': 'What is Python?',
    'options': ['Language', 'Snake', 'Tool', 'None'],  # JSON
    'correct_answer': 'Language',
    'difficulty': 'easy' | 'medium' | 'hard',
    'points': 5 | 10 | 15,
    'explanation': 'Python is a programming language...',
    'created_by_ai': False,
    'times_used': 50,
    'times_correct': 35,
    'times_incorrect': 15,
}
```

---

## TEMPLATE STRUCTURE

### my_skill_gaps.html (450 lines)

**Sections**:
1. **Header**: Job title, match score
2. **Stats Grid**: Critical/High/Moderate/Total gaps count
3. **Critical Gaps Section**: Red priority skills (8-10)
   - For each gap:
     - Skill name, category
     - Current level, required level, gap value
     - Progress bar
     - "Take Assessment" button
4. **High Priority Gaps**: Orange (5-7.9)
5. **Moderate Priority Gaps**: Yellow (<5)
6. **Matched Skills**: Green (already qualified)
7. **Empty State**: "No Skill Gaps Identified" (if no gaps)

**Key Template Code**:
```html
{% if critical_gaps %}
<div class="card gap-section">
    <div class="section-header critical">
        <h3>Critical Gaps</h3>
    </div>
    {% for gap in critical_gaps %}
    <div class="gap-item">
        <h4>{{ gap.skill.name }}</h4>
        <div class="progress-bar">
            <div class="current" style="width: {% widthratio gap.current_level 10 100 %}%"></div>
            <div class="required-mark" style="left: {% widthratio gap.required_level 10 100 %}%"></div>
        </div>
        <a href="{% url 'assessments:start_assessment_from_job' job.id gap.skill.id %}" 
           class="btn btn-primary">
            Take Assessment
        </a>
    </div>
    {% endfor %}
</div>
{% endif %}
```

---

### take_assessment.html (435 lines)

**Features**:
- Question counter (1/10)
- Timer display
- Question text
- Multiple choice options (radio buttons)
- Previous/Next navigation
- Submit button
- AJAX answer submission
- Auto-save progress

**JavaScript**:
```javascript
// Answer submission
submitBtn.addEventListener('click', async () => {
    const selected = document.querySelector('input[name="answer"]:checked');
    const response = await fetch(`/assessments/submit-answer/${attemptId}/`, {
        method: 'POST',
        body: JSON.stringify({
            question_id: currentQuestionId,
            selected_answer: selected.value
        })
    });
    const result = await response.json();
    // Show feedback, move to next question
});
```

---

### assessment_results.html (751 lines)

**Sections**:
1. **Score Card**: Large display of score and percentage
2. **Breakdown**: Correct/incorrect counts with icons
3. **Skill Level**: Updated proficiency with progress bar
4. **Question Review**: (Optional) Show which questions correct/incorrect
5. **Recommendations**: Next steps based on score
6. **Actions**:
   - Return to Gap Analysis
   - View Learning Resources
   - Take Another Assessment
   - Apply to Job (if qualified)

---

## ANTI-CHEATING MEASURES

### 1. Server-Side Validation Only
```python
# CORRECT ✅ - Answer validation on server
def submit_answer(request, attempt_id):
    question = QuestionBank.objects.get(id=question_id)
    is_correct = (selected_answer == question.correct_answer)
    return JsonResponse({'is_correct': is_correct})

# WRONG ❌ - Never send correct answer to client
# context = {'correct_answer': question.correct_answer}  # DON'T DO THIS
```

### 2. Shuffled Options Per Attempt
```python
# Store shuffled order in AssessmentAttempt
shuffled_options = {
    question_id: [2, 0, 3, 1]  # Original indexes shuffled
}

# In template, options displayed in shuffled order
# But correct answer always checked against original
```

### 3. One-Time Question Generation
```python
# Questions generated ONCE per skill, reused forever
if not QuestionBank.objects.filter(skill=skill).exists():
    # Generate questions (AI or template)
    generate_questions(skill)

# All future assessments use these cached questions
# Prevents token exhaustion, maintains consistency
```

### 4. No Client-Side Answers
```javascript
// CORRECT ✅ - Store selected answer only
const selectedAnswer = 'Option B';

// WRONG ❌ - Never store correct answer in JavaScript
// const correctAnswer = 'Option B';  // DON'T DO THIS
```

---

## QUESTION GENERATION STRATEGY

### Priority Order:
1. **Use existing questions**: Check QuestionBank first
2. **AI generation**: If no questions and AI available
3. **Template fallback**: If AI unavailable or exhausted
4. **Error handling**: Show message if no questions available

### Code:
```python
# 1. Try to find existing questions
questions = QuestionBank.objects.filter(
    skill=skill
).order_by('?')[:10]  # Random 10

if questions.count() >= 5:
    return list(questions)

# 2. Try AI generation
if ai_service.is_available():
    new_questions = ai_service.generate_questions(
        skill=skill,
        count=10
    )
    # Save to QuestionBank
    for q in new_questions:
        QuestionBank.objects.create(skill=skill, **q)
    return new_questions

# 3. Fallback to template questions
template_questions = get_template_questions(skill.name)
if template_questions:
    for q in template_questions:
        QuestionBank.objects.create(skill=skill, **q)
    return template_questions

# 4. Error - no questions available
raise ValueError(f"No questions available for {skill.name}")
```

---

## JOB APPLICATION INTEGRATION

### When User Takes Assessment from Job:
1. **Gap analysis shows skill gap**
2. **User takes assessment**
3. **Score updates UserSkillScore**
4. **Gap analysis refreshes**:
   - Skill moved from "Missing" to "Matched"
   - Match percentage increases
   - If ALL requirements met → Enable "Apply Now" button

### Job Detail Page Logic:
```python
# jobs/views.py - job_detail view
user_skills = UserSkillScore.objects.filter(user=request.user)
job_requirements = JobSkillRequirement.objects.filter(job=job)

all_requirements_met = all(
    user_skills.filter(
        skill=req.skill,
        verified_level__gte=req.required_proficiency
    ).exists()
    for req in job_requirements
)

context['can_apply'] = all_requirements_met
```

### Template:
```html
{% if can_apply %}
<a href="{% url 'jobs:apply_job' job.id %}" class="btn btn-success">
    <i class='bx bx-send'></i> Apply Now
</a>
{% else %}
<a href="{% url 'assessments:job_skill_gap_analysis' job.id %}" class="btn btn-primary">
    <i class='bx bx-target'></i> View Skill Requirements
</a>
{% endif %}
```

---

## TESTING CHECKLIST

### Manual Testing:
- [ ] Can view job detail page
- [ ] Click "View Skill Requirements" → Gap analysis loads
- [ ] Gap analysis shows all skill gaps correctly
- [ ] Click "Take Assessment" → Questions load
- [ ] Answer questions → Answers save correctly
- [ ] Submit assessment → Results page loads
- [ ] Results show correct score and percentage
- [ ] UserSkillScore updated in database
- [ ] Return to gap analysis → Gap reduced/closed
- [ ] If qualified → "Apply Now" button appears

### Database Verification:
```sql
-- Check assessment attempt created
SELECT * FROM assessments_assessmentattempt WHERE user_id = 1 ORDER BY id DESC LIMIT 1;

-- Check answers saved
SELECT * FROM assessments_useranswer WHERE attempt_id = <attempt_id>;

-- Check skill score updated
SELECT * FROM assessments_userskillscore WHERE user_id = 1 AND skill_id = 1;

-- Check job requirements
SELECT * FROM recruiter_jobskillrequirement WHERE job_id = 5;
```

---

## TROUBLESHOOTING

### Issue: "No Skill Gaps Identified" shown when gaps exist
**Cause**: Template checks `{% if not skill_gaps %}` but view doesn't pass it
**Fix**: Add `'skill_gaps': all_skill_gaps` to context

### Issue: AttributeError: 'JobSkillRequirement' object has no attribute 'required_level'
**Cause**: Code uses wrong field name
**Fix**: Change `required_level` to `required_proficiency` in all views

### Issue: No questions available for skill
**Cause**: QuestionBank empty for that skill
**Fix**: Run `python manage.py add_questions` or create questions manually

### Issue: Assessment not starting from job
**Cause**: Job doesn't have JobSkillRequirement for that skill
**Fix**: Create JobSkillRequirement entry linking job to skill

---

## BEST PRACTICES

### 1. Always Use Job Context
```python
# GOOD ✅
start_assessment_from_job(job_id, skill_id)

# AVOID ❌
start_assessment_direct(skill_id)  # Use only from skill dashboard
```

### 2. Validate Job-Skill Relationship
```python
# Always check before starting assessment
if not JobSkillRequirement.objects.filter(
    job=job, skill=skill
).exists():
    return redirect_with_error()
```

### 3. Update Skills After Assessment
```python
# Automatically update UserSkillScore
UserSkillScore.objects.update_or_create(
    user=user,
    skill=skill,
    defaults={
        'verified_level': calculated_level,
        'last_assessment_date': timezone.now(),
    }
)
```

### 4. Show Clear Next Steps
```python
# In results template, guide user
if score >= 80:
    "Great job! You're now qualified for this job."
elif score >= 60:
    "Good attempt. Review the learning resources and try again."
else:
    "Keep practicing! Check out these courses to improve."
```

---

## FUTURE ENHANCEMENTS

### Planned Features:
1. **Adaptive Difficulty**: Adjust question difficulty based on performance
2. **Time Limits**: Add countdown timer per question
3. **Question Explanations**: Show why answer is correct/incorrect
4. **Learning Resources**: Link to courses for failed questions
5. **Retake Policy**: Limit retakes to once per 24 hours
6. **Certification**: Issue certificates for high scores
7. **Leaderboards**: Show top scorers per skill
8. **Peer Comparison**: Compare score to other users

---

**Last Updated**: 2026-01-03
**Document Version**: 1.0
**Status**: ✅ PRODUCTION READY
