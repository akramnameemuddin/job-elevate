# Google Gemini API Setup Guide

## ✅ Changes Made

- **Removed**: OpenAI API (costly, quota issues)
- **Added**: Google Gemini API (FREE, unlimited for basic usage)
- **Result**: Each user gets UNIQUE, AI-generated questions

## 🔑 Get Your FREE Google Gemini API Key

### Option 1: Google AI Studio (Recommended)
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Choose "Create API key in new project"
4. Copy your API key

### Option 2: Google MakerSuite
1. Visit: https://makersuite.google.com/app/apikey
2. Follow the same steps

## 🔧 Configuration

### 1. Add API Key to `.env` file

Open `backend/backend/.env` and update:

```env
GOOGLE_API_KEY="your-actual-api-key-here"
```

### 2. Restart Django Server

Stop the current server (Ctrl+C) and restart:

```bash
cd c:/job-elevate/backend
python manage.py runserver
```

### 3. Regenerate Assessments with NEW Questions

Delete old assessments and create fresh ones:

```bash
python manage.py shell
```

Then run:

```python
from assessments.models import Assessment, AssessmentAttempt
from assessments.skill_intelligence_engine import SkillAssessmentGenerator
from assessments.models import Skill

# Delete all old assessments
Assessment.objects.all().delete()
AssessmentAttempt.objects.all().delete()

# Generate new assessments for SQL
sql_skill = Skill.objects.get(name='SQL')
assessment = SkillAssessmentGenerator.generate_assessment(sql_skill)
print(f"✅ Created assessment with {assessment.questions.count()} UNIQUE questions")

# Check first question
first_q = assessment.questions.first()
print(f"\nSample: {first_q.question_text}")
```

## 🎯 Benefits of Google Gemini

1. **FREE**: No credit card required
2. **Generous Limits**: 60 requests per minute
3. **High Quality**: Advanced AI model
4. **UNIQUE Questions**: Each user gets different questions
5. **No Quota Issues**: Unlike OpenAI

## 🧪 Test the Integration

Run this to test if it's working:

```bash
python manage.py shell
```

```python
from assessments.gpt_quiz_generator import ai_quiz_generator

# Test generation
questions = ai_quiz_generator.generate_questions_for_skill(
    skill_name="SQL",
    skill_description="Database querying",
    basic_count=2,
    intermediate_count=1,
    advanced_count=1
)

# Check results
print(f"Basic: {len(questions['basic'])} questions")
print(f"Sample: {questions['basic'][0]['question']}")
```

## 📝 What Changed in the Code

1. **gpt_quiz_generator.py**: Now uses Google Gemini instead of OpenAI
2. **requirements.txt**: Replaced `openai` with `google-generativeai`
3. **settings.py**: Changed `OPENAI_API_KEY` to `GOOGLE_API_KEY`
4. **.env**: Updated API key configuration

## 🚨 Important Notes

- **Each assessment generates UNIQUE questions** - no two users get the same questions
- **Higher temperature (0.9)** ensures maximum variety
- **Random seeds** added to prompts for uniqueness
- **Fallback questions** still available if API fails

## 💡 API Key Limits

**Free Tier (No Credit Card):**
- 60 requests per minute
- 1500 requests per day
- More than enough for your application!

If you need more, you can upgrade to paid tier (still much cheaper than OpenAI).

## 🔍 Troubleshooting

**Issue**: "No Google API key found"
- Solution: Make sure GOOGLE_API_KEY is set in `.env` file

**Issue**: "API key invalid"
- Solution: Regenerate your key at https://aistudio.google.com/app/apikey

**Issue**: "Rate limit exceeded"
- Solution: You hit the 60/minute limit. Wait a minute or upgrade.

## ✨ You're All Set!

Once you add your API key and restart the server, every user will get completely unique, AI-generated questions for their assessments!
