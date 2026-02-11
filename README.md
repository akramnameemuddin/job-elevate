# Job Elevate — AI-Powered Job Matching & Upskilling Platform

A full-stack Django web application that connects job seekers with career opportunities using **Machine Learning**, **AI-generated assessments**, and **personalized learning paths**. Built as an academic project demonstrating end-to-end ML integration in a production-style web app.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.x (Python 3.12) |
| Frontend | Django Templates + Tailwind CSS + BoxIcons |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ML/AI | scikit-learn, NumPy, Pandas, TF-IDF |
| AI API | Google Gemini (question generation, learning paths) |
| PDF Export | ReportLab + WeasyPrint |
| Auth | Django built-in + OTP email verification |

---

## Architecture — 10 Django Apps

```
backend/
├── accounts/       Custom User model (student / professional / recruiter)
├── jobs/           Job listings, applications, recommendation engine
├── assessments/    Skill testing (20 MCQs per assessment, anti-cheating)
├── learning/       AI-powered learning path generator (Gemini API)
├── recruiter/      Recruiter dashboard, job posting, candidate matching
├── resume_builder/ ATS-compliant resume generation with PDF export
├── community/      Forum, discussions, peer support
├── dashboard/      User analytics and centralized navigation
├── agents/         Multi-agent AI system (career + recruiter agents)
├── ml/             ★ Machine Learning model for Job-Candidate Fit Prediction
└── backend/        Django settings, URL routing, context processors
```

---

## ML Model — Job-Candidate Fit Predictor

### What It Does
Predicts how well a **job seeker** matches a **job posting** using a trained **Random Forest Classifier** (ensemble of 200 decision trees).

- **Input:** A (User, Job) pair
- **Output:** Fit probability score (0.0 – 1.0)
- **Integration:** Used in recruiter's candidate ranking and job recommendation engine

### How It Works

```
User Profile + Job Posting
        │
        ▼
┌─────────────────────┐
│  Feature Engineering │   23 numerical features extracted
│  (feature_engineer-  │   from skills, experience, education,
│   ing.py)            │   profile richness, assessments, text
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   StandardScaler     │   Normalize features to zero mean,
│                      │   unit variance
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Random Forest       │   200 decision trees vote
│  Classifier          │   independently → majority wins
│  (trainer.py)        │
└────────┬────────────┘
         │
         ▼
    Fit Probability
      (0.0 – 1.0)
```

### 23 Features Extracted

| Category | Features | Count |
|----------|----------|-------|
| Skill Match | match ratio, matched count, required count, missing mandatory, avg/min proficiency, proficiency gap, max gap, overconfidence | 9 |
| Experience | experience delta, experience ratio, meets requirement | 3 |
| Education | education level (ordinal), CGPA (normalized) | 2 |
| Profile Richness | projects, certifications, internships, work experience, completeness | 5 |
| Assessment | pass rate, avg score, verified skill count | 3 |
| Text Similarity | TF-IDF cosine similarity (user profile vs job description) | 1 |

### Training Pipeline

```bash
# Step 1: Seed demo data (10 users, 8 jobs, 22 applications)
python manage.py seed_demo_data

# Step 2: Train the Random Forest model
python manage.py train_fit_model --synthetic 2000

# Step 3: Evaluate and generate presentable report
python manage.py evaluate_model
```

- **Validation:** 5-fold Stratified Cross-Validation
- **Train/Test Split:** 80%/20% with stratification
- **Class Balancing:** Handled via `class_weight='balanced'`
- **Saved Artifacts:** `ml/saved_models/` (model .joblib, scaler .joblib, report .json, evaluation .txt)

### ML Files

| File | Purpose |
|------|---------|
| `ml/feature_engineering.py` | Extracts 23 features from (User, Job) pairs |
| `ml/dataset.py` | Builds training data from real applications + synthetic generation |
| `ml/trainer.py` | Trains Random Forest, 5-fold CV, saves model |
| `ml/predictor.py` | Thread-safe singleton for serving predictions at runtime |
| `ml/management/commands/train_fit_model.py` | Django command to train the model |
| `ml/management/commands/evaluate_model.py` | Django command to generate evaluation report |
| `ml/management/commands/seed_demo_data.py` | Seed realistic demo data for training |
| `ml/saved_models/` | Trained model, scaler, and reports |

---

## Key Features

### AI-Powered Job Recommendations
- **Content-based filtering** using Jaccard skill similarity (40%) + coverage score (60%)
- **ML boost**: Random Forest fit score blended at 15% weight into recommendations
- Located in `jobs/recommendation_engine.py`

### Skill Assessment System (Anti-Cheating)
- 20 MCQ questions per assessment: 8 Easy + 6 Medium + 6 Hard
- Questions generated ONCE per skill via Google Gemini API, cached in `QuestionBank`
- **Anti-cheating measures:**
  - Correct answers stored as TEXT values, not option indices
  - Answer options shuffled per user via `shuffle_seed`
  - Unique question selection per attempt via `selected_question_ids`
- Passing threshold: 60% (12/20 correct)
- Proficiency scores on 0-10 scale

### Resume Builder
- ATS-compliant resume generation from user profile data
- PDF export via ReportLab/WeasyPrint
- Multiple template options

### AI Learning Paths
- Google Gemini generates personalized course recommendations
- Based on skill gaps identified through assessments
- Fallback to template recommendations if API unavailable

### Multi-Agent AI System
- **Career Agent**: Personalized career guidance for job seekers
- **Recruiter Agent**: AI assistant for recruiter workflows
- Circuit breaker pattern for API reliability

### Recruiter Dashboard
- Post jobs with skill requirements and proficiency levels (1-10 scale)
- View ranked candidates with ML-powered fit scores
- Application status management (Applied → Shortlisted → Interview → Offered → Hired / Rejected)

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- pip
- Virtual environment

### Quick Start
```bash
# Clone and setup
git clone <repository-url>
cd job-elevate
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Environment variables — create backend/backend/.env
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-gemini-api-key
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-app-password
DATABASE_URL=sqlite:///db.sqlite3

# Database setup
cd backend
python manage.py migrate

# Populate assessment questions (one-time)
python manage.py add_questions

# Seed demo data for ML training
python manage.py seed_demo_data

# Train ML model
python manage.py train_fit_model --synthetic 2000

# Generate evaluation report
python manage.py evaluate_model

# Run server
python manage.py runserver
```

Visit http://localhost:8000

---

## Project Structure

```
job-elevate/
├── backend/
│   ├── accounts/              User auth, custom User model, OTP verification
│   ├── agents/                Multi-agent AI (career + recruiter agents)
│   ├── assessments/           Skill testing, AI question generation
│   │   ├── ai_service.py      Google Gemini integration
│   │   ├── models.py          Skill, QuestionBank, AssessmentAttempt
│   │   └── management/        add_questions, populate_assessment_data
│   ├── community/             Forum, discussions
│   ├── dashboard/             Analytics, navigation hub
│   ├── jobs/                  Job listings, recommendations
│   │   ├── recommendation_engine.py   Content-based + ML hybrid recommender
│   │   └── skill_gap_helpers.py       Gap analysis utilities
│   ├── learning/              AI learning path generator
│   ├── ml/                    ★ Machine Learning module
│   │   ├── feature_engineering.py     23-feature extraction
│   │   ├── dataset.py                 Real + synthetic data builder
│   │   ├── trainer.py                 Random Forest training pipeline
│   │   ├── predictor.py              Runtime prediction service
│   │   ├── management/commands/       train_fit_model, evaluate_model, seed_demo_data
│   │   └── saved_models/             Trained model artifacts
│   ├── recruiter/             Recruiter dashboard, candidate management
│   ├── resume_builder/        ATS resume generation + PDF export
│   ├── static/                CSS, JS, images
│   ├── media/                 User uploads
│   └── backend/               Django settings, URLs
├── requirements.txt           Python dependencies
├── LICENSE                    MIT License
└── README.md
```

---

## Management Commands

| Command | Purpose |
|---------|---------|
| `python manage.py seed_demo_data` | Seed 10 users, 8 jobs, 22 applications for ML training |
| `python manage.py train_fit_model` | Train the Random Forest model |
| `python manage.py evaluate_model` | Generate formatted evaluation report |
| `python manage.py add_questions` | Populate question bank for assessments |
| `python manage.py populate_assessment_data` | Seed skills and categories |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
