# Job Elevate - AI Coding Agent Instructions

## Project Overview
Django-based AI-powered job matching and upskilling platform with 8 modular apps. Uses Google Gemini API for AI features, SQLite/PostgreSQL database, and Django templates with Tailwind CSS.

## Architecture & Key Patterns

### Multi-App Structure
The codebase follows Django's app-based architecture with clear separation of concerns:
- **accounts**: Custom User model (`AbstractUser`) with role-based access (student/professional/recruiter). Fields stored as JSON (projects, internships, certifications) or CSV strings (technical_skills).
- **assessments**: Skill testing system with AI-generated MCQ questions. Critical anti-cheating features built-in.
- **jobs**: Job listings with ML-based recommendation engine using scikit-learn for cosine similarity matching.
- **learning**: AI-powered learning path generation based on skill gaps (in `learning_path_generator.py`).
- **recruiter**: Job posting interface with skill-based matching (proficiency levels 1-10).
- **community**: Forum and peer support.
- **dashboard**: User analytics and centralized navigation.
- **resume_builder**: ATS-compliant resume generation with PDF export.

### Critical Design Decisions

**1. AI Token Conservation Pattern**
Questions are generated ONCE per skill and cached in `QuestionBank`. Never regenerate questions - this is by design to prevent API quota exhaustion.
- Check `Skill.questions_generated` flag before calling AI
- AI service in `assessments/ai_service.py` with fallback to template questions
- Google Gemini API (`GOOGLE_API_KEY` in .env) used for question generation

**2. Anti-Cheating System**
Assessment system prevents answer memorization:
- Correct answers stored as TEXT values, not indices (`correct_answer` field)
- Options shuffled per user using `shuffle_seed` in `AssessmentAttempt`
- Question selection tracked with `selected_question_ids` JSON field
- 20 questions per assessment: 8 easy, 6 medium, 6 hard

**3. Skill Proficiency Model**
Two parallel tracking systems exist:
- **UserSkillScore**: Official skill tracking (0-10 scale, status: 'claimed'/'verified')
- **AssessmentAttempt**: Stores assessment data (score, proficiency_level, passed flag)
- Scoring: 60% threshold for passing (12/20 questions)

### Data Flow Examples

**Job Application Flow:**
1. User views job → `jobs/views.py:job_detail`
2. Clicks "Add & Take Assessment" → `jobs/views.py:claim_skill_from_job`
3. Creates UserSkillScore (status='claimed') → Redirects to assessment
4. Assessment completes → Updates UserSkillScore (status='verified', proficiency_level)

**Recommendation Engine:**
Location: `jobs/recommendation_engine.py`
- ContentBasedRecommender: Jaccard similarity on skills (40% weight) + coverage (60% weight)
- Handles both legacy (string) and new (dict) skill formats
- Returns scores 0.0-1.0 for job matching

## Development Workflows

### Setup & Running
```bash
# Initial setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python backend/manage.py migrate

# Required .env variables in backend/backend/.env:
SECRET_KEY=your-key
GOOGLE_API_KEY=your-gemini-api-key  # Get from https://aistudio.google.com/app/apikey
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
DATABASE_URL=sqlite:///db.sqlite3

# Run server
cd backend
python manage.py runserver
```

### Management Commands
```bash
# Add pre-populated questions to database (runs once)
python manage.py add_questions

# Populate assessment data including skills and categories
python manage.py populate_assessment_data

# Shell access for debugging
python manage.py shell
>>> from assessments.models import UserSkillScore, Skill, AssessmentAttempt
```

### Testing Patterns
Test files located at project root (`backend/test_*.py`):
- `test_assessment_20q.py`: Validates 20-question system
- `test_workflow.py`: End-to-end assessment workflow testing
- Run with: `python backend/test_assessment_20q.py` (standalone Django scripts, not pytest)

### Debugging Common Issues
**NoReverseMatch errors**: Check URL patterns in each app's `urls.py`. Assessment URLs require both `job_id` and `skill_id` parameters.
**Question generation**: Never regenerate - check `QuestionBank` table first. Use `python manage.py add_questions` only if empty.
**Skill matching fails**: User.technical_skills is CSV string - parse with `get_skills_list()` method.

## Project-Specific Conventions

### Model Patterns
- User fields with JSON data: Always use JSONField (skills in jobs, certifications in User)
- Proficiency: Always 0-10 float scale (FloatField with validators)
- Status fields: Use choices tuples at model level, not in separate tables

### View Patterns
- Assessment views in `assessments/views.py` handle attempt lifecycle
- Skill-based views split into separate files: `skill_intelligence_views.py`, `skill_management_views.py`
- Job recommendation views: `jobs/recommendation_dashboard_views.py`

### Template Organization
Each app has `templates/<app_name>/` subdirectory following Django conventions.
Context processors in `backend/context_processors.py` and `dashboard/context_processors.py` provide global template variables.

### URL Namespacing
All apps use namespaced URLs:
```python
# In urls.py
path('assessments/', include(('assessments.urls', 'assessments'), namespace='assessments'))

# In templates/views
{% url 'assessments:take_assessment' attempt.id %}
reverse('jobs:job_detail', kwargs={'job_id': job.id})
```

## Integration Points

### AI Services
- **Google Gemini**: Question generation (`assessments/ai_service.py`)
- **Learning Paths**: Uses Gemini for personalized course recommendations (`learning/learning_path_generator.py`)
- Both services have fallback to template data if API unavailable

### External Dependencies
- **PDF Generation**: ReportLab + WeasyPrint for resume export
- **ML Stack**: scikit-learn, numpy, pandas for recommendation engine
- **Email**: Django SMTP backend (Gmail) for OTP verification

### Cross-App Communication
- Jobs → Assessments: Via skill claiming workflow
- Assessments → Learning: Skill gaps trigger learning path generation
- Dashboard: Aggregates data from all apps via context processors

## Key Files Reference
- Main settings: `backend/backend/settings.py`
- URL routing: `backend/backend/urls.py`
- Assessment flow documentation: `ASSESSMENT_20Q_IMPLEMENTATION.md`, `WORKFLOW_FIXED.md`
- AI setup guide: `GOOGLE_GEMINI_SETUP.md`
