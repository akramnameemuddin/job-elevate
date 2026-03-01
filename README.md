# JobElevate — AI-Powered Job Matching & Upskilling Platform

![Django](https://img.shields.io/badge/Django-5.1.6-092E20?style=flat&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-4285F4?style=flat&logo=google&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=flat&logo=scikitlearn&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-107%20passing-brightgreen?style=flat)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat)
[![CI — Test Suite](https://github.com/akramnameemuddin/job-elevate/actions/workflows/ci.yml/badge.svg)](https://github.com/akramnameemuddin/job-elevate/actions/workflows/ci.yml)
[![CD — Deploy to EC2](https://github.com/akramnameemuddin/job-elevate/actions/workflows/cd.yml/badge.svg)](https://github.com/akramnameemuddin/job-elevate/actions/workflows/cd.yml)
[![Code Quality — Lint](https://github.com/akramnameemuddin/job-elevate/actions/workflows/lint.yml/badge.svg)](https://github.com/akramnameemuddin/job-elevate/actions/workflows/lint.yml)

> **Live (AWS EC2):** [https://jobelevates.akramnaeemuddin.me](https://jobelevates.akramnaeemuddin.me)
> **Live (Render):** [https://job-elevate-m96p.onrender.com](https://job-elevate-m96p.onrender.com)

JobElevate is an end-to-end AI-powered career platform that takes a student or professional from "I don't know what skills I'm missing" to "I have a verified skill profile, a personalised learning path, and an ATS-ready resume" — all in a single integrated workflow. Recruiters get the mirror image: post a job with required skills, and the ML engine ranks every applicant automatically.

---

## Table of Contents

| # | Section | Audience |
|---|---|---|
| 1 | [Problem & Solution](#1-problem--solution) | Everyone |
| 2 | [Live Demo & Test Accounts](#2-live-demo--test-accounts) | Everyone |
| 3 | [Feature Showcase](#3-feature-showcase) | Everyone |
| 4 | [Architecture](#4-architecture) | Developers / Evaluators |
| 5 | [Quick Setup — Local Dev](#5-quick-setup--local-dev) | Developers |
| 6 | [Environment Variables](#6-environment-variables) | Developers / DevOps |
| 7 | [Deployment](#7-deployment) | DevOps |
| 8 | [AI & ML Deep Dive](#8-ai--ml-deep-dive) | Evaluators / Developers |
| 9 | [API Reference](#9-api-reference) | Developers |
| 10 | [Testing](#10-testing) | Evaluators / Developers |
| 11 | [Security](#11-security) | Evaluators |
| 12 | [Performance](#12-performance) | Evaluators |
| 13 | [Evaluation Criteria Compliance](#13-evaluation-criteria-compliance) | Evaluators |
| 14 | [Roadmap](#14-roadmap) | Everyone |
| 15 | [Team & Acknowledgements](#15-team--acknowledgements) | Everyone |

---

## 1. Problem & Solution

### The Problem

Fresh graduates and early-career professionals in India face a silent rejection loop:
- They apply on Naukri/LinkedIn **without knowing which skills they are missing**.
- Recruiters reject them but **never explain why**.
- Candidates randomly watch YouTube playlists with **no way to verify** they learned anything.
- There is **no single platform** that ties: job requirements → skill gap → verified assessment → personalised learning.

> **LinkedIn India 2023:** 67% of recruiters say candidates lack proof of claimed skills.
> **VVIT Student Survey (n=20):** 18 of 20 students said they "apply randomly without knowing their skill fit."

### What JobElevate Solves

| Capability | How |
|---|---|
| **See your exact skill gap** | Compare your verified skills vs. job's required skills in < 2 minutes |
| **Prove your skills** | AI-generated 20-question MCQ per skill, anti-cheat shuffled, scored 0–10 |
| **Get a personalised learning path** | Google Gemini generates an ordered course list based on your specific gaps |
| **Match to relevant jobs** | Hybrid ML engine (Jaccard + cosine similarity) ranks every job by your actual fit |
| **Build an ATS resume** | PDF export with three professional templates |
| **Recruiter side** | Post jobs with skill requirements; get candidates ranked by ML match score |

### What We Explicitly Do NOT Solve (v1)
- Video interviews
- External LMS integration (Coursera, Udemy) — v2 roadmap
- Mobile native app

### Competitive Position

| Platform | Skill Gap View | Verified Assessment | AI Learning Path | Job Matching |
|---|---|---|---|---|
| Naukri | ✗ | ✗ | ✗ | Basic keyword |
| LinkedIn | Partial | LinkedIn Learning only | ✗ | Profile-based |
| HackerEarth | ✗ | ✓ | ✗ | ✗ |
| **JobElevate** | **✓** | **✓ (AI-generated)** | **✓ (Gemini)** | **✓ (ML hybrid)** |

---

## 2. Live Demo & Test Accounts

### Production Deployments

| Deployment | URL | Infrastructure |
|---|---|---|
| AWS EC2 | [https://jobelevates.akramnaeemuddin.me](https://jobelevates.akramnaeemuddin.me) | Ubuntu 24.04 · Gunicorn · Nginx · RDS PostgreSQL · S3 |
| Render.com | [https://job-elevate-m96p.onrender.com](https://job-elevate-m96p.onrender.com) | Render managed PostgreSQL · WhiteNoise |

### Test Accounts (both deployments)

| Role | Email | Password | What you can do |
|---|---|---|---|
| Student | `student@demo.com` | `Demo@1234` | Browse jobs, take assessments, view learning paths, build resume |
| Recruiter | `recruiter@demo.com` | `Demo@1234` | Post jobs, view applicants, track application status |

### Suggested Demo Walkthrough (5 minutes)

1. Log in as **Student** → go to **Job Matches**
2. Click any job → see your **ML match score** and **skill gap breakdown**
3. Click **"Verify your skills to boost your match"** → take an assessment
4. After the assessment → view your updated **skill profile**
5. Go to **Learning Paths** → see AI-generated course recommendations
6. Go to **Resume Builder** → choose a template → download PDF
7. Log in as **Recruiter** → post a job with required skills → view ranked applicants

---

## 3. Feature Showcase

### For Students & Professionals

#### Job Matching (ML-powered)
- Every job card shows a **match percentage** computed in real-time
- Hybrid scoring: 40% Jaccard skill similarity + 60% skill coverage
- Filter by job type, location, salary range
- Bookmark jobs; track application status

#### Skill Gap Analysis
- Select any job → instantly see:
  - **Verified skills** you already have (green)
  - **Partial skills** where your proficiency is below the job's requirement (orange)
  - **Missing skills** you haven't verified at all (red)
- Single click to start an assessment for any missing skill

#### Skill Assessments (Anti-cheat)
- **20 questions** per assessment: 8 easy / 6 medium / 6 hard
- Questions generated by **Google Gemini** and cached permanently (quota protection)
- **Shuffle seed** per attempt — options reordered differently for every user/retake
- Correct answers stored as **text values** not indices — prevents index-guessing
- Pass threshold: **60%** (12/20 correct) → skill marked "verified" at proficiency 0–10
- Fallback: 50 pre-seeded template questions if Gemini API is unavailable

#### Learning Paths (Gemini AI)
- Input: your verified skill gaps
- Output: ordered list of courses with title, platform, duration, rationale
- Generated fresh per user; falls back to curated static paths if API is down

#### Resume Builder
- Three templates: **Modern**, **Professional**, **Creative**
- Auto-fills from your profile (skills, experience, projects, education)
- ATS-optimised PDF export via ReportLab
- AI Resume Tailor — customises your resume for a specific job description

#### Community Forum
- Create posts, comment, like
- Career advice threads, job referrals, peer support
- Slug auto-generation, post moderation

#### AI Career Coach (Google ADK)
- Chat interface powered by `gemini-2.0-flash`
- Uses your full profile as context for personalised advice
- Circuit breaker prevents cascade failures if AI is unavailable

### For Recruiters

#### Job Posting
- Specify required skills with **proficiency levels 1–10** and **criticality weights**
- Rich job description editor
- Preview how your job appears to candidates

#### Applicant Tracking
- All applicants **ranked by ML match score**
- See each applicant's verified skill breakdown vs. your requirements
- One-click status updates: Applied → Shortlisted → Interviewed → Hired / Rejected
- Email notifications on status changes

#### AI Recruiter Agent
- Chat with an AI agent to help write better job descriptions
- Get suggestions for skill requirements based on role

---

## 4. Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser / Client                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────────┐
│              Nginx (reverse proxy + SSL termination)            │
│                    /static/ → S3 or WhiteNoise                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP (127.0.0.1:8000)
┌─────────────────────────▼───────────────────────────────────────┐
│             Gunicorn (1–3 workers, WSGI application server)     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Django 5.1 (MVT Monolith)                    │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐  │
│  │ accounts │  │   jobs   │  │ assessments │  │  learning  │  │
│  └──────────┘  └──────────┘  └─────────────┘  └────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐  │
│  │recruiter │  │community │  │  dashboard  │  │   agents   │  │
│  └──────────┘  └──────────┘  └─────────────┘  └────────────┘  │
│  ┌──────────────────────┐                                      │
│  │    resume_builder    │                                      │
│  └──────────────────────┘                                      │
└──────┬────────────────────────────────────────────────────┬────┘
       │                                                    │
┌──────▼──────┐                                   ┌─────────▼──────┐
│ PostgreSQL  │                                   │ Google Gemini  │
│(RDS / Render│                                   │ scikit-learn   │
│  managed)   │                                   │ Gmail SMTP     │
│  SQLite dev │                                   │ AWS S3         │
└─────────────┘                                   └────────────────┘
```

### App Responsibilities

| App | Responsibility | Key Models | Key Files |
|---|---|---|---|
| `accounts` | Custom User, OTP registration, login, profile | `User` (AbstractUser) | `models.py`, `views.py`, `utils.py` |
| `jobs` | Job listings, ML recommendations, applications | `Job`, `JobApplication`, `JobSkillRequirement` | `recommendation_engine.py`, `skill_based_matching_engine.py` |
| `assessments` | Skill intake, MCQ assessments, anti-cheat, scoring | `Skill`, `QuestionBank`, `AssessmentAttempt`, `UserSkillScore` | `views.py`, `ai_service.py` |
| `learning` | Skill gap analysis, AI learning paths, courses | `LearningPath`, `SkillGap`, `Course` | `learning_path_generator.py` |
| `recruiter` | Job posting, applicant tracking, recruiter dashboard | `JobPosting`, `JobSkillRequirement` | `views.py` |
| `community` | Forum posts, comments, likes | `Post`, `Comment`, `Like` | `views.py`, `signals.py` |
| `dashboard` | Central navigation, analytics, context aggregation | — | `context_processors.py`, `views.py` |
| `agents` | Google ADK multi-agent AI (career + recruiter) | — | `career_agent.py`, `recruiter_agent.py`, `circuit_breaker.py` |
| `resume_builder` | ATS resume generation, PDF export, AI tailoring | `Resume`, `ResumeTemplate`, `TailoredResume` | `pdf_generator.py`, `ai_service.py` |

### Key Data Flows

**Assessment Flow (most complex):**
```
Job Detail Page
    │
    ▼  "Verify Skills" button
Skill Gap Analysis  ──▶  identifies missing/partial skills
    │
    ▼  "Take Assessment"
start_assessment_from_job(job_id, skill_id)
    │  checks QuestionBank — fetches cached questions
    │  generates via Gemini ONLY if QuestionBank is empty
    │  selects 20 questions (8 easy / 6 medium / 6 hard)
    │  shuffles using shuffle_seed per-attempt (anti-cheat)
    ▼
AssessmentAttempt created (status='in_progress')
    │
    ▼  take_assessment — renders 20 questions
submit_assessment (POST)
    │  scores: correct_answer TEXT comparison (not index)
    │  calculates proficiency_level (0–10)
    ▼
UserSkillScore updated  (status: 'claimed' → 'verified')
    │
    ▼  assessment_results — shows score, recommends learning path
```

**Recommendation Flow:**
```
User profile → get_skills_list() → [skill_a, skill_b, ...]
                                           │
Job.skills  (JSON dict with proficiency)   │
                                           ▼
ContentBasedRecommender.score(user, job)
    ├── jaccard_similarity(user_skills, job_skills)   40% weight
    └── coverage_score(user_verified, job_required)   60% weight
                                           │
                                           ▼
Ranked job list (0.0 – 1.0 → displayed as 0% – 100%)
```

### Architecture Decisions & Trade-offs

| Decision | Chosen | Alternatives | Rationale |
|---|---|---|---|
| Framework | Django monolith | FastAPI + React, Flask | Shared ORM, built-in admin/auth/migrations — 10× faster to build |
| Database | PostgreSQL | MySQL, MongoDB | JSONB for skills/certifications; ACID compliance |
| AI provider | Google Gemini Flash | OpenAI GPT-4, Claude | Free tier adequate for MCQ generation; low latency |
| ML library | scikit-learn | PyTorch, TensorFlow | Jaccard/cosine on small vectors — no deep learning needed |
| Static files | WhiteNoise (dev) / S3 (prod) | CDN, Nginx direct | WhiteNoise: zero ops; S3: scalable, no disk pressure on EC2 |
| Process server | Gunicorn + Nginx | uWSGI, Uvicorn | Mature, stable; single worker handles t2.micro load |

---

## 5. Quick Setup — Local Dev

### Prerequisites
- Python 3.10 or later (tested on 3.12.8)
- Git
- Gmail account with [App Password](https://myaccount.google.com/apppasswords) enabled (requires 2FA)
- Google AI Studio API key — [get one free here](https://aistudio.google.com/app/apikey)

### Step-by-step

```bash
# 1. Clone
git clone https://github.com/akramnameemuddin/job-elevate.git
cd job-elevate

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

**Create `backend/backend/.env`:**

```env
# Core Django
SECRET_KEY=your-random-50-char-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for local dev)
DATABASE_URL=sqlite:///db.sqlite3

# Google Gemini AI
GOOGLE_API_KEY=your-gemini-api-key

# Email (OTP verification)
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# S3 (leave False for local dev)
USE_S3=False
```

```bash
# 4. Run migrations
cd backend
python manage.py migrate

# 5. Seed the database (run all of these once)
python manage.py add_questions              # populate QuestionBank (REQUIRED)
python manage.py populate_assessment_data   # create skill categories
python manage.py create_resume_templates    # create 3 resume templates

# Optional seed data
python create_sample_jobs.py
python manage.py seed_community

# 6. Create superuser for /admin/
python manage.py createsuperuser

# 7. Start dev server
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Verify Your Setup

```bash
# All 107 tests should pass
python manage.py test

# Check for config issues
python manage.py check

# Confirm QuestionBank is populated
python manage.py shell -c "from assessments.models import QuestionBank; print(QuestionBank.objects.count(), 'questions')"
```

### Generate a SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(50))"
```

---

## 6. Environment Variables

### Complete Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | YES | — | Django secret key — 50+ random hex chars, unique per deployment |
| `DEBUG` | YES | `False` | `True` for development only. `False` activates all production security settings |
| `ALLOWED_HOSTS` | YES | — | `localhost,127.0.0.1` (dev) · `yourdomain.com,EC2-IP` (prod) |
| `DATABASE_URL` | YES | — | `sqlite:///db.sqlite3` (dev) · `postgres://user:pass@host:5432/db` (prod) |
| `GOOGLE_API_KEY` | YES | — | Gemini API key from [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `EMAIL_HOST_USER` | YES | — | Gmail address for OTP emails |
| `EMAIL_HOST_PASSWORD` | YES | — | Gmail App Password (not account password) |
| `USE_S3` | NO | `False` | `True` to serve static/media from AWS S3 |
| `AWS_ACCESS_KEY_ID` | If USE_S3 | — | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | If USE_S3 | — | IAM user secret key |
| `AWS_STORAGE_BUCKET_NAME` | If USE_S3 | — | S3 bucket name |
| `AWS_S3_REGION_NAME` | If USE_S3 | `us-east-1` | AWS region of your S3 bucket |

### Environment Templates

**Local Development:**
```env
SECRET_KEY=dev-only-key-change-before-deploy
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
GOOGLE_API_KEY=your-gemini-api-key
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
USE_S3=False
```

**AWS EC2 Production:**
```env
SECRET_KEY=your-50-char-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR-EC2-IP
DATABASE_URL=postgres://jobelevate:StrongPass@your-rds-host.rds.amazonaws.com:5432/jobelevate
GOOGLE_API_KEY=your-gemini-api-key
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
USE_S3=True
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=jobelevate-static
AWS_S3_REGION_NAME=us-east-1
```

**Render.com Production:**
```env
SECRET_KEY=your-50-char-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=postgres://...  (injected automatically by Render)
GOOGLE_API_KEY=your-gemini-api-key
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
USE_S3=False
```

---

## 7. Deployment

### Option A — Render.com (Easiest, Free Tier)

1. Fork this repository to your GitHub account
2. Go to [render.com](https://render.com) → **New Web Service** → connect your fork
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `cd backend && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn backend.wsgi:application`
4. Add all environment variables from the Render template above
5. Add a **PostgreSQL** add-on — Render injects `DATABASE_URL` automatically
6. After first deploy, run seed commands via Render Shell:
   ```bash
   cd backend
   python manage.py add_questions
   python manage.py populate_assessment_data
   python manage.py create_resume_templates
   python manage.py createsuperuser
   ```

---

### Option B — AWS EC2 (Production, Recommended)

#### Prerequisites
- EC2: Ubuntu 24.04, t2.micro or larger, Elastic IP assigned
- Security Group: ports 22 (SSH), 80 (HTTP), 443 (HTTPS) open inbound
- RDS PostgreSQL in same VPC as EC2
- S3 bucket with public read bucket policy (ACLs disabled)
- Domain with A record pointing to your EC2 Elastic IP

#### 1. Server Setup

```bash
# Connect
ssh -i your-key.pem ubuntu@YOUR-EC2-IP

# System packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip nginx certbot python3-certbot-nginx

# Add swap — critical for t2.micro (prevents OOM kills during startup)
sudo fallocate -l 1.2G /swapfile
sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Clone project
git clone https://github.com/akramnameemuddin/job-elevate.git
cd job-elevate

# Create venv at project root (NOT inside backend/)
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
nano ~/job-elevate/backend/backend/.env
# Paste the AWS EC2 Production template from Section 6 and fill in your values
```

#### 3. Database & Static Files

```bash
cd ~/job-elevate/backend
python manage.py migrate
python manage.py add_questions
python manage.py populate_assessment_data
python manage.py create_resume_templates
python manage.py createsuperuser
python manage.py collectstatic --noinput    # uploads 163 files to S3
```

#### 4. Gunicorn as Systemd Service

```bash
sudo cp ~/job-elevate/deploy/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn   # verify "active (running)"
```

> **t2.micro tip:** Use `--workers 1` in the service file. Each worker uses ~180MB RAM; 3 workers can trigger OOM on a 1GB instance. The 1.2GB swap provides a buffer.

#### 5. Nginx Configuration

```bash
sudo cp ~/job-elevate/deploy/nginx-jobelevate.conf /etc/nginx/sites-available/jobelevate
sudo ln -s /etc/nginx/sites-available/jobelevate /etc/nginx/sites-enabled/
sudo nginx -t          # test — must say "syntax is ok"
sudo systemctl reload nginx
```

#### 6. SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo systemctl reload nginx
```

#### S3 Bucket Policy (Public Read)

In AWS Console → S3 → your bucket → **Permissions** → **Bucket policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
  }]
}
```

> Ensure **Block Public Access** is Off and **Object Ownership** is "Bucket owner enforced" (ACLs disabled). `storages.py` uses `default_acl = None` for compatibility.

#### Updating the Application

```bash
cd ~/job-elevate
git fetch origin && git reset --hard origin/master
source venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

#### Operations Reference

```bash
# Service health
sudo systemctl status gunicorn
sudo journalctl -u gunicorn --no-pager -n 50
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

# Application logs
tail -f ~/job-elevate/logs/django.log

# Resources
free -h          # memory — keep < 900MB on t2.micro
df -h            # disk — keep < 85% to avoid write failures
```

---

## 8. AI & ML Deep Dive

### 1. ML Recommendation Engine (`jobs/recommendation_engine.py`)

**Algorithm:** Hybrid content-based filtering — no user-to-user collaborative component (insufficient user data at launch)

```
score(user, job) = 0.40 × jaccard_similarity + 0.60 × coverage_score

jaccard_similarity  = |user_skills ∩ job_skills| / |user_skills ∪ job_skills|
coverage_score      = count(user_verified_skills matching job) / count(job_required_skills)
```

- Handles two skill formats transparently: legacy CSV strings and JSON dicts with proficiency levels
- Returns float 0.0–1.0 per (user, job) pair; displayed as 0%–100% match

**Skill-based Matching (`jobs/skill_based_matching_engine.py`):**
- Proficiency-aware: your verified level (0–10) vs. job's required level (0–10)
- Partial match: 6/10 on a skill requiring 8/10 → "Needs Improvement" (not "Missing")
- Gap severity: `gap = required_proficiency − user_proficiency`

### 2. AI Question Generation (`assessments/ai_service.py`)

**Model:** `gemini-2.5-flash-lite`

**Prompt:**
```
Generate 20 multiple-choice questions for the skill "{skill_name}".
Distribution: 8 easy (conceptual), 6 medium (applied), 6 hard (expert).
Format: JSON array. Fields: question_text, options (A/B/C/D), correct_answer (full text, not index), difficulty.
```

**Quota protection pipeline:**
1. Check `Skill.questions_generated` flag before any API call
2. If `QuestionBank` has questions → use them, **never regenerate**
3. `ResourceExhausted` exception → fallback to 50 pre-seeded template questions
4. Any other API error → log warning, serve template questions silently

**Anti-cheat system:**
- `correct_answer` stored as full text (e.g. `"List"`) not index position
- `shuffle_seed` = `user.id × skill.id × unix_timestamp` → different shuffle every attempt
- `selected_question_ids` JSON field tracks shown questions — prevents resubmission manipulation

### 3. AI Learning Path Generator (`learning/learning_path_generator.py`)

**Input:** `[(skill_name, gap_score), ...]` — verified skill gaps sorted by severity

**Prompt schema:**
```json
{
  "user": {"experience_level": "...", "current_skills": [...]},
  "gaps": ["skill_a", "skill_b"],
  "output_format": [{"title": "", "platform": "", "duration": "", "url": "", "rationale": ""}]
}
```

**Fallback:** Returns static curated path from pre-built course catalog if API unavailable

### 4. Google ADK Multi-Agent System (`agents/`)

```
User chat input
      │
      ▼
Orchestrator (orchestrator.py)
      ├── CareerAgent (career_agent.py)
      │     context: user profile + job data + skill scores
      │     answers: "How do I improve my Python score?"
      │
      └── RecruiterAgent (recruiter_agent.py)
            context: job market data + applicant pool
            answers: "What skills should I add to this posting?"

Both agents: gemini-2.0-flash via google-adk>=1.0.0
Circuit breaker: opens after 3 consecutive failures → returns graceful error
```

---

## 9. API Reference

All endpoints use Django session authentication. POST/PUT/DELETE require `X-CSRFToken` header or `csrfmiddlewaretoken` form field.

### Authentication

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/accounts/signup/` | Registration page | No |
| `POST` | `/accounts/signup/step1/` | Submit registration → send OTP | No |
| `POST` | `/accounts/signup/step2/` | Verify OTP → create account | No |
| `GET/POST` | `/accounts/login/` | Login | No |
| `POST` | `/accounts/logout/` | Logout | Yes |
| `GET/POST` | `/accounts/profile/` | View / update profile | Yes |

### Jobs

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/jobs/` | Job listing with ML match scores | Yes |
| `GET` | `/jobs/<id>/` | Job detail + skill gap analysis | Yes |
| `POST` | `/jobs/<id>/apply/` | Submit application | Yes |
| `GET` | `/jobs/recommendations/` | ML-ranked personalised list | Yes |
| `POST` | `/jobs/<id>/claim-skill/<skill_id>/` | Claim skill + redirect to assessment | Yes |
| `POST` | `/jobs/<id>/bookmark/` | Toggle bookmark | Yes |
| `GET` | `/jobs/bookmarked/` | View bookmarked jobs | Yes |
| `GET` | `/jobs/my-applications/` | Application history | Yes |

### Assessments

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/assessments/` | Skill intake dashboard | Yes |
| `GET` | `/assessments/browse/` | Browse all skills | Yes |
| `POST` | `/assessments/claim-skill/` | Claim skill `{skill_id, self_rating}` | Yes |
| `GET` | `/assessments/profile/` | User skill profile | Yes |
| `GET` | `/assessments/job/<job_id>/gaps/` | Skill gap for a specific job | Yes |
| `GET` | `/assessments/start-from-job/<job_id>/<skill_id>/` | Start from job context | Yes |
| `GET` | `/assessments/start/<skill_id>/` | Start directly | Yes |
| `GET` | `/assessments/take/<attempt_id>/` | View questions | Yes |
| `POST` | `/assessments/submit/<attempt_id>/` | Submit answers | Yes |
| `GET` | `/assessments/result/<attempt_id>/` | View results | Yes |

### Learning

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/learning/` | Learning dashboard | Yes |
| `GET` | `/learning/paths/` | View personalised learning paths | Yes |
| `GET` | `/learning/skill-gaps/` | Detailed skill gap analysis | Yes |
| `GET` | `/learning/courses/` | Course catalog | Yes |
| `POST` | `/learning/generate-path/` | Generate AI path for a skill | Yes |

### Recruiter

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/recruiter/dashboard/` | Recruiter overview | Recruiter |
| `GET/POST` | `/recruiter/jobs/create/` | Post a new job | Recruiter |
| `GET/POST` | `/recruiter/jobs/<id>/edit/` | Edit job posting | Recruiter |
| `GET` | `/recruiter/jobs/<id>/applicants/` | ML-ranked applicants | Recruiter |
| `POST` | `/recruiter/applications/<id>/status/` | Update application status | Recruiter |

### Resume Builder

| Method | URL | Description | Auth |
|---|---|---|---|
| `GET` | `/resume/` | Resume dashboard | Yes |
| `GET/POST` | `/resume/create/` | Create resume | Yes |
| `GET/POST` | `/resume/<id>/edit/` | Edit resume | Yes |
| `GET` | `/resume/<id>/download/` | Download PDF | Yes |
| `POST` | `/resume/<id>/ai-tailor/` | AI-tailor for a job | Yes |

### Standard Error Response

```json
{
  "error": "brief_error_code",
  "detail": "Human-readable message shown to user",
  "field_errors": { "email": ["Enter a valid email address."] }
}
```

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Created |
| `302` | Redirect (POST-redirect-GET) |
| `400` | Validation error |
| `401` | Login required |
| `403` | Wrong role or not your resource |
| `404` | Not found (via `get_object_or_404`) |
| `500` | Server error (logged, not exposed to user) |

---

## 10. Testing

### Run All Tests

```bash
cd backend
python manage.py test                  # all apps — 107 tests
python manage.py test --verbosity=2    # verbose: shows each test name
python manage.py test accounts         # single app
python manage.py test assessments jobs recruiter community dashboard learning
```

Expected: `Ran 107 tests in ~8s ... OK`

### Standalone Integration Tests

```bash
python test_workflow.py                  # end-to-end: register → assess → verify score
python test_assessment_20q.py            # validates 8E/6M/6H question distribution
python test_recommendation_accuracy.py   # ML precision/recall on synthetic dataset
python test_skill_matching_only.py       # proficiency gap calculation engine
```

### Coverage by App

| App | Tests | Focus |
|---|---|---|
| `accounts` | 18 | OTP signup, login/logout, profile, role redirect |
| `assessments` | 32 | Models, skill intake, browse, start-from-job, attempt lifecycle |
| `recruiter` | 16 | Dashboard access, job CRUD, application status |
| `community` | 14 | Access control, post CRUD, toggle likes, slug generation |
| `dashboard` | 12 | Home (3 roles), profile GET/POST, context keys |
| `learning` | 8 | Dashboard, skill gaps, course catalog, models |
| `resume_builder` | 7 | Template load, resume create, PDF download |
| **Total** | **107** | |

### Test Types

| Type | Examples |
|---|---|
| Unit | `calculate_percentage()`, `is_passing()`, `get_skills_list()` |
| Integration | Full HTTP → view → DB → template → response |
| Negative | Wrong password, unverified email, unauthenticated → correct error |
| Boundary | Empty forms, duplicate email, proficiency outside 0–10 |
| Role-based | Recruiter views → 302/403 for student users |
| Anti-cheat | Shuffle seed produces different option order per attempt |

---

## 11. Security

### Authentication & Sessions

- **OTP** — 6-digit code, 10-minute expiry, single use
- **Passwords** — PBKDF2-SHA256, 720,000 iterations (exceeds OWASP 600,000 minimum)
- **Session cookies** — `HttpOnly=True`, `SameSite=Lax`
- **CSRF** — `CsrfViewMiddleware` active; all forms include `{% csrf_token %}`

### Access Control & IDOR Prevention

Every object lookup is **owner-scoped**:
```python
attempt = get_object_or_404(AssessmentAttempt, pk=attempt_id, user=request.user)
job_posting = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)
```

Role enforcement:
```python
if request.user.user_type != 'recruiter':
    return redirect('dashboard:home')
```

### Security Headers

Always active (regardless of `DEBUG`):
```python
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

Production-only (`DEBUG=False`):
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000        # 1-year HSTS
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### SQL Injection

Django ORM exclusively — no raw SQL anywhere in all 10 apps.

### Secrets

- `.env` in `.gitignore` — never committed
- Gemini API key restricted to Generative Language API in Google Cloud Console
- Generate `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(50))"`

### OWASP Top 10

| Risk | Status | Implementation |
|---|---|---|
| A01 Broken Access Control | ✅ | `@login_required`, role checks, IDOR-safe lookups |
| A02 Cryptographic Failures | ✅ | PBKDF2-SHA256, HTTPS + HSTS in production |
| A03 Injection | ✅ | Django ORM only, no raw SQL |
| A04 Insecure Design | ✅ | OTP expiry, POST-redirect-GET, anti-cheat shuffling |
| A05 Security Misconfiguration | ✅ | `DEBUG=False` in prod, all security headers active |
| A06 Vulnerable Components | 🔍 | `pip-audit` run before each release |
| A07 Authentication Failures | ✅ | OTP required; Django-Axes rate limiting (v2) |
| A08 Software & Data Integrity | ✅ | CSRF tokens, POST-redirect-GET pattern |
| A09 Logging & Monitoring | ✅ | Django file logging in production |
| A10 SSRF | ✅ | External calls only to Gemini API (allow-listed domain) |

---

## 12. Performance

### Bottlenecks & Mitigations

| Bottleneck | Root Cause | Fix Applied |
|---|---|---|
| N+1 on job listing | Each card queried skills separately | `prefetch_related('required_skills')` in `jobs/views.py` |
| Recommendation engine | Full matrix recomputed every page load | Cached per-user, invalidated on profile change |
| AI question generation | Gemini call ~2s per skill | `Skill.questions_generated` flag — **generated once, reused forever** |
| Static asset delivery | Uncompressed CSS/JS | WhiteNoise gzip; S3 served via HTTPS edge |
| Dashboard aggregation | Multiple cross-app queries | `select_related()` + context processor deduplication |
| OOM on t2.micro | 3 workers × ~180MB = 540MB+ | Reduced to 1 worker + 1.2GB swap |

### Query Patterns

```python
# Prevents N+1 on job listing
jobs = Job.objects.filter(status='Open') \
    .select_related('posted_by') \
    .prefetch_related('required_skills__skill') \
    .order_by('-created_at')

# Single query for all user skill scores
user_skill_profiles = {
    p.skill_id: p
    for p in UserSkillScore.objects
        .filter(user=request.user, status='verified')
        .select_related('skill')
}
```

### Frontend
- Tailwind CSS purged in production (< 20KB bundle)
- All `<img>` use `loading="lazy"`
- No render-blocking JS in `<head>`
- Gemini calls have 10-second timeout

---

## 13. Evaluation Criteria Compliance

### Criterion 1 — Problem Definition (10 marks)

| Sub-criterion | Evidence |
|---|---|
| Precise problem statement | "Fresh graduates cannot identify, verify, or close skill gaps for specific job listings in one integrated platform." |
| Target users | Students (0–2 YOE), professionals (0–5 YOE), SME tech recruiters |
| Current workaround | Random applications on Naukri/LinkedIn, zero feedback loop |
| Scope boundary | In: assessment, matching, learning. Out: video interviews, LMS integration |
| Real-world evidence | LinkedIn India 2023 (67%); VVIT survey n=20 (18/20 apply randomly) |
| Concrete scenario | 3rd-year student applying for Python backend role — silent rejection without JobElevate, instant gap diagnosis with it |
| Competitive analysis | Section 1 comparison table — only JobElevate covers all 4 capabilities |
| Differentiator | Only platform tying job → gap → AI assessment → personalised path in one workflow |
| Measurable success | Gap < 2 min; assessment < 15 min; 80% first-time task completion |

### Criterion 2 — Architecture (15 marks)

See Section 4 for full diagrams, data flows, and decision table.

Key evidence: 10 apps with single responsibility each; business logic in pure Python service files (`recommendation_engine.py`, `learning_path_generator.py`, `ai_service.py`) — zero HTML; SQLite → PostgreSQL swap required only `DATABASE_URL` change.

### Criterion 3 — Code Quality (15 marks)

- PEP 8 throughout all 10 apps; self-documenting function names
- DRY utilities table in Section 13 above
- Graceful AI fallback with logging (Section 8)
- Technical debt explicitly documented (CSV field, long submit view)

### Criterion 4 — Functionality (15 marks)

All 8 core flows live and tested on both deployments. Edge cases: duplicate email, double submission, Gemini down, unauthenticated access, skills not in `JobSkillRequirement` — all handled. See Section 3 for full feature list.

### Criterion 5 — Testing (10 marks)

107 tests, 0 failures. Types: unit, integration, negative, boundary, role-based, anti-cheat. See Section 10.

### Criterion 6 — Security (10 marks)

OWASP Top 10 mapping in Section 11. IDOR prevention, HSTS, CSRF, PBKDF2-SHA256, Django ORM-only.

### Criterion 7 — UI/UX (5 marks)

Consistent base template; messages framework on every action; role-based UI; "Question X of 20" progress; responsive CSS breakpoints; dark mode toggle; empty states.

### Criterion 8 — Performance (5 marks)

`select_related`/`prefetch_related` throughout; Gemini results permanently cached; WhiteNoise gzip; bottlenecks identified with concrete fixes (Section 12).

### Criterion 9 — Documentation (5 marks)

This README + inline docstrings throughout + `backend/ASSESSMENT_STATUS.md`, `ASSESSMENT_WORKFLOW.md`, `WORKFLOW_FIXED.md`, `MODELS_AUDIT.md`, `deploy/` configuration files.

### Criterion 10 — Presentation & Defence (10 marks)

**2-minute pitch:**

*"JobElevate is a Django monolith across 10 apps. A student registers — OTP verified by Gmail SMTP. They browse jobs and see an ML match score from our hybrid Jaccard + coverage engine. Clicking their skill gap reveals exactly which skills are missing or below threshold. One click creates an `AssessmentAttempt`: 20 questions from `QuestionBank` (8/6/6 easy/medium/hard), shuffled per user with a per-attempt seed so no two users see the same option order. Submit scores it — correct answer matched by text, not index. `UserSkillScore` updates from 'claimed' to 'verified'. Gemini receives the verified gaps and returns an ordered learning path. Recruiter side: post job with skill requirements, applicants auto-ranked by the same ML engine."*

**Prepared answers:**

| Question | Answer |
|---|---|
| "How do you prevent cheating?" | Shuffle seed per attempt; correct answer as text not index; `selected_question_ids` prevents resubmission |
| "What if Gemini is down?" | Circuit breaker + fallback to 50 pre-seeded template questions — assessment always works |
| "Why not microservices?" | Shared ORM avoids serialisation overhead; single deployment for college project. Recommendation engine is the natural v2 candidate |
| "Can this scale?" | Not as-is beyond ~5,000 jobs in-process. Fix: Celery async task. AI scaling already solved by caching |
| "Why Gemini over GPT-4?" | Free tier adequate for MCQ; lower latency; no cost at student project scale |

---

## 14. Roadmap

### Version 2.0

- [ ] Migrate `technical_skills` CSV → `ManyToManyField`
- [ ] Celery + Redis: async OTP email and recommendation refresh
- [ ] Django-Axes: brute-force login rate limiting
- [ ] Server-enforced 30-minute assessment timer
- [ ] Coursera / YouTube API for real course links
- [ ] Django Channels: real-time recruiter notifications
- [ ] Resume PDF parsing: upload PDF → auto-fill profile
- [ ] Mobile PWA

### Known Limitations (v1)

| Area | Limitation | Workaround |
|---|---|---|
| `technical_skills` | CSV string — not normalised | `get_skills_list()` bridges legacy and new formats |
| OTP email | Synchronous | Acceptable at current scale |
| Recommendation | In-process | Cached on profile change |
| Assessment timer | No server-side limit | Anti-cheat via shuffling + question tracking |
| Login throttling | None | Django-Axes in v2 |

---

## 15. Team & Acknowledgements

**Project:** JobElevate — AI-Powered Job Matching & Upskilling Platform
**Institution:** Vasireddy Venkatadri Institute of Technology (VVIT), Guntur, Andhra Pradesh
**Department:** Computer Science & Engineering — Artificial Intelligence & Machine Learning
**Academic Year:** 2024–25

### Stack

| Technology | Purpose |
|---|---|
| [Django 5.1](https://www.djangoproject.com/) | Web framework — ORM, admin, auth, migrations |
| [PostgreSQL 16](https://www.postgresql.org/) | Production database — JSONB, ACID |
| [Google Gemini Flash](https://ai.google.dev/) | MCQ generation, learning paths, AI agents |
| [scikit-learn](https://scikit-learn.org/) | ML recommendation engine |
| [ReportLab](https://www.reportlab.com/) | PDF resume generation |
| [django-storages + boto3](https://django-storages.readthedocs.io/) | AWS S3 static/media storage |
| [WhiteNoise](https://whitenoise.readthedocs.io/) | Static files in dev and Render |
| [Gunicorn](https://gunicorn.org/) | WSGI application server |
| [Nginx](https://nginx.org/) | Reverse proxy + SSL termination |
| [Google ADK](https://google.github.io/adk-docs/) | Multi-agent AI framework |
| [Render.com](https://render.com/) | Free-tier cloud deployment |
| [AWS EC2 + RDS + S3](https://aws.amazon.com/) | Production cloud infrastructure |

### Acknowledgements

- [Django documentation](https://docs.djangoproject.com/) — comprehensive and exemplary
- [Google AI Studio](https://aistudio.google.com/) — free Gemini API access
- [Boxicons](https://boxicons.com/) — icon library
- LinkedIn India Skills Report 2023 — problem validation data

---

<div align="center">

**JobElevate** — From skill gap to job offer, in one platform.

*Built at VVIT, Guntur · CSE-AIML · 2024–25*

</div>
