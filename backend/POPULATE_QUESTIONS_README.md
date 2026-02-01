# Populating Assessment Questions

This guide explains how to populate technical skills with 100 relevant questions each.

## Available Commands

### 1. Generate Questions Using AI (Recommended)
Uses Google Gemini AI to generate skill-specific, relevant questions:

```bash
# Generate 100 questions for all skills
python manage.py generate_skill_questions

# Generate for a specific skill
python manage.py generate_skill_questions --skill="Python"

# Overwrite existing questions
python manage.py generate_skill_questions --skill="Excel" --overwrite

# Custom batch size (default: 20)
python manage.py generate_skill_questions --batch-size=10
```

**Features:**
- Generates 100 questions per skill
- Uses AI to ensure questions are relevant and skill-specific
- Distribution: 40% easy, 30% medium, 30% hard
- Generates in batches to avoid API timeouts
- Validates question quality before saving

### 2. Populate with Pre-defined Questions
Uses pre-written question templates (faster, no API required):

```bash
# Populate all skills with templates
python manage.py populate_technical_questions

# Populate specific skill
python manage.py populate_technical_questions --skill="React"
```

**Note:** This command has limited questions pre-defined. Use AI generation for comprehensive coverage.

## Workflow

### Quick Start (Recommended)
```bash
# 1. Activate virtual environment
cd backend
source venv/Scripts/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 2. Generate questions for all skills using AI
python manage.py generate_skill_questions

# 3. Check results
python manage.py shell
>>> from assessments.models import Skill, QuestionBank
>>> for skill in Skill.objects.all():
...     count = QuestionBank.objects.filter(skill=skill).count()
...     print(f"{skill.name}: {count} questions")
```

### For Specific Skills
```bash
# Generate Python questions
python manage.py generate_skill_questions --skill="Python"

# Generate SQL questions
python manage.py generate_skill_questions --skill="SQL"

# Generate JavaScript questions
python manage.py generate_skill_questions --skill="JavaScript"
```

### Regenerate Questions
```bash
# Overwrite existing questions with new AI-generated ones
python manage.py generate_skill_questions --skill="Django" --overwrite
```

## Question Distribution

The system automatically:
- Generates **100 questions per skill**
- Uses **40% easy** (40 questions) for basic concepts
- Uses **30% medium** (30 questions) for practical applications
- Uses **30% hard** (30 questions) for advanced topics
- Randomly selects **20 questions** per assessment (8 easy, 6 medium, 6 hard)

## Requirements

### For AI Generation:
1. Google Gemini API key configured in `.env`:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. Install required package:
   ```bash
   pip install google-generativeai
   ```

### For Template Questions:
No additional requirements - works offline.

## Troubleshooting

### "AI generation failed"
- Check your `GOOGLE_API_KEY` in `.env` file
- Verify API quota hasn't been exceeded
- Try reducing batch size: `--batch-size=10`

### "Already has X questions (skipped)"
- Use `--overwrite` flag to regenerate
- Or delete questions manually and regenerate

### Check Question Count
```bash
python manage.py shell -c "from assessments.models import Skill, QuestionBank; [print(f'{s.name}: {QuestionBank.objects.filter(skill=s).count()}') for s in Skill.objects.all()]"
```

### Clear All Questions (Careful!)
```python
from assessments.models import QuestionBank
QuestionBank.objects.all().delete()
```

## Best Practices

1. **Start with AI Generation** for comprehensive, relevant questions
2. **Generate in batches** during off-peak hours (API limits)
3. **Review questions** periodically for accuracy
4. **Update questions** when technology standards change
5. **Monitor usage** to ensure 20-question randomization works correctly

## Assessment Flow

1. User takes assessment
2. System randomly selects **20 questions** from the 100 available
3. Distribution: 8 easy, 6 medium, 6 hard
4. Questions shuffled to prevent memorization
5. Options shuffled per user for anti-cheating

This ensures:
- ✅ Every assessment is unique
- ✅ Questions are always relevant
- ✅ Users can't memorize answer patterns
- ✅ Fair evaluation across all users
