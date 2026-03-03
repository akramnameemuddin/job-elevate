"""
Seed the community feed with realistic demo posts, comments, and likes.
Creates demo user accounts if they don't exist, then posts on their behalf.

Run with:  python manage.py seed_community_posts
Re-run safe: skips posts that already exist (matched by title).
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from community.models import Post, Comment, Like, Tag, Follow

User = get_user_model()

# ── Demo user profiles ────────────────────────────────────────────────────────
DEMO_USERS = [
    {
        "username": "priya_sharma",
        "full_name": "Priya Sharma",
        "email": "priya.sharma@demo.jobelevate",
        "password": "Demo@12345",
        "user_type": "student",
        "university": "IIT Bombay",
        "degree": "B.Tech Computer Science",
        "graduation_year": 2025,
        "technical_skills": "Python,Django,React,SQL,Machine Learning",
        "job_title": "",
        "organization": "",
    },
    {
        "username": "rahul_verma",
        "full_name": "Rahul Verma",
        "email": "rahul.verma@demo.jobelevate",
        "password": "Demo@12345",
        "user_type": "professional",
        "university": "NIT Trichy",
        "degree": "B.E. Electronics",
        "graduation_year": 2022,
        "technical_skills": "Java,Spring Boot,AWS,Docker,Kubernetes",
        "job_title": "Backend Engineer",
        "organization": "Infosys",
    },
    {
        "username": "aisha_khan",
        "full_name": "Aisha Khan",
        "email": "aisha.khan@demo.jobelevate",
        "password": "Demo@12345",
        "user_type": "professional",
        "university": "BITS Pilani",
        "degree": "M.Sc. Data Science",
        "graduation_year": 2023,
        "technical_skills": "Python,TensorFlow,PyTorch,SQL,Power BI,Tableau",
        "job_title": "Data Scientist",
        "organization": "Wipro",
    },
    {
        "username": "karthik_ms",
        "full_name": "Karthik M S",
        "email": "karthik.ms@demo.jobelevate",
        "password": "Demo@12345",
        "user_type": "student",
        "university": "VIT Vellore",
        "degree": "B.Tech IT",
        "graduation_year": 2026,
        "technical_skills": "JavaScript,Node.js,React,MongoDB,Express",
        "job_title": "",
        "organization": "",
    },
    {
        "username": "sneha_nair",
        "full_name": "Sneha Nair",
        "email": "sneha.nair@demo.jobelevate",
        "password": "Demo@12345",
        "user_type": "recruiter",
        "university": "",
        "degree": "",
        "graduation_year": None,
        "technical_skills": "Recruitment,HR,LinkedIn,ATS",
        "job_title": "Senior Recruiter",
        "organization": "TCS",
        "company_name": "Tata Consultancy Services",
    },
    {
        "username": "arjun_dev",
        "full_name": "Arjun Dev",
        "email": "arjun.dev@demo.jobelevate",
        "password": "Demo@12345",
        "user_type": "professional",
        "university": "IIIT Hyderabad",
        "degree": "M.Tech Software Engineering",
        "graduation_year": 2021,
        "technical_skills": "Python,FastAPI,Microservices,Redis,PostgreSQL,GCP",
        "job_title": "Software Engineer II",
        "organization": "Google",
    },
]

# ── Posts data ─────────────────────────────────────────────────────────────────
# Format: (author_username, post_type, tags_slugs, title, content)
POSTS = [
    (
        "priya_sharma",
        "discussion",
        ["python", "machine-learning", "upskilling"],
        "How I went from 0 to landing an ML internship in 6 months",
        """Six months ago I had no idea what gradient descent was. Today I got an offer from a fintech startup for an ML engineering internship. Here's what actually worked for me:

**1. Stop tutorial hell**
I spent the first month on YouTube and got nowhere. The shift happened when I started building — even broken, ugly projects.

**2. The 3-project rule**
I built exactly 3 projects before applying:
- Sentiment analysis on product reviews (NLP)
- A price prediction model for used cars (regression)  
- A simple recommendation engine (collaborative filtering)

None of them are impressive. But they gave me something real to talk about in interviews.

**3. Used JobElevate's skill gap analysis**
This was genuinely helpful. After adding target job roles, it showed me exactly which skills I was missing. I had Python but needed Pandas, Scikit-learn, and basic SQL — the platform flagged all three and suggested learning paths.

**4. One DSA problem per day, no more**
I see people grinding 5-6 problems daily and burning out. One focused problem with proper understanding is better than rushing through 10.

If you're starting out — build something ugly, put it on GitHub, apply anyway. Rejection is data, not judgement.

What helped YOU break into tech? Drop it below 👇""",
    ),
    (
        "rahul_verma",
        "resource",
        ["career-advice", "interview-tips"],
        "Backend Interview Prep: What actually gets asked at service companies (2025 edition)",
        """After 3 years at Infosys and going through 12 interviews at various companies last year, here's the actual distribution of what gets asked for backend roles (mid-level):

**System Design: 40% of screening weight**
- Design a URL shortener
- Design a notification service
- Rate limiting strategies
- Database sharding basics

Most candidates fail here not because they don't know the answer but because they don't structure their thinking. Use RESHADED: Requirements → Estimation → Storage → High-level → APIs → Deep dive → Edge cases.

**Coding: 35%**
Arrays + hashmaps solve 60% of LeetCode mediums. Learn them cold. Then: sliding window, two pointers, BFS/DFS. That's honestly 80% of what shows up.

**Projects / past work: 25%**
They WILL ask "what's the hardest bug you debugged". Have a real story prepared. STAR format. Mine was a race condition in a payment service — I talk about it in every interview and it lands well every time.

**Tools that helped me:**
- JobElevate for identifying gaps in my profile vs. job requirements
- NeetCode for structured DSA prep
- Excalidraw for system design diagrams

Feel free to DM me if you want the exact list of questions I got at specific companies.""",
    ),
    (
        "aisha_khan",
        "question",
        ["data-science", "machine-learning", "career-advice"],
        "Should I do an MBA after data science or stay technical? Genuinely confused",
        """I'm 2 years into my data science career (currently at Wipro, working on NLP projects). I recently got a call from IIM Calcutta's executive program and honestly it's tempting.

My current situation:
- 2 YOE in DS/ML
- Working on NLP, recommendation systems
- Getting decent at Python + SQL + some cloud
- Want to eventually move into a Principal DS or ML Engineering lead role

My concern: I see a lot of DS folks getting sidelined as companies automate reporting and junior ML work. The MBA seems like it could open product/strategy doors.

But then I see ML engineers at FAANG making 40-60 LPA at 4-5 YOE and thinking — maybe just go deeper technically?

Has anyone here made this choice? Did the MBA actually help or did it distract from the technical track?

Also genuinely curious — does anyone use the AI career coaching feature here? I ran my profile through it and it suggested staying technical for 2 more years before considering management. Curious if others got different advice based on their goals.""",
    ),
    (
        "karthik_ms",
        "discussion",
        ["web-development", "javascript", "job-search"],
        "Honest review: applying to 50 jobs through JobElevate vs. manual LinkedIn applications",
        """I ran an experiment over 2 months. Applied to 50 jobs "the normal way" via LinkedIn (manual applications, generic resume). Then used JobElevate for the next 50.

Here's what I tracked:

| Metric | LinkedIn Manual | JobElevate |
|--------|----------------|------------|
| Response rate | 6% | 22% |
| Interview calls | 2 | 9 |
| Time per application | ~45 min | ~20 min |
| Resume tailoring | None | AI-tailored per job |

The difference was *ridiculous*. The AI tailored resume feature actually restructures your experience to match the job description keywords. I was skeptical but my first callback came within 48 hours of submitting a tailored resume.

The skill gap feature also helped me realize I was applying to roles that needed skills I simply didn't have (React Native, TypeScript) while ignoring jobs where I was a near-perfect match.

**What didn't work**: The job matching isn't perfect for niche roles. For very specialized positions (like WebGL or embedded JS) the recommendations were hit or miss.

Overall — 8/10 would recommend over cold LinkedIn applications. The tailored resume feature alone is worth it.

Anyone else done a similar comparison?""",
    ),
    (
        "sneha_nair",
        "announcement",
        ["job-search", "career-advice", "networking"],
        "TCS is hiring! 200+ openings across Hyderabad, Pune, Chennai — here's what we actually look for",
        """Hi everyone! Sneha here from TCS Talent Acquisition. We have a large hiring push happening right now and I want to give you THE REAL picture — not the job description copy-paste.

**Open roles (as of this week):**
- Software Engineer (0-2 YOE): 80 positions
- Digital Specialist Engineer: 45 positions  
- Data Engineer / ML Engineer: 30 positions
- DevOps / Cloud Engineer: 25 positions
- Business Analyst: 20+ positions

**What we actually care about:**
1. **Communication** — more than you think. If you can't explain what your project does in 2 minutes, that's a red flag for us.
2. **Attitude toward learning** — we know freshers don't know everything. We want to see that you're building skills intentionally.
3. **Real projects** — even a college project matters more than just certifications.

**What we're tired of seeing:**
- Resumes with "Proficient in: Python, Java, C++, React, Angular, Django, Spring, AWS, Azure..." — nobody is proficient in all of these at 21.
- AI-generated cover letters with zero personalization.
- "I'm a quick learner and team player" with no evidence.

**How to apply:**
Drop your resume in the comments or DM me directly. For the best shot, use the AI Tailor Resume feature on this platform — your resume will match our JD keywords much better.

All the best! 🙏""",
    ),
    (
        "arjun_dev",
        "resource",
        ["career-advice", "upskilling", "tech-news"],
        "The skills gap is real: what Google actually looks for vs. what colleges teach",
        """I've been at Google for 4 years now. I also mentor ~10 engineers per year through various programs. The pattern I see is consistent:

**What college teaches:**
- Data structures and algorithms (well)
- OOP concepts (okay)
- OS, DBMS, Networks (surface level)
- Specific languages (varies wildly)

**What we actually test for and need:**
- Can you decompose a complex problem into clean, testable components?
- How do you think about scale? (Not just Big O, but distributed systems thinking)
- Do you write code that other humans can read?
- Can you estimate? Volume, latency, throughput?
- How do you handle ambiguity?

The last one kills most candidates. "Design a notifications system" — most people ask: "what framework should I use?" That's the wrong first question.

**What's genuinely missing from most profiles I review:**
1. Real experience with any database beyond SQLite/MySQL basics
2. Exposure to async patterns (message queues, event-driven)
3. Git workflow beyond "git add . && git commit -m 'changes'"
4. ANY observability — logging, metrics, traces

**The good news:**
These aren't hard to pick up. Build one project that uses Postgres + Redis + a message queue (even locally with Docker). You'll understand more systems in 2 weeks than in a semester of theory.

Use the skill assessment feature here — it's not a gimmick. I ran my team's interns through it and the gap analysis was surprisingly accurate.""",
    ),
    (
        "priya_sharma",
        "question",
        ["resume-help", "interview-tips"],
        "Resume gap: took 8 months off for mental health — honest advice needed",
        """I need actual advice, not generic "just be honest" type responses.

Context: I took 8 months off between graduation and now. The reason was genuine burnout and anxiety that got bad enough that I needed to step back. In that time I did therapy, some online courses, and took care of my health. I'm genuinely better now and ready to work.

The problem: I have a gap on my resume from April to December 2024. Every interview I get asked about it and I panic. I've tried:
- "Personal development and upskilling" — they always probe further
- Being fully honest — one interviewer got visibly uncomfortable
- Listing the courses I did — they ask why I didn't do them while working

I'm not ashamed of what I did. It was the right decision. But the job market is ruthless and I don't know how to frame it without lying (which I won't do) or tanking my chances.

Has anyone navigated this successfully? Especially in the Indian tech job market which feels particularly unforgiving about gaps. Any advice from people in hiring (looking at you @sneha_nair) would be incredibly helpful.""",
    ),
    (
        "rahul_verma",
        "discussion",
        ["python", "web-development", "upskilling"],
        "Django vs FastAPI for new projects in 2025 — real-world considerations",
        """I've built production systems in both and I'm tired of the internet defaulting to "it depends." Let me be specific.

**Use Django when:**
- You're building something with a lot of models, admin, and CRUD
- The team has mixed experience levels (Django's conventions save you)
- You need auth, permissions, and ORM fast
- Your project is more "web app" than "API service"
- You want to ship in 2 weeks not 2 months

**Use FastAPI when:**
- You're building a dedicated API service that already has a frontend
- Async is genuinely needed (high I/O, ML model serving)
- You want automatic OpenAPI docs as part of the workflow
- Your team is Python-first and comfortable with async/await
- Performance actually matters (it does for ML inference endpoints)

**The stuff nobody tells you:**
- FastAPI async is only faster if you actually use async I/O everywhere. Mixing sync DB calls in async routes is worse than just using Django.
- Django REST Framework still gets things done faster for teams building standard REST APIs
- Django's database migration system (with PostgreSQL) is genuinely excellent — FastAPI with Alembic is more manual
- FastAPI + SQLModel is promising but less mature than Django ORM

**My actual take:** If your new project is a microservice that serves ML predictions or high-throughput events — FastAPI. If it's a full product with users, profiles, jobs, dashboards — Django, no contest.

What are you all building and which did you choose?""",
    ),
    (
        "aisha_khan",
        "resource",
        ["data-science", "machine-learning", "upskilling"],
        "Free resources that actually got me interview-ready for DS roles (no paid courses needed)",
        """I've seen too many people spend ₹50,000 on bootcamps and still not be hireable. Here's what genuinely moved the needle for me — and it was all free:

**Statistics & Math foundations**
- StatQuest with Josh Starmer (YouTube) — the best stats teacher on the internet, period
- 3Blue1Brown's Linear Algebra series — watch it even if you think you know linear algebra

**Machine Learning core**
- Fast.ai Practical Deep Learning — top-down approach, you build before you understand theory
- Andrej Karpathy's Neural Networks: Zero to Hero — painful but transforms how you think about models
- Kaggle's free ML courses (Intro to ML, Intermediate ML) — practical and fast

**SQL (massively underrated for DS roles)**
- Mode Analytics SQL Tutorial — best structured learning I found
- SQLZoo — for practice
- Literally just open a SQLite DB and query your own data

**Portfolio building approach that worked for me:**
1. Pick ONE Kaggle competition dataset you find interesting
2. Do a thorough EDA (don't rush this — it shows in notebooks)
3. Try 3 different models, compare properly
4. Write your findings like a blog post

That one notebook got me more interview calls than my entire degree transcript.

**Also:** run the JobElevate skill gap analysis for your target DS roles — it will tell you which specific tools you're missing. For me it flagged SQL and Power BI, both of which came up heavily in actual interviews.

Save this post. Come back to it when you're ready. 🙏""",
    ),
    (
        "sneha_nair",
        "job_sharing",
        ["job-search", "networking"],
        "Referral opportunities: companies actively hiring through my network this week",
        """Good morning everyone! I regularly get requests from my network across companies. Here's what I have this week — all confirmed open positions:

**Immediate Joiners Preferred:**

🏢 **Amazon (Hyderabad)**
- SDE-1: Python/Java, DSA fundamentals
- Package: 18-24 LPA
- Contact: DM me with resume

🏢 **Deloitte USI (Bengaluru)**  
- Data Analyst: SQL, Python, Power BI/Tableau
- Package: 9-14 LPA
- Walk-in this Saturday: 10 AM, Embassy Tech Village

🏢 **PhonePe (Bengaluru)**
- Backend Engineer: Go or Python, distributed systems
- Package: 20-35 LPA
- Referral bonus: ₹50,000 for successful hire

🏢 **Swiggy (Hyderabad/Remote)**
- ML Engineer: Python, Spark, recommendation systems
- Package: 22-38 LPA
- Strong portfolio required

🏢 **Zepto (Mumbai)**
- Full Stack (React + Node): 0-2 YOE fresher role
- Package: 8-12 LPA
- GitHub portfolio required

**How to apply through me:**
1. Make sure your resume is tailored for the role (use AI Tailor Resume if you haven't)
2. DM me with: role name + tailored resume + 2 lines about why you're a fit
3. I'll submit your profile directly to the HR contact

No fees, no catches. I do this because good candidates are hard to find and I want to help both sides. 

Best of luck everyone! 💼""",
    ),
]

# ── Comments per post (by index into POSTS list) ─────────────────────────────
COMMENTS = {
    0: [  # priya_sharma — ML internship post
        ("rahul_verma", "This is genuinely one of the most useful posts I've seen here. The 3-project rule is exactly right — I tell everyone the same thing. Quality over quantity, always."),
        ("karthik_ms", "The skill gap analysis thing is real. I added 5 target roles and it told me I was missing TypeScript and REST API design — things I wouldn't have thought to list as gaps. Changed my prep plan completely."),
        ("arjun_dev", "From someone who reviews 200+ resumes a year — this is accurate. Three well-explained projects > 10 half-finished ones. Also: put the GitHub links on your resume, not just the project names."),
        ("aisha_khan", "The 'one DSA problem per day' advice saved my mental health honestly. I was doing 4-5 and burning out constantly. One with full understanding is so much better."),
        ("sneha_nair", "As a recruiter — yes to all of this. Especially the 'apply anyway' point. We interview for potential too, not just current skill. Congrats on the internship offer! 🎉"),
    ],
    1: [  # rahul_verma — backend interview prep
        ("priya_sharma", "The RESHADED framework is new to me — saving this. Do you have any resources for practicing system design with feedback? Mock interviews or anything?"),
        ("arjun_dev", "Solid framework. I'd add: practice drawing on a whiteboard (or tablet). The physical act of drawing changes how you structure the answer. Most candidates who draw think more clearly."),
        ("karthik_ms", "The race condition story thing is a real tip. My story was debugging a memory leak in a Node.js service — I've used it 4 times and it always prompts follow-up questions in a good way."),
        ("aisha_khan", "What about for DS/ML roles? Is system design that important or does it shift more toward ML system design (feature stores, model serving etc.)?"),
    ],
    2: [  # aisha_khan — MBA question
        ("arjun_dev", "I get asked this constantly. My honest take: if your goal is IC (individual contributor) excellence, the MBA is a detour. If you want to move into product management or strategy, 4-5 YOE + MBA is the right sequence. At 2 YOE, you haven't yet hit the ceiling of the technical track."),
        ("rahul_verma", "My senior at Infosys did an IIM exec program after 6 YOE and it opened product management doors. But he had already grown significantly as an IC first. Timing matters a lot."),
        ("sneha_nair", "From a hiring perspective: for ML/DS principal roles, we look for depth of technical expertise first, then leadership. The MBA helps more for Product or Strategy roles. Pure ML leadership honestly doesn't need it."),
        ("priya_sharma", "I used the AI career coach and it basically said 'deepen Python + cloud + ML systems for 2 more years before considering leadership track.' Seems to match what @arjun_dev is saying."),
    ],
    3: [  # karthik_ms — job application comparison
        ("sneha_nair", "The tailored resume data matches what we see on our end as recruiters. ATS-optimized resumes that match JD keywords get a significantly higher pass-through rate. This isn't a secret but most candidates still don't do it."),
        ("priya_sharma", "Wow the 22% vs 6% response rate difference is significant. Did you notice the quality of the roles was different too, or were these similar-level positions?"),
        ("rahul_verma", "The skill matching for niche roles point is fair. I found it best for mainstream roles (backend, full stack, data analyst). For very specialized positions you still need to do manual targeting."),
        ("arjun_dev", "I shared this post with my mentees. The key insight is that 'fit' isn't just seniority — it's keyword and skill match. Most people apply broadly hoping something sticks. Targeted applications with tailored content win."),
    ],
    4: [  # sneha_nair — TCS hiring
        ("priya_sharma", "The 'quick learner' point hurts because I definitely had that on my resume until last month 😅 Updating now. Thank you for being honest about what recruiters actually think."),
        ("karthik_ms", "The list of skills thing is so real. I removed half my skills list after a feedback session and my response rate actually went up. Less is more when every skill is provable."),
        ("rahul_verma", "Is there a specific day/time to apply that gets more visibility, or is it mostly ATS-filtered regardless? Asking genuinely."),
        ("aisha_khan", "Shared this with my college group. A lot of freshers need this kind of honest recruiter perspective — the usual advice is so sanitized."),
    ],
    5: [  # arjun_dev — Google / skills gap
        ("rahul_verma", "The ambiguity point is underrated. I did a mock interview recently and the interviewer said my biggest strength was asking clarifying questions before jumping in. It's a learnable skill."),
        ("karthik_ms", "The Git workflow point embarrassed me. I literally just used 'git commit -m update' for years. Switched to conventional commits and proper branches last year — it actually makes your GitHub profile look more professional too."),
        ("aisha_khan", "Adding observability to my learning list right now. I've never worked with metrics/traces properly and you're right that it shows in interviews when you can't talk about it."),
        ("priya_sharma", "Ran the skill assessment after reading this. It flagged async programming and Docker as weak areas for me — exactly what you mentioned. Starting with Docker this week."),
        ("sneha_nair", "We actively look for candidates who mention monitoring and logging in system design rounds — it signals production experience. This post should be pinned 📌"),
    ],
    6: [  # priya_sharma — resume gap
        ("arjun_dev", "I've interviewed people with gaps and what matters is the honest, confident framing — not the reason. 'I took time to address a health situation, I'm fully ready now, and here's what I did during that time' is a complete and professional answer. Any interviewer who can't accept that is someone you don't want to work for anyway."),
        ("sneha_nair", "From a hiring perspective: mental health time off is more common than you think and as an industry we're getting better at handling it. I'd suggest being matter-of-fact: 'health reasons, fully resolved, here's what I worked on.' Don't apologize, don't over-explain. And yes — if an interviewer makes it uncomfortable, that's a culture signal."),
        ("aisha_khan", "I had a 4-month gap and framed it as 'career transition and focused upskilling period.' Wasn't entirely untrue. The courses I did were real, even if health was the primary reason. You don't owe anyone a full medical history in a job interview."),
        ("rahul_verma", "First: what you did was courageous and the right call. Second: 'personal development period — completed XYZ courses and worked on ABC project' is the framing I've seen work. The courses you did ARE real. Lead with them."),
    ],
    7: [  # rahul_verma — Django vs FastAPI
        ("arjun_dev", "The async mixing point is the one nobody talks about. I've seen teams switch to FastAPI for 'performance' and then call a blocking ORM in every route. Slower than Django sync in every benchmark. Pick the right tool and use it correctly."),
        ("karthik_ms", "I'm building a job board side project (full CRUD, auth, notifications, dashboard) and went with Django — best decision. The admin panel alone has saved me weeks. Considering FastAPI only for the ML recommendation endpoint as a separate service."),
        ("aisha_khan", "What about for ML model serving specifically? I have a Django project and need to serve a prediction endpoint. Separate FastAPI microservice or add it to Django views?"),
        ("priya_sharma", "This is the most useful framework comparison I've read. Every other post is 'FastAPI is the future' without nuance. Thank you for being specific about use cases."),
    ],
    8: [  # aisha_khan — free resources
        ("priya_sharma", "StatQuest is criminally underrated. I understood PCA for the first time watching that channel after failing to get it from textbooks. Highly recommend for anyone struggling with the math side."),
        ("rahul_verma", "SQLZoo + Mode Analytics is exactly the combo I used. SQL is underestimated for backend too — complex query optimization has come up in 3 of my last 5 interviews."),
        ("karthik_ms", "The 'one Kaggle notebook written like a blog post' strategy actually works for front-end too. I wrote a detailed blog post about a React performance problem I solved and it came up in 2 interviews. Documented thinking > certificate PDFs."),
        ("sneha_nair", "Saving this to share with candidates who ask for resource recommendations. The fact that it's all free removes every excuse for not upskilling. Thank you for putting this together 🙏"),
        ("arjun_dev", "Karpathy's course is hard but worth every minute. The candidates who can explain backprop from scratch in interviews stand out immediately. It's rare and impressive."),
    ],
    9: [  # sneha_nair — referral opportunities
        ("karthik_ms", "Sending my profile for the Zepto role now! Tailoring the resume first like you suggested. Thank you for doing this 🙏"),
        ("priya_sharma", "The PhonePe ML Engineer role sounds perfect for where I'm heading. Tailoring my resume now and will DM you. Thank you so much!"),
        ("aisha_khan", "Shared with 3 people in my network who are actively looking. Posts like this are exactly why this community is valuable."),
        ("rahul_verma", "The Amazon SDE-1 role is interesting. Is the package range for Hyderabad specifically, or is it the same across locations? Asking for a friend who's considering relocating."),
    ],
}


class Command(BaseCommand):
    help = 'Seed community with realistic demo posts, comments, and likes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all demo posts before re-seeding (demo users are never deleted)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = Post.objects.filter(
                author__email__endswith='@demo.jobelevate'
            ).delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} existing demo posts'))

        # ── 1. Create / fetch demo users ──────────────────────────────────────
        user_map = {}
        for data in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'full_name': data['full_name'],
                    'email': data['email'],
                    'user_type': data['user_type'],
                    'university': data.get('university', ''),
                    'degree': data.get('degree', ''),
                    'graduation_year': data.get('graduation_year'),
                    'technical_skills': data.get('technical_skills', ''),
                    'job_title': data.get('job_title', ''),
                    'organization': data.get('organization', ''),
                    'company_name': data.get('company_name', ''),
                    'email_verified': True,
                    'is_active': True,
                },
            )
            if created:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(f'  Created user: {user.username}')
            else:
                self.stdout.write(f'  Found user:   {user.username}')
            user_map[data['username']] = user

        # ── 2. Ensure tags exist ──────────────────────────────────────────────
        all_tag_slugs = {slug for _, _, tags, _, _ in POSTS for slug in tags}
        tag_map = {}
        for slug in all_tag_slugs:
            name = slug.replace('-', ' ').title()
            tag_obj, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': name})
            tag_map[slug] = tag_obj

        # ── 3. Create posts with staggered timestamps ─────────────────────────
        now = timezone.now()
        created_posts = 0
        post_objects = []

        for i, (author_uname, ptype, tag_slugs, title, content) in enumerate(POSTS):
            if Post.objects.filter(title=title).exists():
                self.stdout.write(f'  Skipped (exists): {title[:60]}')
                post_objects.append(Post.objects.get(title=title))
                continue

            # Space posts out over the last 14 days
            hours_ago = (len(POSTS) - i) * 30 + random.randint(0, 12) * 60
            created_at = now - timedelta(hours=hours_ago)

            author = user_map[author_uname]
            post = Post(
                author=author,
                title=title,
                content=content,
                post_type=ptype,
                views=random.randint(40, 320),
                is_active=True,
            )
            post.save()
            # Monkey-patch created_at after save (auto_add_now)
            Post.objects.filter(pk=post.pk).update(created_at=created_at)
            post.refresh_from_db()

            post.tags.set([tag_map[s] for s in tag_slugs])
            post_objects.append(post)
            created_posts += 1
            self.stdout.write(f'  Post created: {title[:60]}')

        # ── 4. Add comments with staggered timestamps ──────────────────────────
        created_comments = 0
        for post_idx, comment_list in COMMENTS.items():
            if post_idx >= len(post_objects):
                continue
            post = post_objects[post_idx]
            post_created = post.created_at

            for j, (commenter_uname, text) in enumerate(comment_list):
                commenter = user_map[commenter_uname]
                # Don't duplicate comments
                if Comment.objects.filter(post=post, author=commenter, content=text).exists():
                    continue
                comment_time = post_created + timedelta(hours=random.randint(1, 48), minutes=j * 7)
                comment = Comment(
                    post=post,
                    author=commenter,
                    content=text,
                    is_active=True,
                )
                comment.save()
                Comment.objects.filter(pk=comment.pk).update(created_at=comment_time)
                created_comments += 1

        # ── 5. Add likes to posts ─────────────────────────────────────────────
        created_likes = 0
        for post in post_objects:
            # Random subset of demo users like each post
            likers = random.sample(list(user_map.values()), k=random.randint(2, len(user_map) - 1))
            for liker in likers:
                if liker == post.author:
                    continue
                already = Like.objects.filter(
                    user=liker, content_type='post', post=post
                ).exists()
                if not already:
                    Like.objects.create(user=liker, content_type='post', post=post)
                    created_likes += 1

        # ── 6. Mutual follows between demo users ──────────────────────────────
        created_follows = 0
        users_list = list(user_map.values())
        for u in users_list:
            # Each user follows 2-3 random others
            others = [x for x in users_list if x != u]
            for target in random.sample(others, k=min(3, len(others))):
                if not Follow.objects.filter(follower=u, content_type='user', user=target).exists():
                    Follow.objects.create(follower=u, content_type='user', user=target)
                    created_follows += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Seeded: {created_posts} posts | {created_comments} comments | '
            f'{created_likes} likes | {created_follows} follows'
        ))
        self.stdout.write(self.style.SUCCESS(
            'Demo users (password: Demo@12345): ' +
            ', '.join(u['username'] for u in DEMO_USERS)
        ))
