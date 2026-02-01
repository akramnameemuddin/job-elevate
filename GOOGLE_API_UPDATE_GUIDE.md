# Google Gemini API Update Guide

## Summary of Changes

The Google Gemini AI service has been updated to use the new `google-genai` package (v1.x) which replaces the deprecated `google.generativeai` package.

## What Changed

### 1. Package Update
- **Old**: `google-generativeai` (deprecated)
- **New**: `google-genai` (current)

### 2. API Changes
- **Model Name Format**: Now requires `models/` prefix (e.g., `models/gemini-2.5-flash`)
- **Client Initialization**: Uses `genai.Client(api_key=...)` instead of `genai.configure()`
- **Generation Method**: `client.models.generate_content()` with `types.GenerateContentConfig`

### 3. Rate Limits
The free tier has strict rate limits:
- **5 requests per minute** for `gemini-2.5-flash`
- **15 requests per minute** for other models

## Fixed Issues

1. ✅ **FutureWarning about deprecated package** - Now using new API
2. ✅ **Unexpected keyword argument 'difficulty'** - Updated method signature
3. ✅ **Model not found (404 errors)** - Fixed model name format
4. ✅ **Rate limit errors (429)** - Added automatic retry with delays
5. ✅ **Unicode encoding errors** - Replaced special characters with ASCII
6. ✅ **API key not found** - Now checks both `GEMINI_API_KEY` and `GOOGLE_API_KEY`

## Current Configuration

### API Key
The system checks for API keys in this order:
1. `settings.GEMINI_API_KEY`
2. `settings.GOOGLE_API_KEY`
3. `os.getenv('GEMINI_API_KEY')`
4. `os.getenv('GOOGLE_API_KEY')`

Currently using: `GOOGLE_API_KEY` from `.env` file

### Model
- **Production Model**: `models/gemini-2.5-flash`
- **Fallback**: Switches to legacy API if new API unavailable
- **Template Fallback**: Uses pre-written questions if API fails

### Rate Limit Handling
- **Automatic retry**: 3 attempts with exponential backoff (15s, 30s, 45s)
- **Batch delays**: 15-second pause between batches
- **Smart fallback**: Uses template questions when quota exceeded

## Using the Question Generation Command

### Basic Usage
```bash
# Generate 100 questions for all skills (SLOW - will take hours due to rate limits)
python manage.py generate_skill_questions

# Generate for specific skill
python manage.py generate_skill_questions --skill="Python"

# Overwrite existing questions
python manage.py generate_skill_questions --skill="Excel" --overwrite

# Adjust batch size (smaller = more API calls but more control)
python manage.py generate_skill_questions --skill="Django" --batch-size=5
```

### Recommended Approach for 100 Questions
Given the rate limit of 5 requests/minute:

**Option 1: Gradual Generation (Recommended)**
Generate questions skill-by-skill over several days:
```bash
# Day 1: Core programming languages
python manage.py generate_skill_questions --skill="Python"
python manage.py generate_skill_questions --skill="JavaScript"

# Day 2: Frameworks
python manage.py generate_skill_questions --skill="Django"
python manage.py generate_skill_questions --skill="React"

# etc...
```

**Option 2: Use Template Questions**
For immediate setup without API limits:
```bash
python manage.py populate_technical_questions
```
This uses pre-written questions (currently has 2-3 per skill, needs expansion to 100).

### Time Estimates
For generating 100 questions per skill:
- **Easy**: 40 questions = 8 batches (5 per batch) = ~2 minutes with delays
- **Medium**: 30 questions = 6 batches = ~1.5 minutes
- **Hard**: 30 questions = 6 batches = ~1.5 minutes
- **Total per skill**: ~5 minutes + API processing time = **~10-15 minutes per skill**

For 25 skills: **~4-6 hours total** (if run continuously)

## Monitoring API Usage
Check your usage at: https://ai.dev/usage?tab=rate-limit

## Troubleshooting

### Still Seeing Deprecation Warning
If you see: "Using deprecated google.generativeai package"
- The new API import failed, falling back to old API
- Check if `google-genai` is installed: `pip show google-genai`
- Reinstall if needed: `pip install --upgrade google-genai`

### Rate Limit Errors
If you see: "429 RESOURCE_EXHAUSTED"
- **Wait 1 minute** and try again
- Reduce `--batch-size` to spread requests over time
- Use `--skill` flag to generate one skill at a time
- Consider upgrading to paid tier for higher limits

### No Questions Generated
If output shows: "0 new questions generated"
- Check if AI service initialized: Should NOT say "AI Service not available"
- Verify API key: `python manage.py shell -c "from assessments.ai_service import question_generator; print(question_generator.ai_available)"`
- Check logs for specific error messages

### Questions Are Low Quality
- Template questions are generic fallbacks
- For better quality, ensure AI generation succeeds
- Review generated questions: `python manage.py shell -c "from assessments.models import QuestionBank, Skill; skill = Skill.objects.get(name='Python'); [print(f'{q.difficulty}: {q.question_text[:50]}...') for q in QuestionBank.objects.filter(skill=skill)[:5]]"`

## Next Steps

1. ✅ **Fixed**: All API integration issues resolved
2. ⏳ **In Progress**: Generate 100 questions per skill (requires time due to rate limits)
3. 📋 **TODO**: Expand template questions to 100 per skill as backup
4. 📋 **TODO**: Set up scheduled task to regenerate questions quarterly
5. 📋 **TODO**: Add admin interface for reviewing/editing questions

## Technical Details

### Files Modified
1. `assessments/ai_service.py` - Updated to support both API versions
2. `assessments/management/commands/generate_skill_questions.py` - Added rate limit handling
3. `requirements.txt` - Already had `google-genai>=0.2.0`

### Backward Compatibility
The service supports both old and new APIs:
- Tries new `google.genai` first
- Falls back to `google.generativeai` if new API unavailable
- Falls back to templates if both APIs fail

This ensures the system works in all environments.
