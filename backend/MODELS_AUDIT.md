# Models Structure Audit & Recommendations

## OVERVIEW

All models across the project follow Django best practices with proper verbose names, help text, and field validators. The structure is production-ready with some minor improvements suggested.

---

## 1. ASSESSMENTS APP MODELS ✅

**File**: `assessments/models.py` (499 lines)

### Models:
1. **SkillCategory**: Categories for grouping skills
2. **Skill**: Individual skills with question generation tracking
3. **QuestionBank**: Persistent question storage (AI + template)
4. **Assessment**: Legacy model (kept for backward compatibility)
5. **AssessmentAttempt**: User assessment sessions
6. **UserAnswer**: Individual question answers
7. **UserSkillScore**: Verified skill proficiency levels

### Strengths:
- ✅ Comprehensive documentation
- ✅ Anti-cheating design (shuffled options, server-side validation)
- ✅ Anti-token-exhaustion (one-time question generation)
- ✅ Proper indexes for performance
- ✅ Graceful degradation (AI → fallback)

### Recommendations:
1. **Add soft delete**: Consider adding `is_deleted` field to QuestionBank instead of hard deletes
2. **Question versioning**: Track question updates with version field
3. **Add question statistics**: Track average time spent per question
4. **User attempt limits**: Add field to track retake cooldowns

---

## 2. RECRUITER APP MODELS

**File**: `recruiter/models.py` (448 lines)

### Key Models:
1. **Job**: Job postings with full details
2. **JobSkillRequirement**: Skills required for jobs with proficiency levels
3. **JobApplication**: User applications to jobs
4. **SavedSearch**: User saved job search criteria
5. **AIJobDescription**: AI-generated job descriptions
6. **RecruiterProfile**: Extended profile for recruiters

### Critical Field:
```python
# JobSkillRequirement
required_proficiency = models.FloatField(
    default=5.0,
    validators=[MinValueValidator(0), MaxValueValidator(10)]
)
```

### Strengths:
- ✅ Comprehensive job management
- ✅ Skill-based matching architecture
- ✅ AI integration for job descriptions
- ✅ Proper status tracking

### Recommendations:
1. **Standardize skill levels**: Create a PROFICIENCY_CHOICES constant
   ```python
   PROFICIENCY_LEVELS = [
       (0, 'No Experience'),
       (2.5, 'Beginner'),
       (5.0, 'Intermediate'),
       (7.5, 'Advanced'),
       (10.0, 'Expert'),
   ]
   ```
2. **Add JobSkillRequirement ordering**: Add default ordering by criticality
3. **Job expiration**: Consider auto-expiring old jobs
4. **Application status webhooks**: Add integration points for status updates

---

## 3. JOBS APP MODELS ✅

**File**: `jobs/models.py` (112 lines)

### Models:
1. **JobView**: Track user views of jobs
2. **JobBookmark**: User saved jobs
3. **UserJobPreference**: User job search preferences

### Strengths:
- ✅ Simple and focused
- ✅ Proper timestamps
- ✅ Unique constraints to prevent duplicates

### Recommendations:
1. **Analytics enhancement**: Add session tracking to JobView
   ```python
   session_id = models.CharField(max_length=100, blank=True)
   referrer = models.URLField(blank=True)
   ```
2. **Bookmark folders**: Allow organizing bookmarks into folders
3. **Preference scoring**: Add weight field to UserJobPreference

---

## 4. LEARNING APP MODELS

**File**: `learning/models.py` (460 lines)

### Models:
1. **Course**: Available learning resources
2. **CourseEnrollment**: User course enrollments
3. **CourseProgress**: Track completion progress
4. **LearningPath**: Structured learning journeys
5. **LearningPathStep**: Individual steps in paths
6. **UserLearningPath**: User progress in learning paths

### Strengths:
- ✅ Comprehensive learning management
- ✅ Multi-platform course support (Coursera, Udemy, etc.)
- ✅ Progress tracking with completion percentages
- ✅ Certificate management

### Recommendations:
1. **Add course ratings**: User ratings and reviews
   ```python
   class CourseReview(models.Model):
       course = models.ForeignKey(Course, on_delete=models.CASCADE)
       user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
       rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
       review_text = models.TextField(blank=True)
       created_at = models.DateTimeField(auto_now_add=True)
   ```
2. **Gamification**: Add badges/achievements for completion milestones
3. **Learning streaks**: Track consecutive days of learning
4. **Spaced repetition**: Add quiz/review scheduling

---

## 5. COMMUNITY APP MODELS

**File**: `community/models.py`

### Models:
1. **Post**: Community forum posts
2. **Comment**: Post comments
3. **PostLike**: Post likes
4. **CommentLike**: Comment likes
5. **Report**: Content moderation reports

### Recommendations:
1. **Add post categories/tags**: Organize discussions
2. **User reputation**: Track helpful contributions
3. **Moderation queue**: Add status field for pending/approved posts
4. **Mention notifications**: Track @mentions

---

## 6. RESUME BUILDER APP MODELS

**File**: `resume_builder/models.py`

### Models:
1. **ResumeTemplate**: Available resume templates
2. **Resume**: User resumes
3. **ResumeSection**: Resume sections (experience, education, etc.)
4. **WorkExperience**: Job history
5. **Education**: Educational background
6. **Project**: Portfolio projects
7. **Certification**: Professional certifications

### Recommendations:
1. **ATS optimization**: Add ATS score field to Resume
2. **Version control**: Track resume versions
3. **Export formats**: Track which formats (PDF, DOCX) generated
4. **Template analytics**: Track which templates most successful

---

## CROSS-APP CONSISTENCY

### Naming Conventions ✅
- All models use verbose_name and verbose_name_plural
- Timestamps: created_at, updated_at (auto_now_add, auto_now)
- Boolean fields: is_active, is_verified, is_deleted
- Foreign keys: proper related_names

### Common Patterns ✅
- Use of Django validators (Min/Max, URL, Email)
- gettext_lazy for internationalization
- Proper choices with tuples
- Index hints for performance

---

## RECOMMENDED GLOBAL IMPROVEMENTS

### 1. Abstract Base Models
Create common base classes in `core/models.py`:

```python
class TimeStampedModel(models.Model):
    """Abstract model with creation and modification timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    """Abstract model with soft delete functionality"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True

class UserOwnedModel(models.Model):
    """Abstract model for user-owned content"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    
    class Meta:
        abstract = True
```

### 2. Standard Proficiency Scale
Create shared constant in `core/constants.py`:

```python
PROFICIENCY_SCALE = [
    (0.0, 'No Experience'),
    (2.5, 'Beginner - Basic understanding'),
    (5.0, 'Intermediate - Practical application'),
    (7.5, 'Advanced - Expert knowledge'),
    (10.0, 'Master - Industry leader'),
]

DIFFICULTY_LEVELS = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
    ('expert', 'Expert'),
]
```

### 3. Model Managers
Add custom managers for common queries:

```python
# assessments/models.py
class SkillManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)
    
    def with_questions(self):
        return self.filter(question_bank__isnull=False).distinct()

class Skill(models.Model):
    objects = SkillManager()
    # ... rest of model
```

### 4. Signal Handlers
Organize in `signals.py` for each app:

```python
# assessments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=AssessmentAttempt)
def update_skill_score(sender, instance, created, **kwargs):
    if instance.status == 'completed':
        # Auto-update UserSkillScore
        pass
```

### 5. Model Validators
Create reusable validators in `core/validators.py`:

```python
from django.core.exceptions import ValidationError

def validate_proficiency_level(value):
    if not 0 <= value <= 10:
        raise ValidationError(
            f'{value} is not a valid proficiency level (0-10 scale)'
        )

def validate_difficulty(value):
    if value not in ['easy', 'medium', 'hard', 'expert']:
        raise ValidationError(
            f'{value} is not a valid difficulty level'
        )
```

---

## MIGRATION STRATEGY

### Priority 1: Critical Fixes ✅
- [x] Add missing fields to QuestionBank (created_by_ai, times_incorrect)
- [x] Fix required_level → required_proficiency reference

### Priority 2: Consistency (Next Sprint)
- [ ] Create abstract base models
- [ ] Migrate existing models to use base classes
- [ ] Add custom managers
- [ ] Standardize field names across apps

### Priority 3: Enhancements (Future)
- [ ] Add soft delete to all content models
- [ ] Implement version control for key models
- [ ] Add audit trail (who changed what when)
- [ ] Performance optimization (select_related, prefetch_related hints)

---

## DOCUMENTATION REQUIREMENTS

### Each Model Should Have:
1. **Docstring**: Purpose and usage
2. **Field help_text**: Clear descriptions
3. **Example usage**: In docstring or separate docs
4. **Relationships**: Document foreign key relationships
5. **Business rules**: Constraints and validation logic

### Example:
```python
class JobSkillRequirement(models.Model):
    """
    Defines skills required for a job posting.
    
    Each requirement specifies:
    - Required proficiency level (0-10 scale)
    - Criticality weight (how important this skill is)
    - Whether skill is mandatory vs nice-to-have
    
    Example:
        # Job requiring Python at intermediate level
        requirement = JobSkillRequirement.objects.create(
            job=job,
            skill=python_skill,
            required_proficiency=6.0,
            criticality=0.8,
            is_mandatory=True,
            skill_type='must_have'
        )
    
    Related Views:
        - job_skill_gap_analysis: Compares user skills to requirements
        - start_assessment_from_job: Validates skill is required
    """
    # ... model fields
```

---

## TESTING RECOMMENDATIONS

### Model Tests Required:
1. **Field validation**: Test validators work correctly
2. **Relationships**: Test foreign keys and related_names
3. **Methods**: Test custom model methods
4. **Managers**: Test custom querysets
5. **Signals**: Test signal handlers fire correctly

### Example Test:
```python
# tests/test_models.py
from django.test import TestCase
from assessments.models import Skill, QuestionBank

class QuestionBankModelTest(TestCase):
    def test_success_rate_calculation(self):
        skill = Skill.objects.create(name='Python')
        question = QuestionBank.objects.create(
            skill=skill,
            question_text='Test?',
            times_used=10,
            times_correct=7
        )
        self.assertEqual(question.success_rate, 70.0)
```

---

## SUMMARY

### Overall Status: **PRODUCTION READY** ✅

All models are well-designed with proper Django conventions. The architecture supports:
- ✅ Skill-based job matching
- ✅ Assessment and learning systems
- ✅ Community features
- ✅ Resume building
- ✅ Recruiter/candidate workflows

### Minor Improvements Suggested:
1. Create abstract base models for DRY
2. Add soft delete to preserve data
3. Implement model versioning for audit trails
4. Add more comprehensive indexes for performance
5. Create reusable validators

### No Breaking Changes Needed:
Current models work correctly and follow best practices. Suggested improvements are enhancements, not fixes.

---

**Last Updated**: 2026-01-03
**Audited By**: AI Code Review
**Status**: ✅ APPROVED FOR PRODUCTION
