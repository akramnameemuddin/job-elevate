# JobElevate — Complete Project Overview

## What Is This Project?

JobElevate is an AI-powered job matching and upskilling platform built with Django. It connects three types of users: **students** looking for jobs, **professionals** upgrading their careers, and **recruiters** hiring talent. The platform uses machine learning to recommend jobs, Google Gemini AI to generate quiz questions and learning paths, and Google ADK (Agent Development Kit) to run a multi-agent system where two AI agents work together — one helping job seekers and one helping recruiters.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 5.1.6 (Python 3.12) |
| Database | SQLite (dev) / PostgreSQL (production via `DATABASE_URL`) |
| AI / LLM | Google Gemini API (`gemini-2.0-flash` for agents, `gemini-2.5-flash-lite` for question generation) |
| Multi-Agent Framework | Google ADK (`google-adk` package) |
| ML / Recommendation | scikit-learn, numpy, pandas (TF-IDF + cosine similarity) |
| Frontend | Django templates + Tailwind CSS + vanilla JavaScript |
| PDF Generation | ReportLab + WeasyPrint |
| Production Server | Gunicorn + WhiteNoise (static files) |
| Email | Gmail SMTP (OTP verification) |

---

## The 10 Django Apps — What Each One Does

```
backend/
├── accounts/       → User registration, login, profiles, OTP email verification
├── jobs/           → Job listings, ML-powered job recommendations, job search
├── assessments/    → Skill testing with AI-generated MCQ quizzes (20 questions each)
├── learning/       → AI-generated learning paths to close skill gaps
├── community/      → Forum, posts, peer discussions
├── dashboard/      → Central hub showing stats, recent activity, navigation
├── recruiter/      → Job posting, application management, candidate shortlisting
├── resume_builder/ → ATS-compliant resume creation with PDF export
├── agents/         → Google ADK multi-agent system (career coach + recruiter AI)
├── ml/             → ML model training, evaluation, demo data seeding
```

### How They Connect

```
User signs up (accounts)
    │
    ├── Student/Professional path:
    │   ├── Views jobs (jobs) → ML recommends matching ones
    │   ├── Takes skill assessments (assessments) → AI generates questions
    │   ├── Sees skill gaps (jobs/assessments) → Gets learning paths (learning)
    │   ├── Builds resume (resume_builder) → AI tailors it for jobs
    │   ├── Gets AI career coaching (agents) → Career agent analyses everything
    │   └── Joins community (community) → Discusses with peers
    │
    └── Recruiter path:
        ├── Posts jobs with skill requirements (recruiter)
        ├── Reviews applications (recruiter)
        ├── Uses AI to rank candidates (agents) → Recruiter agent scores applicants
        └── Messages candidates (recruiter)
```

---

## How the User System Works

The `accounts` app has a custom `User` model extending Django's `AbstractUser`. Every user has a `user_type` field that is either `student`, `professional`, or `recruiter`. This single field controls what pages they see and what features they access.

- **Technical skills** are stored as a comma-separated string (e.g., `"Python,Django,React"`). You access them via `user.get_skills_list()` which splits the string into a list.
- **Projects, internships, certifications** are stored as JSON fields.
- **Login** uses Django's built-in authentication with email OTP verification.

---

## How Job Recommendations Work (ML Engine)

File: `jobs/recommendation_engine.py`

When a student views their dashboard, the system recommends jobs using a **3-component weighted score**:

```
Final Score = 0.55 × Skill Score + 0.10 × Text Similarity + 0.35 × Preference Score
```

**Component 1 — Skill Score (55% weight):**
Takes the user's technical skills and the job's required skills. Computes Jaccard similarity (overlap) plus a coverage ratio. If a job needs Python, Django, React and the user knows Python and Django, that is a 2/3 = 67% coverage.

**Component 2 — Text Similarity (10% weight):**
Uses TF-IDF vectorization + cosine similarity to compare the user's profile text (objective, projects, certifications) against the job's description. This catches cases where exact skill names do not match but the content is relevant.

**Component 3 — Preference Score (35% weight):**
Checks five signals:
- Experience match (30%): Does the user's years of experience meet the job's requirement?
- Location match (25%): Same city or remote?
- Job type match (20%): Full-time, part-time, internship?
- Industry match (15%): Same sector?
- Salary match (10%): Within expected range?

The engine returns a sorted list of jobs with scores from 0.0 to 1.0.

---

## How Skill Assessments Work

File: `assessments/ai_service.py`, `assessments/views.py`

Each assessment has **20 multiple-choice questions**: 8 easy, 6 medium, 6 hard.

**Question generation** uses a hybrid approach:
1. First, check if template questions already exist in the `QuestionBank` database table for that skill.
2. If not, call Google Gemini (`gemini-2.5-flash-lite`) to generate 20 questions with correct answers and explanations.
3. Store them permanently in `QuestionBank`. Never regenerate — this saves API quota.
4. If the API is unavailable, fall back to generic template questions.

**Anti-cheating features:**
- Correct answers are stored as text values, not index positions (so shuffling options does not break grading).
- Each attempt gets a unique `shuffle_seed` that randomizes option order per user.
- Questions are randomly selected from the bank and tracked via `selected_question_ids`.

**Scoring:**
- 60% threshold to pass (12 out of 20 correct).
- Produces a proficiency level on a 0-to-10 scale.
- Two tracking models: `UserSkillScore` (official verified level) and `AssessmentAttempt` (individual attempt data).

---

## How Learning Paths Work

File: `learning/learning_path_generator.py`

When a user has skill gaps (their level is below what a job requires), the system generates a personalized learning path:

1. Calls Google Gemini with the user's current level, target level, and the skill name.
2. Gemini returns a structured JSON with recommended courses, estimated hours, and milestones.
3. The system creates `LearningPath`, `SkillGap`, `Course`, and `LearningPathCourse` records in the database.
4. Time estimates: 8 hours per proficiency point (basic), 12 hours (intermediate), 20 hours (advanced).

This uses the direct `google.genai` SDK, not ADK agents.

---

## How the Resume Builder Works

File: `resume_builder/views.py`

Users build ATS-compliant resumes through a form-based editor. Two AI features exist:

1. **AI Analyze** — Sends resume sections to Gemini, gets back suggestions for improvement.
2. **AI Tailor** — Given a specific job posting, rewrites resume bullet points to match the job's keywords and requirements.

PDF export uses ReportLab and WeasyPrint.

---

## How the Google ADK Multi-Agent System Works

This is the core AI architecture. It uses the official `google-adk` package (not a custom implementation).

### What Is Google ADK?

Google ADK (Agent Development Kit) is Google's framework for building AI agents. An agent is an LLM (like Gemini) that has access to tools (Python functions it can call). You define:
- An `Agent` with a name, model, instruction, and a list of tools.
- The LLM reads the user's question, decides which tools to call, calls them, reads the results, and then generates a response.

ADK also supports **multi-agent** architectures where a root agent delegates to sub-agents based on the query.

### The Agent Hierarchy

```
root_agent ("job_elevate_orchestrator")
│   Model: gemini-2.0-flash
│   Role: Understands user requests, delegates to the right specialist
│
├── career_guidance_agent (6 tools)
│   │   Role: Helps students/professionals with career advice
│   │
│   ├── fetch_user_profile()        → Reads User model from database
│   ├── fetch_user_skills()         → Reads UserSkillScore (verified skill levels)
│   ├── fetch_assessment_attempts() → Reads recent assessment results
│   ├── fetch_recommended_jobs()    → Calls the ML recommendation engine
│   ├── compute_skill_gap()         → Compares user skills vs job requirements
│   └── generate_learning_roadmap() → Triggers learning path generation
│
└── recruiter_matching_agent (3 tools)
    │   Role: Helps recruiters evaluate and rank candidates
    │
    ├── fetch_job_details()          → Reads Job model + skill requirements
    ├── fetch_applicants()           → Reads all Applications for a job
    └── compute_candidate_score()    → 5-component weighted scoring algorithm
```

### How Each File Works

**`agents/adk_runtime.py` — The Foundation**

This is a thin wrapper around the `google-adk` package. It does three things:

1. **Sets environment variables** — ADK needs `GOOGLE_API_KEY` and `GOOGLE_GENAI_USE_VERTEXAI=FALSE` as environment variables. This file reads `GOOGLE_API_KEY` from Django settings and sets them.

2. **Creates a Runner** — `create_runner(agent)` takes an Agent and creates an ADK `Runner` with an `InMemorySessionService`. The Runner is what actually executes agent conversations.

3. **Bridges sync/async** — Django views are synchronous, but ADK's Runner is async. The `call_agent()` function wraps the async loop in `asyncio.run()` with a thread-pool fallback so it works inside Django.

```python
# How you use it:
from agents.adk_runtime import create_runner, call_agent

runner = create_runner(root_agent)
reply = call_agent(runner, user_id="user_1", session_id="session_1",
                   query="Recommend jobs for me")
# reply is a plain string with the agent's response
```

**`agents/career_agent.py` — Student/Professional Side**

Defines 6 tool functions as plain Python functions. ADK automatically wraps them into `FunctionTool` objects by reading the function signature and docstring. When the LLM decides to call a tool, ADK executes the Python function and feeds the result back to the LLM.

Each tool:
- Takes simple arguments (integers, strings) — ADK cannot pass complex objects.
- Returns a dictionary with a `status` key ("success" or "error").
- Reads from the Django database (User, UserSkillScore, AssessmentAttempt, Job models).

The file also exports `get_career_recommendations()` — a programmatic function that calls all 6 tools directly in sequence without involving the LLM. This is used by the Orchestrator for deterministic demo flows where you want guaranteed, fast results without LLM unpredictability.

**`agents/recruiter_agent.py` — Recruiter Side**

Defines 3 tool functions and a **5-component weighted scoring algorithm** for ranking candidates:

```
Composite Score = 0.30 × Skill Match
               + 0.15 × Verified Ratio
               + 0.20 × Avg Assessment Score
               + 0.10 × First Try Pass Rate
               + 0.25 × Proficiency Fit
```

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Skill Match | 30% | Jaccard overlap: how many required skills does the candidate have? |
| Verified Ratio | 15% | Of matched skills, how many are assessment-verified (not just claimed)? |
| Avg Assessment Score | 20% | Average percentage score on relevant skill assessments |
| First Try Pass Rate | 10% | Did they pass assessments on the first attempt? |
| Proficiency Fit | 25% | Weighted average of (user level / required level), using skill criticality as weights |

The `rank_candidates_for_job()` function calls all 3 tools for every applicant, computes scores, and returns a sorted list.

**`agents/orchestrator.py` — The Brain**

This file has two parts:

**Part 1: ADK Root Agent** — `root_agent` is an ADK `Agent` with `sub_agents=[career_agent, recruiter_agent]`. When you send a free-text query through the ADK Runner, the orchestrator LLM reads the query, decides which sub-agent should handle it, and delegates. Example:
- "Recommend jobs for me" → delegates to `career_guidance_agent`
- "Rank candidates for my Python Developer job" → delegates to `recruiter_matching_agent`

**Part 2: Orchestrator Class** — A Python class with 3 deterministic flows that call tool functions directly (no LLM):

| Method | What It Does |
|--------|-------------|
| `run_career_flow(user, target_job_id)` | Calls career agent tools → returns profile, recommended jobs, skill gaps, learning roadmap, next steps |
| `run_recruiter_flow(user, job_id)` | Calls recruiter agent tools → returns ranked candidates with scores |
| `run_full_multi_agent_flow(user, job_id)` | Runs career flow THEN recruiter flow → returns combined result showing both perspectives |

Every flow:
1. Creates an `AgentRunLog` in the database (status: "running").
2. Logs every inter-agent message as an `AgentMessage` (sender, receiver, intent, payload).
3. On completion, updates the run log (status: "completed", stores result JSON).
4. On failure, marks status as "failed" with the error message.

This logging lets the UI show a real-time timeline of agent communication.

**`agents/views.py` — Web Interface**

Four Django views that connect the agents to web pages:

| URL | View | Page |
|-----|------|------|
| `/ai/career-coach/` | `career_guidance_view` | Students click "Analyse My Career", gets JSON back, JS renders results |
| `/ai/recruiter/` | `recruiter_agent_view` | Recruiters select a job, click "Rank Candidates", gets ranked list |
| `/ai/agents-demo/` | `multi_agent_demo_view` | Shows both agents working together with a communication timeline |
| `/ai/run/<id>/` | `agent_run_detail_view` | JSON API returning messages for a specific run (used by AJAX) |

Each view works the same way:
- **GET**: Renders the HTML template with job lists and recent run history.
- **POST**: Calls `Orchestrator.run_*_flow()`, transforms the result to match what the template JavaScript expects, returns JSON.
- The templates use AJAX (fetch API) to POST the form, receive JSON, and dynamically render results (job cards, score rings, skill badges, timeline dots) without a page reload.

**`agents/models.py` — Database Models**

Two models for logging:

```
AgentMessage
├── sender_agent    (string, e.g., "orchestrator")
├── receiver_agent  (string, e.g., "career_guidance_agent")
├── intent          (string, e.g., "career_analysis")
├── payload         (JSON, structured data)
└── created_at      (timestamp)

AgentRunLog
├── user            (FK to User)
├── run_type        (string: "career_flow", "recruiter_flow", "full_multi_agent")
├── status          (string: "running", "completed", "failed")
├── result          (JSON, full result data)
├── messages        (M2M to AgentMessage)
├── started_at      (timestamp)
└── completed_at    (timestamp)
```

### Two Ways to Use the Agents

**Way 1 — LLM-driven (via ADK Runner):**
You send a natural language query. The root agent's LLM reads it, picks the right sub-agent, the sub-agent's LLM calls tools, and you get a natural language response back. This is fully dynamic but uses Gemini API calls.

```python
from agents.orchestrator import root_agent
from agents.adk_runtime import create_runner, call_agent

runner = create_runner(root_agent)
reply = call_agent(runner, user_id="1", session_id="s1",
                   query="What jobs match my skills?")
print(reply)  # Natural language response from the LLM
```

**Way 2 — Deterministic (via Orchestrator class):**
You call Python functions directly. No LLM is involved. Tools execute, data is returned as structured dictionaries. This is what the web views use — it is faster, cheaper, and always returns the same structure.

```python
from agents.orchestrator import Orchestrator

orch = Orchestrator()
result = orch.run_career_flow(user, target_job_id=42)
print(result["recommended_jobs"])       # List of job dicts
print(result["skill_analysis"])         # Gap analysis dict
print(result["learning_roadmap"])       # Learning path list
```

---

## All Gemini API Calls in the Project

| Where | What Calls Gemini | Model Used | When It Happens | How Often |
|-------|-------------------|-----------|-----------------|-----------|
| `assessments/ai_service.py` | Generates 20 MCQ questions per skill | `gemini-2.5-flash-lite` | First time a skill is assessed | Once per skill (cached forever) |
| `learning/learning_path_generator.py` | Creates personalized study plan | `gemini-2.0-flash` | User requests a learning path | On-demand |
| `resume_builder/views.py` | Analyses or tailors resume | `gemini-2.0-flash` | User clicks AI buttons | On-demand |
| `agents/` (ADK agents) | Career/recruiter agent LLM reasoning | `gemini-2.0-flash` | Only if using LLM-driven path (Way 1) | On-demand |

The deterministic path (Way 2) that the web views use does **not** call Gemini at all. The tools are pure database reads and Python math.

---

## How to Run the Project

```bash
# 1. Clone and set up
git clone <repo-url>
cd job-elevate
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Create backend/backend/.env
SECRET_KEY=your-django-secret-key
GOOGLE_API_KEY=your-gemini-api-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DATABASE_URL=sqlite:///db.sqlite3
DEBUG=True

# 3. Run migrations and seed data
cd backend
python manage.py migrate
python manage.py seed_demo_data     # Creates demo users, jobs, skills, applications
python manage.py add_questions      # Loads template questions into QuestionBank

# 4. Start server
python manage.py runserver
# Open http://localhost:8000
```

---

## URL Map (All Pages)

| URL Pattern | App | What It Does |
|------------|-----|-------------|
| `/` | accounts | Landing page |
| `/login/`, `/register/` | accounts | Authentication |
| `/dashboard/` | dashboard | Main hub after login |
| `/jobs/` | jobs | Browse job listings |
| `/jobs/<id>/` | jobs | Job detail + apply |
| `/assessments/` | assessments | List available skill assessments |
| `/assessments/take/<id>/` | assessments | Take a 20-question quiz |
| `/learning/` | learning | View learning paths |
| `/community/` | community | Forum and discussions |
| `/recruiter/` | recruiter | Recruiter dashboard |
| `/recruiter/post-job/` | recruiter | Create a new job posting |
| `/resume_builder/` | resume_builder | Build and export resumes |
| `/ai/career-coach/` | agents | AI career analysis for students |
| `/ai/recruiter/` | agents | AI candidate ranking for recruiters |
| `/ai/agents-demo/` | agents | Multi-agent demo (both agents together) |
| `/admin/` | django.contrib.admin | Django admin panel |

---

## Key Design Decisions

1. **Skills as CSV strings** — The User model stores `technical_skills` as `"Python,Django,React"`. This is simple but means you must always use `get_skills_list()` to convert it to a Python list.

2. **Questions generated once** — The `Skill.questions_generated` flag prevents re-calling Gemini. This is intentional to avoid burning API quota.

3. **Two agent paths** — The LLM-driven path exists for flexible natural language interaction. The deterministic path exists for the web UI where you need reliable, structured JSON responses.

4. **Agent messages logged** — Every inter-agent communication is stored in the database. This makes the multi-agent demo transparent — users can see exactly which agent sent what to whom and when.

5. **Scoring weights are explicit** — Both the ML recommendation engine and the recruiter scoring algorithm have clearly defined, documented weights that sum to 1.0. This makes the system explainable and auditable.
