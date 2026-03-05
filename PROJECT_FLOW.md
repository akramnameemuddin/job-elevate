# JobElevate — ER Flow & System Execution Guide

> Django 5.1 · Python 3.12 · PostgreSQL · Google Gemini AI · scikit-learn · AWS EC2

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Entity-Relationship (ER) Diagram](#2-entity-relationship-er-diagram)
3. [Model Reference](#3-model-reference)
4. [System Execution Flow](#4-system-execution-flow)
5. [Key User Journeys](#5-key-user-journeys)
6. [AI & ML Pipeline](#6-ai--ml-pipeline)
7. [API & URL Map](#7-api--url-map)
8. [Data Flow Between Apps](#8-data-flow-between-apps)

---

## 1. Project Structure

```
backend/
├── backend/          # Django settings, root URLs, WSGI/ASGI
├── accounts/         # Custom User model, auth, OTP email verification
├── assessments/      # Skill categories, MCQ bank, attempts, scoring
├── jobs/             # Job listings, bookmarks, recommendations, preferences
├── recruiter/        # Job posting, applications, ML candidate ranking
├── learning/         # Courses, skill gaps, AI learning paths
├── resume_builder/   # Resume templates, builder, AI tailoring, PDF export
├── dashboard/        # Aggregated analytics, notifications, context processors
├── community/        # Forum posts, comments, likes, follows, events
└── agents/           # AI career agent (Google ADK), orchestrator
```

---

## 2. Entity-Relationship (ER) Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ACCOUNTS                                           │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  User (AbstractUser)                                                     │   │
│  │  PK: id (int)                                                            │   │
│  │  user_type: student | professional | recruiter                           │   │
│  │  technical_skills: TextField (CSV string → get_skills_list())            │   │
│  │  projects: TextField (JSON string → get_projects())                      │   │
│  │  internships: TextField (JSON string → get_internships())                │   │
│  │  certifications: TextField (JSON string → get_certifications())          │   │
│  │  university, degree, cgpa, phone_number, objective                       │   │
│  │  linkedin_profile, github_profile, portfolio_website                     │   │
│  │  is_email_verified, email_otp                                            │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────────────────┘
                               │  (FK: user → everywhere below)
       ┌───────────────────────┼───────────────────────────────────────────┐
       │                       │                                           │
       ▼                       ▼                                           ▼
┌─────────────┐     ┌─────────────────────┐                  ┌────────────────────┐
│  RECRUITER  │     │    ASSESSMENTS       │                  │       JOBS         │
│             │     │                      │                  │                    │
│  Job        │     │  SkillCategory       │                  │  JobBookmark       │
│  ├─ posted_by→User│  └─ id, name, icon   │                  │  ├─ user → User    │
│  ├─ title   │     │                      │                  │  └─ job → Job      │
│  ├─ skills  │     │  Skill               │                  │                    │
│  │  (JSON)  │     │  ├─ category → Cat.  │                  │  JobView           │
│  ├─ status  │     │  ├─ name, difficulty │                  │  ├─ user → User    │
│  └─ created_at    │  └─ questions_generated                 │  └─ job → Job      │
│             │     │                      │                  │                    │
│  Application│     │  QuestionBank        │                  │  UserJobPreference │
│  ├─ job → Job     │  ├─ skill → Skill    │                  │  └─ user → User    │
│  ├─ applicant→User│  ├─ question_text    │                  │    (OneToOne)      │
│  ├─ status  │     │  ├─ options (JSON)   │                  │                    │
│  ├─ score   │     │  ├─ correct_answer   │                  │  JobRecommendation │
│  └─ cover_letter  │  └─ difficulty       │                  │  ├─ user → User    │
│             │     │                      │                  │  └─ job → Job      │
│  JobSkillReq│     │  AssessmentAttempt   │                  │                    │
│  ├─ job → Job     │  ├─ user → User      │                  │  UserSimilarity    │
│  ├─ skill→Skill   │  ├─ skill → Skill    │                  │  ├─ user1 → User   │
│  └─ proficiency   │  ├─ score (0-20)     │                  │  └─ user2 → User   │
│             │     │  ├─ passed (60% thr) │                  └────────────────────┘
│  UserJobFit │     │  ├─ shuffle_seed     │
│  ├─ user→User     │  ├─ selected_q_ids   │
│  └─ job → Job     │  └─ proficiency_level│
│             │     │                      │
│  Message    │     │  UserAnswer          │
│  ├─ sender→User   │  ├─ attempt → Attempt│
│  ├─ recipient→User│  ├─ question_bank→QB │
│  └─ app→Application  └─ chosen_answer   │
└─────────────┘     │                      │
                    │  UserSkillScore       │
                    │  ├─ user → User       │
                    │  ├─ skill → Skill     │
                    │  ├─ score (0.0-10.0)  │
                    │  └─ status: claimed/verified
                    └──────────────────────┘

┌─────────────────────────────┐     ┌──────────────────────────────────────────┐
│         LEARNING            │     │           RESUME_BUILDER                 │
│                             │     │                                          │
│  Course                     │     │  ResumeTemplate                          │
│  ├─ skill → Skill           │     │  └─ html_structure, css_structure        │
│  ├─ title, provider         │     │                                          │
│  ├─ url, duration           │     │  Resume                                  │
│  └─ difficulty              │     │  ├─ user → User                          │
│                             │     │  ├─ template → ResumeTemplate            │
│  SkillGap                   │     │  ├─ show_* toggles (bool fields)         │
│  ├─ user → User             │     │  ├─ selected_projects (JSON indices)     │
│  ├─ skill → Skill           │     │  ├─ selected_experience (JSON indices)   │
│  ├─ current_level (0-10)    │     │  ├─ selected_internships (JSON indices)  │
│  ├─ required_level (0-10)   │     │  └─ selected_certifications (JSON idx)   │
│  └─ related_job → Job       │     │                                          │
│                             │     │  TailoredResume                          │
│  LearningPath               │     │  ├─ user → User                          │
│  ├─ user → User             │     │  ├─ base_resume → Resume                 │
│  ├─ skill_gap → SkillGap    │     │  ├─ job → Job                            │
│  ├─ courses (M2M → Course)  │     │  ├─ suggestions (JSON)                   │
│  └─ ai_generated_plan (JSON)│     │  ├─ tailored_skills/experience (JSON)    │
│                             │     │  └─ selected_* (JSON indices)            │
│  CourseProgress             │     └──────────────────────────────────────────┘
│  ├─ user → User             │
│  ├─ course → Course         │     ┌──────────────────────────────────────────┐
│  └─ learning_path → LP      │     │            COMMUNITY                     │
└─────────────────────────────┘     │                                          │
                                    │  Tag  ←──── Post (M2M)                   │
                                    │  Post                                     │
                                    │  ├─ author → User                        │
                                    │  ├─ tags (M2M → Tag)                     │
                                    │  └─ category, is_pinned                  │
                                    │                                          │
                                    │  Comment                                 │
                                    │  ├─ post → Post                          │
                                    │  ├─ author → User                        │
                                    │  └─ parent → Comment (self, for replies) │
                                    │                                          │
                                    │  Like                                    │
                                    │  ├─ user → User                          │
                                    │  ├─ post → Post (nullable)               │
                                    │  └─ comment → Comment (nullable)         │
                                    │                                          │
                                    │  Follow                                  │
                                    │  ├─ follower → User                      │
                                    │  ├─ post → Post (nullable)               │
                                    │  └─ user → User (nullable, follow person)│
                                    │                                          │
                                    │  Event / EventRegistration               │
                                    │  Notification / UserActivity             │
                                    └──────────────────────────────────────────┘
```

---

## 3. Model Reference

### accounts.User
| Field | Type | Notes |
|---|---|---|
| id | AutoField PK | |
| username, email, password | inherited | AbstractUser |
| full_name | CharField | |
| user_type | CharField | `student` / `professional` / `recruiter` |
| technical_skills | TextField | CSV: `"Python,Django,React"` → `get_skills_list()` |
| projects | TextField | JSON string → `get_projects()` returns `[{title, description, technologies, link}]` |
| internships | TextField | JSON string → `get_internships()` |
| certifications | TextField | JSON string → `get_certifications()` |
| university, degree, cgpa | CharField/Float | Education details |
| objective | TextField | Professional summary |
| linkedin_profile, github_profile, portfolio_website | URLField | |
| is_email_verified | BooleanField | OTP email flow |
| profile_picture | ImageField | |

### assessments.Skill
| Field | Type | Notes |
|---|---|---|
| id | AutoField PK | |
| category | FK → SkillCategory | |
| name | CharField | e.g. "Python", "Machine Learning" |
| difficulty | CharField | `beginner` / `intermediate` / `advanced` |
| questions_generated | BooleanField | **Never regenerate if True** |

### assessments.AssessmentAttempt
| Field | Type | Notes |
|---|---|---|
| user | FK → User | |
| skill | FK → Skill | |
| score | IntegerField | Out of 20 |
| passed | BooleanField | score ≥ 12 (60%) |
| proficiency_level | FloatField | 0–10 scale |
| shuffle_seed | IntegerField | Per-user option shuffling (anti-cheat) |
| selected_question_ids | JSONField | 20 questions: 8 easy, 6 medium, 6 hard |

### recruiter.Job
| Field | Type | Notes |
|---|---|---|
| id | AutoField PK | |
| posted_by | FK → User (recruiter) | |
| title, company, location | CharField | |
| job_type | CharField | Full-time / Part-time / Remote / Contract / Internship |
| skills | JSONField | `[{name, proficiency_required}]` |
| status | CharField | `Open` / `Closed` / `Draft` |
| created_at | DateTimeField | auto_now_add |

### recruiter.Application
| Field | Type | Notes |
|---|---|---|
| job | FK → Job | |
| applicant | FK → User | |
| status | CharField | pending / reviewed / interview / accepted / rejected / withdrawn |
| score | FloatField | ML fit score from Random Forest |
| cover_letter | TextField | |
| applied_at | DateTimeField | |

### learning.SkillGap
| Field | Type | Notes |
|---|---|---|
| user | FK → User | |
| skill | FK → Skill | |
| current_level | FloatField | From UserSkillScore (0–10) |
| required_level | FloatField | From job requirement |
| gap_size | FloatField | required − current |
| related_job | FK → Job (nullable) | Which job triggered this gap |

---

## 4. System Execution Flow

### Startup
```
manage.py runserver
    └─ backend/settings.py  (loads .env: SECRET_KEY, GOOGLE_API_KEY, DATABASE_URL)
    └─ backend/urls.py       (routes to 9 app url namespaces)
    └─ context_processors    (inject user data into every template)
```

### Request Lifecycle
```
HTTP Request
    ↓
Django Middleware (CSRF, Auth, Session)
    ↓
URL Router → App URLs → View function
    ↓
View: queries DB, calls AI/ML services if needed
    ↓
Template rendering (Jinja-compatible Django templates)
    ↓
HTTP Response (HTML / JSON / PDF / redirect)
```

---

## 5. Key User Journeys

### Journey 1 — New User Registration & Email Verification
```
GET /accounts/register/
    → User fills form (name, email, password, user_type)
    → accounts/views.py: create User (is_email_verified=False)
    → Send OTP via Gmail SMTP (accounts/utils.py)
GET /accounts/verify-email/
    → User enters OTP → is_email_verified=True
    → Redirect to dashboard
```

### Journey 2 — Student Takes Skill Assessment
```
Job detail page → "Add Skill & Take Assessment" button
    ↓
jobs/views.py: claim_skill_from_job()
    → Create UserSkillScore(status='claimed')
    ↓
assessments/views.py: start_assessment()
    → Load QuestionBank for skill (20 questions: 8E/6M/6H)
    → Create AssessmentAttempt(shuffle_seed=random)
    → Shuffle options per user using seed (anti-cheat)
    ↓
User answers 20 MCQs
    ↓
assessments/views.py: submit_assessment()
    → Compare chosen_answer vs correct_answer (TEXT match, not index)
    → Calculate score/20
    → passed = score >= 12
    → proficiency_level = (score/20) * 10
    → Update UserSkillScore(status='verified', proficiency_level=X)
    ↓
Redirect to results page
    → Trigger learning path suggestion if skill gap detected
```

### Journey 3 — Job Recommendation Engine
```
User visits /jobs/
    ↓
jobs/views.py: job_listings()
    ↓
jobs/recommendation_engine.py: ContentBasedRecommender
    → Load user skills (UserSkillScore verified + profile CSV)
    → Load all open jobs
    → For each job:
        Jaccard similarity on skill names     (40% weight)
        Coverage: % of required skills met    (60% weight)
    → Score = weighted combination → 0.0 to 1.0
    → Sort descending, return top N
    ↓
Template renders score ring SVG (percentage * 100)
Applied badge shown if job.id in applied_job_ids
Bookmark icon if job.id in bookmarked_job_ids
```

### Journey 4 — AI Skill Gap → Learning Path
```
After assessment: gap detected
    ↓
learning/views.py: generate_learning_path()
    ↓
learning/learning_path_generator.py
    → Build prompt: user skills + required skills + skill gap
    → Google Gemini API call (gemini-1.5-flash)
    → Parse JSON response: [{course_title, provider, url, reason}]
    ↓
Save LearningPath + LearningPathCourse records
    ↓
Dashboard shows personalized course list
```

### Journey 5 — Resume Builder → AI Tailoring → PDF
```
Resume Builder Dashboard
    ↓
User selects template → Resume object created
    ↓
edit_resume view:
    → User configures style (colors, font)
    → Section toggles (show_experience, show_projects etc.)
    → Per-item selection: checkboxes choose which projects/
      experience/internships/certifications to include
      (saved as JSON index arrays in Resume model)
    ↓
"Tailor for Job" button on job detail page
    ↓
resume_builder/ai_views.py: tailor_for_job()
    → Build diff: user profile vs job requirements
    → Gemini API → [{section, type, current, suggested, reason, priority}]
    → Save TailoredResume(status='analyzing' → 'reviewed')
    ↓
AI Review page: user accepts/rejects each suggestion
    ↓
apply_and_finalize() → saves tailored_skills, tailored_objective etc.
    ↓
customize_tailored_sections() → per-item selection for tailored resume
    ↓
download_tailored_resume() → ReportLab PDF generation → HTTP response
```

### Journey 6 — Recruiter Posts Job & Reviews Candidates
```
Recruiter logs in (/recruiter/)
    ↓
Post job form: title, company, skills [{name, proficiency_required 1-10}]
    ↓
recruiter/views.py: saves Job(posted_by=request.user)
    ↓
Students apply → Application objects created
    ↓
Recruiter views applicants:
    → recruiter/skill_based_matching_engine.py
    → Random Forest model scores each applicant
    → Ranked list with fit score
    → Status updates: pending → reviewed → interview → accepted/rejected
```

---

## 6. AI & ML Pipeline

### Google Gemini API (assessments/ai_service.py, learning/learning_path_generator.py)
```
Input: skill name + difficulty level
    ↓
Prompt construction → Gemini 1.5 Flash API call
    ↓
Parse JSON response → QuestionBank records
    ↓
questions_generated = True (NEVER regenerate)
```

```
Input: user skill profile + skill gap details
    ↓  
Prompt → Gemini → JSON course list
    ↓
LearningPath + LearningPathCourse records
```

### ML Recommendation (jobs/recommendation_engine.py)
```
Algorithm: ContentBasedRecommender
Input vectors:
    - User skill set (from UserSkillScore + profile CSV)
    - Job skill set (from Job.skills JSONField)

Score = 0.4 × Jaccard(user_skills, job_skills)
      + 0.6 × coverage(required_skills ∩ user_skills) / len(required_skills)

Output: float 0.0–1.0 per job
```

### ML Candidate Ranking (recruiter/skill_based_matching_engine.py)
```
Features: UserSkillScore values for each required skill
Model: Random Forest Classifier (scikit-learn)
    → fit on existing application outcomes
    → predict fit score for new applicants
Output: ranked applicant list
```

---

## 7. API & URL Map

| App | URL Pattern | View | Description |
|---|---|---|---|
| accounts | `/accounts/register/` | register | User signup + OTP send |
| accounts | `/accounts/login/` | login | Login with verification check |
| accounts | `/accounts/verify-email/` | verify_email | OTP validation |
| assessments | `/assessments/start/<skill_id>/` | start_assessment | Create attempt |
| assessments | `/assessments/take/<attempt_id>/` | take_assessment | MCQ page |
| assessments | `/assessments/submit/<attempt_id>/` | submit_assessment | Grade + save |
| jobs | `/jobs/` | job_listings | Main listings + recommendations |
| jobs | `/jobs/<job_id>/` | job_detail | Job detail + Apply Now |
| jobs | `/jobs/bookmark/<job_id>/` | toggle_bookmark | AJAX bookmark |
| recruiter | `/recruiter/post-job/` | post_job | Recruiter creates job |
| recruiter | `/recruiter/applications/<job_id>/` | view_applications | Ranked candidates |
| learning | `/learning/path/<gap_id>/` | learning_path_detail | AI course list |
| resume_builder | `/resume/edit/<id>/` | edit_resume | Builder UI |
| resume_builder | `/resume/tailored/customize/<id>/` | customize_tailored_sections | Per-item selection |
| resume_builder | `/resume/tailored/download/<id>/` | download_tailored_resume | PDF export |
| resume_builder | `/resume/ai/tailor/<job_id>/` | tailor_for_job | Trigger AI tailoring |
| community | `/community/` | community_feed | Forum feed |
| community | `/community/toggle-like/` | toggle_like | AJAX like |
| dashboard | `/dashboard/` | home | Central analytics hub |

---

## 8. Data Flow Between Apps

```
┌──────────────┐
│   accounts   │  User created here — all other apps FK to User
│   (User)     │
└──────┬───────┘
       │
       ├──────────────────────────────────────────────────┐
       │                                                  │
       ▼                                                  ▼
┌─────────────┐   Application.job_id    ┌──────────────────┐
│  recruiter  │ ◄───────────────────── │      jobs        │
│  (Job,      │                         │  (JobBookmark,   │
│  Application│ ──────────────────────► │  JobRecommend,   │
│  Message)   │   Job.id used as FK     │  UserPreference) │
└──────┬──────┘                         └──────────────────┘
       │ claim_skill_from_job()
       │ (creates UserSkillScore status=claimed)
       ▼
┌──────────────────┐
│  assessments     │  skill → QuestionBank → AssessmentAttempt → UserAnswer
│  (Skill,         │
│  UserSkillScore) │ ─────── proficiency_level ──────────────────────────────┐
└──────────────────┘                                                         │
       │  gap detected                                                        │
       ▼                                                                      │
┌──────────────┐                                                              │
│   learning   │  SkillGap → LearningPath (Gemini API) → CourseProgress      │
│              │                                                              │
└──────────────┘                                                              │
       │  tailored resume triggered from job                                  │
       ▼                                                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  resume_builder                                                          │
│  Resume (user selections) → TailoredResume (AI suggestions + per-item)  │
│  → PDF download via ReportLab                                            │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│  dashboard   │  Aggregates: skill scores + applications + recommendations
│  community   │  Posts / Comments / Events (independent social layer)
└──────────────┘
```

---

## Running the Project Locally

```bash
# 1. Clone & activate venv
git clone https://github.com/akramnameemuddin/job-elevate.git
cd job-elevate
python -m venv venv
source venv/Scripts/activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Create backend/backend/.env with:
# SECRET_KEY=your-secret-key
# GOOGLE_API_KEY=your-gemini-key   ← https://aistudio.google.com/app/apikey
# EMAIL_HOST_USER=your@gmail.com
# EMAIL_HOST_PASSWORD=app-password
# DATABASE_URL=sqlite:///db.sqlite3

# 4. Migrate & seed
cd backend
python manage.py migrate
python manage.py add_questions          # populate MCQ bank
python manage.py populate_assessment_data
python manage.py seed_community_posts   # demo community content

# 5. Run
python manage.py runserver
# → http://127.0.0.1:8000/
```

---

*Generated from source: March 2026 — commit 281c92fb*
