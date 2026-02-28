# JobElevate — AI-Powered Job Matching & Upskilling Platform

> **Live Demo:** [job-elevate-m96p.onrender.com](https://job-elevate-m96p.onrender.com)
> **Tech Stack:** Django 5.1 · Python 3.12 · Google Gemini AI · scikit-learn · PostgreSQL · Render

---

## Table of Contents
1. [What It Solves](#1-what-it-solves)
2. [Live Demo & Deployment](#2-live-demo--deployment)
3. [Quick Setup](#3-quick-setup)
4. [Architecture](#4-architecture)
5. [Feature Map](#5-feature-map)
6. [Evaluation Criteria Compliance](#6-evaluation-criteria-compliance)
7. [API Reference](#7-api-reference)
8. [Testing](#8-testing)
9. [Security Notes](#9-security-notes)
10. [Known Limitations & Version 2.0](#10-known-limitations--version-20)
11. [Team & Acknowledgements](#11-team--acknowledgements)

---

## 1. What It Solves

**The Problem:** Fresh graduates and early-career professionals in India cannot see which skills they lack for jobs they want, cannot verify those skills credibly, and cannot get a personalised learning plan to close the gap — all in one place.

**Who faces this problem:** First- and second-year engineering students and professionals with 0–3 years of experience applying to technical roles, who receive no structured feedback from recruiters about why they were rejected.

**Current workaround:** Candidates blindly apply on Naukri/LinkedIn, guess at skill gaps, and cobble together random YouTube playlists with no verification they learned anything.

**What we solve vs. NOT solve:**
- YES: Skill gap identification against a specific job description
- YES: AI-proctored skill assessments (MCQ with anti-cheat shuffling)
- YES: Personalised learning path generation (Google Gemini)
- YES: ML-based job matching (hybrid cosine similarity + Jaccard)
- YES: ATS-compliant resume export (PDF)
- NO: Video interviews
- NO: External LMS integration (Coursera, Udemy) in v1

**Evidence the problem exists:**
- LinkedIn India 2023 report: 67% of recruiters say candidates lack proof of claimed skills.
- A 20-person survey among 3rd and 4th-year VVIT students confirmed: 18/20 said they "apply randomly without knowing their skill fit."

**Success criteria (measurable):**
- A user can identify their skill gaps for any posted job in < 2 minutes.
- A user can take and pass a skill assessment in < 15 minutes.
- 80% of test users can navigate from registration to their first job match without help.

---

## 2. Live Demo & Deployment

| Property | Value |
|---|---|
| Production URL | https://job-elevate-m96p.onrender.com |
| Hosting | Render.com (free tier) |
| Database | PostgreSQL (Render managed) |
| Static files | WhiteNoise (served directly by Gunicorn) |
| Process manager | Gunicorn 21.2 |

**Test Accounts:**

| Role | Email | Password |
|---|---|---|
| Student | `student@demo.com` | `Demo@1234` |
| Recruiter | `recruiter@demo.com` | `Demo@1234` |

---

## 3. Quick Setup

### Prerequisites
- Python 3.10+ (tested on 3.12.8)
- Git
- A Gmail App Password for OTP email
- A Google AI Studio API key — [get one free here](https://aistudio.google.com/app/apikey)

### Steps

```bash
# 1. Clone
git clone https://github.com/your-username/job-elevate.git
cd job-elevate

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

Create `backend/backend/.env`:
```env
SECRET_KEY=your-random-50-char-secret-key
DEBUG=True
GOOGLE_API_KEY=your-gemini-api-key
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

```bash
# 4. Migrate and seed
cd backend
python manage.py migrate
python manage.py add_questions            # populate skill question bank
python manage.py populate_assessment_data # create skill categories

# 5. Run
python manage.py runserver
```

Open http://127.0.0.1:8000

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | YES | Django secret key (50+ random chars) |
| `DEBUG` | YES | `True` for dev, `False` for prod |
| `GOOGLE_API_KEY` | YES | Gemini API key for AI features |
| `EMAIL_HOST_USER` | YES | Gmail address for OTP emails |
| `EMAIL_HOST_PASSWORD` | YES | Gmail App Password |
| `DATABASE_URL` | YES | SQLite path (dev) or PostgreSQL URL (prod) |
| `ALLOWED_HOSTS` | YES | Comma-separated hostnames |

---

## 4. Architecture

### High-Level Diagram

```
Browser --> HTTPS --> Gunicorn/WhiteNoise (Render.com)
                            |
                      Django 5.1 (MVT)
            +-----------+  +----------+  +----------+
            | accounts  |  |   jobs   |  |assessments|
            +-----------+  +----------+  +----------+
            +-----------+  +----------+  +----------+
            | recruiter |  |community |  | learning |
            +-----------+  +----------+  +----------+
            +-----------+  +----------+  +----------+
            | dashboard |  |  agents  |  |  resume  |
            +-----------+  +----------+  +----------+
                   |               |
           PostgreSQL        Google Gemini AI
           (SQLite dev)      Gmail SMTP (OTP)
```

### App Responsibilities

| App | Responsibility | Key Models |
|---|---|---|
| `accounts` | Custom User, registration, OTP verification, login | `User` (AbstractUser) |
| `jobs` | Job listings, ML recommendation engine | `Job`, `JobApplication` |
| `assessments` | Skill intake, MCQ assessments, anti-cheat | `Skill`, `QuestionBank`, `AssessmentAttempt`, `UserSkillScore` |
| `learning` | Skill gap analysis, AI learning paths | `LearningPath`, `SkillGap`, `Course` |
| `recruiter` | Job posting, applicant tracking | `JobPosting`, `RequiredSkill` |
| `community` | Forum posts, comments, likes | `Post`, `Comment` |
| `dashboard` | Central navigation, analytics | (aggregates from other apps) |
| `agents` | Google ADK career & recruiter AI | `CareerAgent`, `RecruiterAgent` |
| `resume_builder` | ATS resume generation, PDF export | `Resume`, `ResumeSection` |
| `ml` | Clustering and recommendation utilities | Utility module |

### Why Django Monolith?

We chose Django deliberately:
- **Pros:** Shared ORM eliminates serialisation overhead; Django admin accelerated development; single deployment unit reduces ops complexity for a college project.
- **Trade-off:** Horizontal scaling requires sticky sessions or shared Redis. For microservices, the natural split is: Auth Service + Recommendation Service + AI Service.
- **Bottleneck at 10x users:** The recommendation engine (`jobs/recommendation_engine.py`) runs a full cosine similarity matrix in-process. Fix: Celery background task or dedicated FastAPI service.

---

## 5. Feature Map

### Student / Professional Flow
1. **Register** — email OTP verification (6-digit, 10-min expiry)
2. **Profile Setup** — skills, work experience, projects (JSON fields)
3. **Browse Jobs** — see ML match score (0-100%) per listing
4. **Skill Gap View** — see exactly which required skills you are missing
5. **Take Assessment** — 20 MCQs (8 easy / 6 medium / 6 hard), shuffled per user
6. **Learning Path** — AI-generated course recommendations based on verified gaps
7. **Community** — forum posts, comments, likes
8. **Resume Builder** — generate ATS-optimised PDF resume

### Recruiter Flow
1. **Register as Recruiter** — separate dashboard
2. **Post Job** — specify required skills with proficiency levels (1-10)
3. **View Applicants** — ranked by ML match score
4. **Track Status** — shortlisted / hired / rejected

---

## 6. Evaluation Criteria Compliance

### Criterion 1 — Problem Definition & Motivation (10 marks)

| Sub-criterion | Evidence |
|---|---|
| Precise problem statement | "Fresh graduates cannot identify, verify, or close skill gaps for specific job listings in one integrated platform." |
| Specific target users | Students (0-2 YOE) and professionals (0-5 YOE) in technical roles; recruiters at SME tech companies |
| Current workaround | Random job applications on Naukri/LinkedIn with no skill feedback loop |
| Scope boundary | In scope: assessment, matching, learning. Out of scope: video interviews, LMS integration |
| Real-world evidence | LinkedIn India Skills Report 2023; 20-person VVIT student survey (18/20 apply randomly) |
| Concrete scenario | A 3rd-year student applies for a Python backend role, does not know they lack Docker & PostgreSQL, gets rejected silently — JobElevate shows the gap immediately |
| Competitive analysis | LinkedIn (no assessments tied to job gaps), HackerEarth (assessments only, no matching), Naukri (no skill gap view) |
| Our differentiator | Only platform that ties: job posting → skill gap → AI assessment → personalised learning path in one workflow |
| Measurable success | Skill gap visible in < 2 min; assessment done in < 15 min; 80% new-user task completion unaided |

---

### Criterion 2 — System Design & Architecture (15 marks)

| Sub-criterion | Evidence |
|---|---|
| Architecture diagram | See Section 4 — component diagram with layers |
| Architectural style justification | Django monolith: shared ORM, admin acceleration, single-unit deployment — trade-offs documented in Section 4 |
| Scalability bottleneck identified | Recommendation engine (in-process cosine similarity); fix: Celery async task |
| Separation of concerns | 10 Django apps, single responsibility each; templates / views / models / services cleanly separated |
| Business logic separate from UI | `recommendation_engine.py`, `learning_path_generator.py`, `ai_service.py` are pure Python — zero HTML |
| Database swap impact | Django ORM: SQLite → PostgreSQL required only `DATABASE_URL` env var change, zero code changes |
| Schema design | AbstractUser, FK with `on_delete=CASCADE`, M2M for skills, indexes on `email` and FK columns |
| API design | HTTP verbs correct (GET/POST/PUT/DELETE); structured JSON error responses; see Section 7 |
| Async awareness | OTP email currently sync (acceptable); production plan is Celery + Redis |

**Technology Choices & Justification:**

| Technology | Chosen over | Reason |
|---|---|---|
| Django 5.1 | FastAPI, Flask | Built-in admin, ORM, auth, migrations — batteries-included for 10-app project |
| PostgreSQL | MySQL | Better JSONB support (projects/certifications stored as JSON), superior full-text search |
| Google Gemini Flash | OpenAI GPT-4 | Free tier adequate; lower latency for real-time assessment paths |
| scikit-learn | PyTorch | Cosine similarity on small vectors does not need deep learning; 10x faster to iterate |
| Render.com | Heroku, Railway | Free PostgreSQL + zero-downtime deploys from GitHub |
| WhiteNoise | Nginx, S3 | Static files via WSGI without extra infrastructure |

---

### Criterion 3 — Code Quality & Engineering Practices (15 marks)

**Naming & Readability — self-documenting function names:**
```python
# assessments/views.py
def start_assessment_direct(request, skill_id): ...
def submit_assessment(request, attempt_id): ...

# jobs/recommendation_engine.py
def calculate_jaccard_similarity(user_skills, job_skills): ...
def get_recommendations_for_user(user, limit=10): ...
```

**Coding style:** PEP 8 snake_case throughout all 10 apps; consistent 4-space indentation.

**DRY utility functions shared across apps:**

| Utility | Location | Used by |
|---|---|---|
| `get_skills_list()` | `accounts/models.py` | jobs, assessments, learning, dashboard |
| `calculate_skill_match_score()` | `jobs/skill_based_matching_engine.py` | views, recommendation engine, recruiter |
| `generate_learning_path()` | `learning/learning_path_generator.py` | learning views, dashboard context |
| `get_skill_gaps()` | `jobs/skill_gap_helpers.py` | jobs views, learning views, dashboard |

**Exception handling:**
```python
# assessments/ai_service.py — catches AI failures, falls back gracefully
try:
    questions = generate_with_gemini(skill_name, difficulty)
except google.api_core.exceptions.ResourceExhausted:
    logger.warning("Gemini quota exceeded, falling back to template questions")
    questions = get_template_questions(skill_name, difficulty)
except Exception as e:
    logger.error(f"AI question generation failed: {e}")
    questions = get_template_questions(skill_name, difficulty)
```

**Secrets management:** `.env` excluded via `.gitignore`. No credentials in any commit.

**Technical debt acknowledged:**
- `technical_skills` stored as CSV string (legacy) — bridged by `get_skills_list()`; M2M migration in v2.
- `assessments/views.py:submit_assessment` is longer than ideal — refactor target for v2.

---

### Criterion 4 — Functionality & Feature Completeness (15 marks)

**Core user flows (all functional end-to-end on live production):**

| Flow | Entry URL | Result | Status |
|---|---|---|---|
| Registration + OTP | `/accounts/signup/` | Dashboard redirect after OTP | Live |
| Job match score | `/jobs/` | Match % on each card | Live |
| Skill assessment | `/assessments/start/<id>/` | Score + proficiency level | Live |
| Learning path | `/learning/paths/` | AI course recommendations | Live |
| Resume PDF export | `/resume/` | Downloads PDF file | Live |
| Recruiter post job | `/recruiter/post/` | Job visible to candidates | Live |

**Edge cases handled:**

| Edge case | Handling |
|---|---|
| Duplicate registration | `unique=True` on `User.email` — "Email already registered" form error |
| Double form submission | POST-redirect-GET; `AssessmentAttempt` status flag prevents re-takes |
| Empty form submission | Server-side Django form validation + client-side `required` attributes |
| Gemini API unavailable | Falls back to 50 pre-seeded template questions per skill |
| Unauthenticated access | `@login_required` on all non-public views |
| Non-existent resource | `get_object_or_404()` on all detail views — clean 404 page |
| Proficiency out of range | `MinValueValidator(0)`, `MaxValueValidator(10)` on FloatField |

**Feature prioritisation (MoSCoW):**
- Must have (built): Registration, skill assessment, job matching, learning paths
- Should have (built): Forum, resume builder, recruiter dashboard
- Could have (partial): AI chat agents (Google ADK) — functional but not polished
- Will not have v1: Video interviews, LMS integration, mobile app

**Fresh-database test:** `manage.py add_questions` populates everything from zero — no hidden preconditions.

---
### Criterion 5 — Testing (10 marks)

**107 tests, 0 failures, 0 errors**

```bash
cd backend
python manage.py test
# Ran 107 tests in ~8s  OK
```

**Test coverage by app:**

| App | Test file | Focus |
|---|---|---|
| `accounts` | `accounts/tests.py` | Signup OTP flow, login (valid/invalid/unverified), logout, profile redirect |
| `recruiter` | `recruiter/tests.py` | Dashboard access, job CRUD, application status, model |
| `community` | `community/tests.py` | Access control, post creation, post detail, toggle likes, slug auto-gen |
| `dashboard` | `dashboard/tests.py` | Home (student/pro/recruiter), profile GET/POST, context keys |
| `learning` | `learning/tests.py` | Dashboard, skill gaps, course catalog, models |
| `assessments` | `assessments/tests.py` | All models, skill intake, browse, start-from-job, attempt |

**Test types covered:**
- Unit tests — model methods (`calculate_percentage`, `is_passing`, `success_rate`, `get_skills_list`)
- Integration tests — full HTTP request → view → template → response cycles
- Negative tests — wrong password, unverified email, unauthenticated access all return correct errors
- Boundary tests — empty forms, duplicate email registration
- Role-based access — recruiter views redirect/403 for student users

**Standalone workflow tests:**
```bash
python test_workflow.py
python test_assessment_20q.py
python test_recommendation_accuracy.py
python test_skill_matching_only.py
```

---

### Criterion 6 — Security Awareness (10 marks)

**Password Storage:**
Django PBKDF2-SHA256 with 720,000 iterations (exceeds OWASP recommended minimum). Passwords are never stored in plain text and are never logged.

**Security headers — always active (not DEBUG-only) in `settings.py`:**
```python
X_FRAME_OPTIONS = 'DENY'               # clickjacking prevention
SECURE_CONTENT_TYPE_NOSNIFF = True     # MIME-sniffing prevention
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

**Production-only (when `DEBUG=False`):**
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**IDOR Prevention — every object lookup is owner-scoped:**
```python
attempt = get_object_or_404(AssessmentAttempt, pk=attempt_id, user=request.user)
job_posting = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)
```

**SQL Injection Prevention:** Django ORM exclusively — no raw SQL. All user input parameterised automatically.

**CSRF Protection:** `CsrfViewMiddleware` active on all POST forms. All forms include `{% csrf_token %}`.

**Secrets Management:** `.env` excluded via `.gitignore`. No credentials in any Git commit.

**OWASP Top 10 Mapping:**

| OWASP Risk | Status | Implementation |
|---|---|---|
| A01 Broken Access Control | Mitigated | `@login_required`, role checks, IDOR-safe lookups |
| A02 Cryptographic Failures | Mitigated | PBKDF2-SHA256, HTTPS enforced in prod, HSTS |
| A03 Injection | Mitigated | Django ORM only, no raw queries |
| A04 Insecure Design | Mitigated | OTP expiry enforced, auth flow reviewed |
| A05 Security Misconfiguration | Mitigated | `DEBUG=False` in prod, security headers always on |
| A06 Vulnerable Components | Monitored | `pip-audit` run before release |
| A07 Authentication Failures | Mitigated | OTP required; Django-Axes for rate limiting in v2 |
| A08 Software & Data Integrity | Mitigated | CSRF tokens, POST-redirect-GET pattern |
| A09 Logging & Monitoring | Mitigated | Django logging to file in production |
| A10 SSRF | Mitigated | External calls only to Gemini API (allow-listed domain) |

---

### Criterion 7 — UI/UX & User Interaction (5 marks)

| Principle | Implementation |
|---|---|
| Consistency | Tailwind CSS utility classes throughout; same navbar, card pattern, button styles across all apps |
| Feedback on every action | Django messages framework — green success / red error banners on every form submission |
| Inline error messages | Human-readable field errors inline next to each field; no raw 500 pages shown to users |
| Loading states | Spinner shown during assessment submission (prevents double-click) |
| Responsive design | Tailwind breakpoints (`sm:`, `md:`, `lg:`) — tested on mobile, tablet, desktop |
| Role-based UI | Student sees skill gaps; recruiter sees applicants — no irrelevant UI shown |
| Empty states | Custom empty-state illustrations when no jobs/skills/posts exist |
| Progress visibility | Assessment shows "Question X of 20" |

---

### Criterion 8 — Performance Awareness (5 marks)

**Identified bottlenecks and mitigations applied:**

| Bottleneck | Problem | Fix |
|---|---|---|
| N+1 on job listing | Each card triggered separate DB query for skills | `prefetch_related('required_skills')` in `jobs/views.py` |
| Recommendation engine | Full skill matrix recomputed every page load | Cached per user on profile change |
| AI question generation | Gemini call = ~2s latency | `Skill.questions_generated` flag — generated ONCE, stored in `QuestionBank` |
| Static asset size | Uncompressed CSS/JS | WhiteNoise gzip compression in production |
| Dashboard aggregation | Multiple cross-app queries | `select_related()` on User queries; context processors avoid duplicates |

**Database query awareness:**
```python
# jobs/views.py — avoids N+1
jobs = Job.objects.all()
    .select_related('posted_by')
    .prefetch_related('required_skills')
    .order_by('-created_at')
```

**Frontend:** Tailwind CSS purged in production; images `loading="lazy"`; no blocking JS in `<head>`.

**API:** Gemini calls have 10s timeout — avoids hanging requests.

---

### Criterion 9 — Documentation (5 marks)

This README is the primary documentation entry point. Additional documentation:

**Inline docstrings:**
```python
def calculate_jaccard_similarity(user_skills: list, job_skills: list) -> float:
    """
    Calculate Jaccard similarity between user skill set and job required skills.
    Jaccard = |intersection| / |union|. Returns float in [0.0, 1.0].
    """
```

**Additional docs in `backend/`:**

| File | Contents |
|---|---|
| `ASSESSMENT_STATUS.md` | Anti-cheat system design decisions |
| `ASSESSMENT_WORKFLOW.md` | Step-by-step assessment lifecycle |
| `WORKFLOW_FIXED.md` | Skill claim → assessment → score update flow |
| `MODELS_AUDIT.md` | All model fields, types, and relationships |
| `POPULATE_QUESTIONS_README.md` | How to seed the question bank |

**Key design decisions documented:**
- `technical_skills` as CSV: legacy decision bridged by `get_skills_list()`; M2M migration in v2.
- Questions cached in `QuestionBank`: Gemini free-tier quota protection — generate once, reuse always.
- `shuffle_seed` in `AssessmentAttempt`: reproducible shuffling prevents guess-and-refresh cheating.

---

### Criterion 10 — Presentation & Defence (10 marks)

**2-minute architecture pitch:**

"JobElevate is a Django monolith with 10 apps. A student registers, their email is verified via OTP, they browse jobs and see an ML-computed match score. Clicking 'Show Skill Gap' calls our Jaccard-similarity engine against the job's required skills. Clicking 'Take Assessment' creates an `AssessmentAttempt`, selects 20 questions from `QuestionBank` (8 easy / 6 medium / 6 hard), shuffles options using a per-attempt seed, and presents them. On submission, we score the attempt (60% = pass), update `UserSkillScore` from 'claimed' to 'verified', and feed the gap into our Gemini-powered learning path generator. The recruiter side mirrors this in reverse."

**What we would change in v2:**
1. `technical_skills` CSV → M2M relationship
2. Synchronous email → Celery + Redis task queue
3. In-process recommendation scoring → dedicated service with caching
4. Django-Axes for login rate limiting
5. Celery Beat for periodic recommendation refresh

**Conscious trade-offs:**
- SQLite in dev (faster setup) → PostgreSQL in prod (ACID compliance, concurrent writes)
- Server-rendered templates over React SPA (faster to build, sufficient for current scale)
- Gemini Flash over GPT-4 (free tier, adequate quality for MCQ generation)

---

### Bonus — AI & ML Integration

**1. ML Recommendation Engine** (`jobs/recommendation_engine.py`)
- Hybrid model: 40% Jaccard skill similarity + 60% skill coverage score
- Returns match scores 0.0-1.0 per (user, job) pair
- Handles both legacy (string) and new (dict with proficiency) skill formats

**2. AI Skill Assessment** (`assessments/ai_service.py`)
- Gemini gemini-2.5-flash-lite generates 20 MCQ questions per skill × 3 difficulty levels
- Stored in `QuestionBank` — never regenerated (quota protection)
- Anti-cheat: `shuffle_seed` per attempt, correct answers as text not index

**3. AI Learning Path Generator** (`learning/learning_path_generator.py`)
- Accepts verified skill gaps as input, prompts Gemini with JSON schema
- Returns ordered course list with title, platform, duration, rationale
- Falls back to static curated paths if API unavailable

**4. Google ADK Agents** (`agents/`)
- `career_agent.py` — answers career questions using user profile as context
- `recruiter_agent.py` — helps recruiters write better job descriptions
- `google-adk>=1.0.0` with `gemini-2.0-flash`
- Circuit breaker (`circuit_breaker.py`) prevents cascade failures

---

## 7. API Reference

Authentication via Django session cookie (CSRF token required for POST/PUT/DELETE).

### Authentication

| Method | URL | Description | Auth |
|---|---|---|---|
| `POST` | `/accounts/signup/step1/` | Register — send OTP | No |
| `POST` | `/accounts/signup/step2/` | Verify OTP | No |
| `POST` | `/accounts/login/` | Login | No |
| `POST` | `/accounts/logout/` | Logout | Yes |

### Jobs

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/jobs/` | List jobs with match scores | Yes |
| `GET` | `/jobs/<id>/` | Job detail + skill gap | Yes |
| `POST` | `/jobs/<id>/apply/` | Apply for a job | Yes |
| `GET` | `/jobs/recommendations/` | ML-ranked recommendations | Yes |
| `POST` | `/jobs/<id>/claim-skill/<skill_id>/` | Claim skill → start assessment | Yes |

### Assessments

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/assessments/` | Skill intake dashboard | Yes |
| `GET` | `/assessments/browse/` | Browse skills | Yes |
| `POST` | `/assessments/start/<skill_id>/` | Start attempt | Yes |
| `GET` | `/assessments/take/<attempt_id>/` | View questions | Yes |
| `POST` | `/assessments/submit/<attempt_id>/` | Submit answers | Yes |
| `GET` | `/assessments/result/<attempt_id>/` | View result | Yes |

### Learning

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/learning/` | Learning dashboard | Yes |
| `GET` | `/learning/skill-gaps/` | Skill gap analysis | Yes |
| `GET` | `/learning/courses/` | Course catalog | Yes |
| `POST` | `/learning/generate-path/` | Generate AI learning path | Yes |

### Recruiter

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/recruiter/dashboard/` | Recruiter dashboard | Recruiter |
| `POST` | `/recruiter/jobs/create/` | Post job | Recruiter |
| `GET` | `/recruiter/jobs/<id>/applicants/` | View applicants | Recruiter |
| `POST` | `/recruiter/applications/<id>/status/` | Update status | Recruiter |

### Error Response Format

```json
{
  "error": "Brief description",
  "detail": "Human-readable explanation",
  "field_errors": { "email": ["Enter a valid email address."] }
}
```

HTTP codes: `200` success, `201` created, `400` bad input, `401` login required, `403` forbidden, `404` not found, `500` server error (logged, not exposed to user).

---

## 8. Testing

```bash
cd backend
python manage.py test               # all apps — 107 tests
python manage.py test accounts      # accounts only
python manage.py test assessments   # assessments only
python manage.py test jobs          # jobs only

python test_workflow.py                  # end-to-end assessment workflow
python test_assessment_20q.py            # 20-question system validation
python test_recommendation_accuracy.py   # ML match quality metrics
python test_skill_matching_only.py       # skill matching engine
```

---

## 9. Security Notes

- **Never commit `.env`** — it is in `.gitignore`. Use `.env.example` as a template.
- **Gmail App Password** — use [App Passwords](https://myaccount.google.com/apppasswords), not your account password. Requires 2FA.
- **`SECRET_KEY`** — generate fresh per deployment: `python -c "import secrets; print(secrets.token_hex(50))"`
- **`DEBUG=False` in production** — enables HTTPS redirects, HSTS, and secure cookies automatically.
- **Database URL** — always set via environment variable, never hardcoded in source.
- **Gemini API key** — restrict to Generative Language API in Google Cloud Console.

---

## 10. Known Limitations & Version 2.0

### Current Limitations (v1)

| Area | Limitation | Impact |
|---|---|---|
| `technical_skills` storage | CSV string — not normalised | Minor: bridged by `get_skills_list()` |
| Email sending | Synchronous — blocks request | Slight delay on OTP signup |
| Recommendation engine | Runs in-process | Slow beyond ~5,000 jobs |
| Auth rate limiting | No login attempt throttling | Brute-force possible |
| Assessment timing | No server-side time limit | Anti-cheat: users can take unlimited time |

### Version 2.0 Roadmap

- [ ] Migrate `technical_skills` CSV to ManyToManyField
- [ ] Celery + Redis: async email and recommendation refresh
- [ ] Django-Axes: login rate limiting
- [ ] Server-enforced 30-minute assessment timer
- [ ] LMS integration: Coursera/YouTube API for real course links
- [ ] Django Channels + Redis: real-time recruiter notifications
- [ ] Mobile PWA mode
- [ ] Resume parsing: upload PDF to auto-fill profile

---

## 11. Team & Acknowledgements

**Project:** JobElevate — AI-Powered Job Matching & Upskilling Platform
**Institution:** Vasireddy Venkatadri Institute of Technology, Guntur
**Department:** CSE — Artificial Intelligence & Machine Learning
**Academic Year:** 2024-25

**Built with:**
- [Django](https://www.djangoproject.com/) — the web framework for perfectionists with deadlines
- [Google Gemini](https://ai.google.dev/) — AI question generation and learning paths
- [scikit-learn](https://scikit-learn.org/) — ML recommendation engine
- [Tailwind CSS](https://tailwindcss.com/) — utility-first CSS
- [Render.com](https://render.com/) — free-tier cloud deployment

---

*Last updated: June 2025*
