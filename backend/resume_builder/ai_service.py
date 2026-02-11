"""
AI Resume Optimization Service
================================
Uses Google Gemini to analyze a user's resume against a specific job posting
and produce actionable, section-by-section suggestions for tailoring.

Integration: Called from views.py when a user starts the "Tailor for Job" flow.
"""
import json
import logging
import os
import uuid
from typing import Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini client (mirrors pattern from assessments/ai_service.py)
# ---------------------------------------------------------------------------
try:
    from google import genai
    from google.genai import types

    GEMINI_CLIENT = genai.Client(
        api_key=getattr(settings, 'GOOGLE_API_KEY', None) or os.getenv('GOOGLE_API_KEY')
    )
    GEMINI_MODEL = 'models/gemini-2.5-flash-lite'
    GEMINI_AVAILABLE = True
    logger.info(f"✓ Resume AI service enabled ({GEMINI_MODEL})")
except Exception as e:
    GEMINI_AVAILABLE = False
    GEMINI_CLIENT = None
    GEMINI_MODEL = None
    logger.warning(f"✗ Resume AI unavailable – will use rule-based fallback: {e}")


# ---------------------------------------------------------------------------
# Helper: build a text snapshot of the user's resume
# ---------------------------------------------------------------------------

def _build_resume_text(user, resume=None) -> str:
    """Flatten user profile + resume data into a plain-text resume."""
    sections = []

    # Header
    sections.append(f"Name: {user.full_name or user.username}")
    if user.email:
        sections.append(f"Email: {user.email}")
    if user.phone_number:
        sections.append(f"Phone: {user.phone_number}")
    if user.job_title:
        sections.append(f"Current Title: {user.job_title}")
    if user.preferred_location:
        sections.append(f"Location: {user.preferred_location}")

    # Objective / Summary
    if user.objective:
        sections.append(f"\n--- Professional Summary ---\n{user.objective}")

    # Education
    if user.university:
        edu = f"\n--- Education ---\n{user.degree or 'Degree'} – {user.university}"
        if user.graduation_year:
            edu += f" ({user.graduation_year})"
        if user.cgpa:
            edu += f" | CGPA: {user.cgpa}"
        sections.append(edu)

    # Skills
    skills = user.get_skills_list()
    if skills:
        sections.append(f"\n--- Technical Skills ---\n{', '.join(skills)}")
    soft = user.get_soft_skills_list() if hasattr(user, 'get_soft_skills_list') else []
    if soft:
        sections.append(f"Soft Skills: {', '.join(soft)}")

    # Work experience
    work = user.get_work_experience() if hasattr(user, 'get_work_experience') else []
    if work:
        lines = ["\n--- Work Experience ---"]
        for w in work:
            lines.append(f"• {w.get('title','')} at {w.get('company','')} "
                         f"({w.get('start_date','')} – {w.get('end_date','Present')})")
            if w.get('description'):
                lines.append(f"  {w['description'][:300]}")
        sections.append('\n'.join(lines))

    # Internships
    internships = user.get_internships() if hasattr(user, 'get_internships') else []
    if internships:
        lines = ["\n--- Internships ---"]
        for i in internships:
            lines.append(f"• {i.get('title','')} at {i.get('company','')} "
                         f"({i.get('start_date','')} – {i.get('end_date','Present')})")
            if i.get('description'):
                lines.append(f"  {i['description'][:300]}")
        sections.append('\n'.join(lines))

    # Projects
    projects = user.get_projects() if hasattr(user, 'get_projects') else []
    if projects:
        lines = ["\n--- Projects ---"]
        for p in projects:
            lines.append(f"• {p.get('title','Untitled')}")
            if p.get('technologies'):
                lines.append(f"  Tech: {p['technologies']}")
            if p.get('description'):
                lines.append(f"  {p['description'][:300]}")
        sections.append('\n'.join(lines))

    # Certifications
    certs = user.get_certifications() if hasattr(user, 'get_certifications') else []
    if certs:
        lines = ["\n--- Certifications ---"]
        for c in certs:
            lines.append(f"• {c.get('name','')}")
        sections.append('\n'.join(lines))

    # Achievements
    if user.achievements:
        sections.append(f"\n--- Achievements ---\n{user.achievements}")

    return '\n'.join(sections)


def _build_job_text(job) -> str:
    """Flatten a Job object into readable text."""
    parts = [
        f"Job Title: {job.title}",
        f"Company: {job.company}",
        f"Location: {job.location}",
        f"Type: {job.job_type}",
    ]
    if job.salary:
        parts.append(f"Salary: {job.salary}")
    if job.experience:
        parts.append(f"Experience Required: {job.experience} years")
    parts.append(f"\nDescription:\n{job.description}")
    if job.requirements:
        parts.append(f"\nRequirements:\n{job.requirements}")

    # Skills list
    skill_names = []
    for s in (job.skills or []):
        if isinstance(s, dict):
            skill_names.append(s.get('name', str(s)))
        else:
            skill_names.append(str(s))
    if skill_names:
        parts.append(f"\nRequired Skills: {', '.join(skill_names)}")

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Core: keyword matching (used for before/after scoring)
# ---------------------------------------------------------------------------

def compute_keyword_match(user, job) -> dict:
    """Return keywords_matched, keywords_missing, and match score."""
    job_skills = []
    for s in (job.skills or []):
        if isinstance(s, dict):
            name = s.get('name', '')
        else:
            name = str(s)
        if name:
            job_skills.append(name.lower().strip())

    # Also extract notable keywords from description + requirements
    extra_kw = set()
    text_blob = f"{job.description or ''} {job.requirements or ''}".lower()
    # Common tech keywords to look for
    for kw in job_skills:
        extra_kw.add(kw)

    user_skills = [s.lower().strip() for s in user.get_skills_list()]
    user_text = _build_resume_text(user).lower()

    matched = []
    missing = []
    for kw in job_skills:
        if kw in user_skills or kw in user_text:
            matched.append(kw)
        else:
            missing.append(kw)

    total = len(job_skills) if job_skills else 1
    score = int((len(matched) / total) * 100)

    return {
        'matched': matched,
        'missing': missing,
        'score': min(score, 100),
    }


# ---------------------------------------------------------------------------
# AI suggestion generation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert resume optimization agent for the JobElevate platform.
Your role: analyze a candidate's resume against a specific job posting and produce
precise, actionable suggestions to tailor the resume for maximum ATS compatibility
and recruiter appeal.

RULES:
1. Each suggestion must target a specific resume SECTION: "summary", "skills",
   "experience", "projects", "certifications", "education", or "achievements".
2. Each suggestion must have a TYPE: "add" (add new content), "improve" (rewrite
   existing content), "reorder" (change section order/priority), or "remove"
   (drop irrelevant content).
3. Each suggestion must have a PRIORITY: "high" (critical for passing ATS/recruiter
   screening), "medium" (noticeably improves chances), or "low" (nice polish).
4. "current" field = the user's existing text for that section (empty string if adding new).
5. "suggested" field = your recommended replacement/addition text. Be specific.
6. "reason" field = one-sentence explanation of WHY this change helps for THIS job.

OUTPUT FORMAT — strict JSON array, no markdown, no comments:
[
  {
    "section": "skills",
    "type": "add",
    "priority": "high",
    "current": "",
    "suggested": "Add 'Kubernetes' to technical skills",
    "reason": "Job requires Kubernetes experience and it's missing from your resume."
  }
]

Generate 5-12 suggestions, prioritising high-impact changes first.
Do NOT suggest fabricating experience the candidate doesn't have.
Focus on: keyword alignment, phrasing improvements, quantifying achievements,
reordering sections for relevance, and removing irrelevant details."""


def generate_ai_suggestions(user, job, resume=None) -> List[Dict]:
    """
    Call Gemini to produce resume tailoring suggestions.
    Falls back to rule-based suggestions if AI is unavailable.
    """
    resume_text = _build_resume_text(user, resume)
    job_text = _build_job_text(job)

    prompt = (
        f"=== CANDIDATE RESUME ===\n{resume_text}\n\n"
        f"=== TARGET JOB POSTING ===\n{job_text}\n\n"
        "Analyze the resume against the job and produce tailoring suggestions."
    )

    suggestions = []
    if GEMINI_AVAILABLE and GEMINI_CLIENT:
        try:
            response = GEMINI_CLIENT.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    'system_instruction': SYSTEM_PROMPT,
                    'temperature': 0.4,
                    'max_output_tokens': 2048,
                },
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            if raw.endswith('```'):
                raw = raw[:-3]
            raw = raw.strip()

            suggestions = json.loads(raw)
            if not isinstance(suggestions, list):
                suggestions = []
            logger.info(f"✓ AI generated {len(suggestions)} resume suggestions")
        except json.JSONDecodeError as e:
            logger.warning(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Gemini error in resume AI: {e}")

    # Fallback: rule-based suggestions if AI produced nothing
    if not suggestions:
        suggestions = _rule_based_suggestions(user, job)

    # Tag each suggestion with a unique id
    for i, s in enumerate(suggestions):
        s['id'] = str(uuid.uuid4())[:8]
        s.setdefault('accepted', None)  # None=pending, True=accepted, False=rejected

    return suggestions


def _rule_based_suggestions(user, job) -> List[Dict]:
    """Generate basic suggestions using keyword matching when AI is unavailable."""
    kw = compute_keyword_match(user, job)
    suggestions = []

    # 1. Missing skills
    for skill in kw['missing'][:5]:
        suggestions.append({
            'section': 'skills',
            'type': 'add',
            'priority': 'high',
            'current': '',
            'suggested': f"Add '{skill.title()}' to your technical skills if you have experience with it.",
            'reason': f"The job requires {skill.title()} but it's not listed on your resume.",
        })

    # 2. Improve summary to mention role
    if user.objective:
        suggestions.append({
            'section': 'summary',
            'type': 'improve',
            'priority': 'high',
            'current': user.objective[:200],
            'suggested': f"Rewrite your summary to mention the '{job.title}' role and highlight your most relevant skills: {', '.join(kw['matched'][:4]) or 'your core skills'}.",
            'reason': 'A tailored summary that mirrors the job title catches the recruiter\'s attention immediately.',
        })
    else:
        suggestions.append({
            'section': 'summary',
            'type': 'add',
            'priority': 'high',
            'current': '',
            'suggested': f"Add a professional summary targeting the {job.title} role at {job.company}.",
            'reason': 'Resumes without a summary are less likely to pass ATS screening.',
        })

    # 3. Quantify experience
    work = user.get_work_experience() if hasattr(user, 'get_work_experience') else []
    if work:
        suggestions.append({
            'section': 'experience',
            'type': 'improve',
            'priority': 'medium',
            'current': work[0].get('description', '')[:200],
            'suggested': 'Add metrics and quantifiable results (e.g., "Improved performance by 30%", "Managed a team of 5").',
            'reason': 'Quantified achievements are 40% more likely to get recruiter callbacks.',
        })

    # 4. Projects relevance
    projects = user.get_projects() if hasattr(user, 'get_projects') else []
    if projects:
        job_desc_lower = (job.description or '').lower()
        for p in projects[:2]:
            tech = (p.get('technologies') or '').lower()
            overlap = [s for s in kw['matched'] if s in tech]
            if not overlap:
                suggestions.append({
                    'section': 'projects',
                    'type': 'improve',
                    'priority': 'medium',
                    'current': p.get('title', ''),
                    'suggested': f"In your '{p.get('title', '')}' project, emphasize technologies relevant to this job: {', '.join(kw['missing'][:3]) or 'key required skills'}.",
                    'reason': 'Linking project tech stack to job requirements strengthens your application.',
                })

    # 5. Section ordering
    if job.experience and job.experience > 2:
        suggestions.append({
            'section': 'experience',
            'type': 'reorder',
            'priority': 'low',
            'current': '',
            'suggested': 'Move Work Experience above Projects/Education since this role requires significant experience.',
            'reason': 'Experienced roles benefit from leading with work history rather than education.',
        })

    return suggestions


# ---------------------------------------------------------------------------
# Post-tailoring: apply accepted suggestions to produce snapshot data
# ---------------------------------------------------------------------------

def apply_suggestions_to_resume(user, tailored_resume) -> dict:
    """
    After the user accepts/rejects suggestions, produce tailored content
    snapshots that can be rendered in the preview/download.
    Returns updated field values for the TailoredResume model.
    """
    accepted = tailored_resume.accepted_suggestions
    kw_after = compute_keyword_match(user, tailored_resume.job)

    # Start with user's original data
    skills = list(user.get_skills_list())
    objective = user.objective or ''
    experience = user.get_work_experience() if hasattr(user, 'get_work_experience') else []
    projects = user.get_projects() if hasattr(user, 'get_projects') else []

    for sug in accepted:
        section = sug.get('section', '')
        stype = sug.get('type', '')

        if section == 'skills' and stype == 'add':
            # Extract skill name from suggestion text
            suggested = sug.get('suggested', '')
            # Try to extract quoted skill name
            if "'" in suggested:
                parts = suggested.split("'")
                if len(parts) >= 2:
                    new_skill = parts[1]
                    if new_skill.lower() not in [s.lower() for s in skills]:
                        skills.append(new_skill)

        elif section == 'summary' and stype in ('improve', 'add'):
            if sug.get('suggested'):
                objective = sug['suggested']

    # Re-compute match after accepting
    # Approximate: add accepted skill keywords
    all_text = ' '.join(skills).lower() + ' ' + objective.lower()
    job_skills = []
    for s in (tailored_resume.job.skills or []):
        name = s.get('name', str(s)) if isinstance(s, dict) else str(s)
        job_skills.append(name.lower().strip())

    matched = [k for k in job_skills if k in all_text]
    missing = [k for k in job_skills if k not in all_text]
    total = len(job_skills) if job_skills else 1
    score_after = min(int((len(matched) / total) * 100), 100)

    return {
        'tailored_skills': skills,
        'tailored_objective': objective,
        'tailored_experience': experience,
        'tailored_projects': projects,
        'match_score_after': score_after,
        'keywords_matched': matched,
        'keywords_missing': missing,
    }
