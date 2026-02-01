# On-Demand Question Generation System

## 🎯 Overview

The assessment system now uses **smart on-demand generation** instead of bulk pre-generation. Questions are generated **only when users need them**, solving rate limit issues and reducing API waste.

## How It Works

### Traditional Approach (OLD) ❌
```
Admin runs command → Generate 100 questions for ALL skills → Takes 4-6 hours → Rate limit errors
```

### On-Demand Approach (NEW) ✅
```
User starts assessment → Generate 20 questions for THAT skill → Takes <1 minute → Gradually builds to 100
```

## System Logic

### When User Starts Assessment:

1. **Check existing questions for skill**
   ```
   If questions >= 100: Use existing (no generation)
   If questions < 100: Use existing + generate 20 more
   If questions = 0: Generate first batch of 20 (blocks user, but only once)
   ```

2. **Question Selection**
   - Always selects 20 questions from available pool
   - Randomizes from existing questions
   - Ensures difficulty balance: 8 easy, 6 medium, 6 hard

3. **Gradual Growth**
   - First user: 0 → 20 questions
   - Second user: 20 → 40 questions
   - Third user: 40 → 60 questions
   - Fourth user: 60 → 80 questions
   - Fifth user: 80 → 100 questions (target reached!)
   - Sixth+ users: Use existing 100 questions (no new generation)

## Benefits

### 1. **Solves Rate Limits** 🚀
- Only generates when needed
- Spreads API calls across time
- No bulk generation = no rate limit errors
- Perfect for free tier API quota

### 2. **Fast User Experience** ⚡
- First-time users: ~30 seconds (generates 20 questions)
- Subsequent users: Instant (uses existing questions)
- No waiting for 100-question pre-generation

### 3. **Smart Resource Usage** 💰
- Unpopular skills: Generate only when users need them
- Popular skills: Build up to 100 naturally
- No API waste on unused skills

### 4. **Natural Quality Improvement** 📈
- Questions improve through real usage
- Can add manual curation as skills grow
- Identifies which skills need better questions

## Example Scenarios

### Scenario 1: Popular Skill (Python)
```
Day 1: User 1 starts Python assessment → 0 → 20 questions
Day 1: User 2 starts Python assessment → 20 → 40 questions
Day 2: User 3 starts Python assessment → 40 → 60 questions
Day 2: User 4 starts Python assessment → 60 → 80 questions
Day 3: User 5 starts Python assessment → 80 → 100 questions
Day 3+: All future users use existing 100 questions (instant)
```

### Scenario 2: Niche Skill (COBOL)
```
Week 1: No users → 0 questions (no API waste)
Week 2: First user → 0 → 20 questions
Month 2: Second user → 20 → 40 questions
(Grows slowly, matches actual demand)
```

### Scenario 3: Rate Limit Hit
```
User starts assessment → API rate limit → Falls back to template questions
- Still generates 6-8 generic questions
- User can complete assessment
- Next user (after cooldown) gets AI questions
```

## Configuration

### Question Counts
- **Per batch**: 20 questions (8 easy, 6 medium, 6 hard)
- **Target per skill**: 100 questions
- **Minimum for assessment**: 1 question (system works with any count)

### Generation Strategy
Located in: `assessments/views.py`

```python
def _get_or_generate_questions(skill):
    current = QuestionBank.objects.filter(skill=skill).count()
    
    if current >= 100:
        return existing  # No generation
    elif current > 0:
        generate_more(20)  # Non-blocking
        return existing
    else:
        generate_first(20)  # Blocking (first time only)
        return new_questions
```

### Fallback System
1. **Try AI generation** (Google Gemini)
2. **If rate limit**: Retry 3 times with exponential backoff
3. **If still fails**: Use template questions (generic but functional)
4. **Template count**: 6-8 questions per skill

## Testing

### Test On-Demand Generation
```bash
cd backend
python manage.py test_ondemand_generation --skill="Python"
```

### Check Question Counts
```bash
python manage.py shell -c "
from assessments.models import Skill, QuestionBank
for skill in Skill.objects.all():
    count = QuestionBank.objects.filter(skill=skill).count()
    print(f'{skill.name}: {count}/100')
"
```

### Simulate User Flow
```bash
# Create test user and start assessment through UI
# System will generate questions automatically
```

## Monitoring

### Track Question Growth
```python
# In Django shell
from assessments.models import Skill, QuestionBank
from django.db.models import Count

stats = Skill.objects.annotate(
    question_count=Count('questionbank')
).values('name', 'question_count')

for s in stats:
    progress = (s['question_count'] / 100) * 100
    print(f"{s['name']}: {s['question_count']}/100 ({progress:.0f}%)")
```

### Identify Popular Skills
```python
# Skills with most questions = most popular
from assessments.models import Skill, QuestionBank
from django.db.models import Count

popular = Skill.objects.annotate(
    q_count=Count('questionbank')
).order_by('-q_count')[:10]

for skill in popular:
    print(f"{skill.name}: {skill.q_count} questions")
```

## Migration from Old System

### If You Already Ran Bulk Generation
**No action needed!** System works with existing questions:
- Uses existing questions first
- Only generates more if count < 100
- Seamless transition

### If Starting Fresh
**Perfect!** System is ready to go:
1. Users start assessments
2. Questions generate automatically
3. No manual intervention needed

## Comparison: Old vs New

| Feature | Bulk Pre-Generation | On-Demand Generation |
|---------|-------------------|---------------------|
| **Setup Time** | 4-6 hours | 0 minutes |
| **Rate Limits** | Frequent errors | Rare (spread over time) |
| **API Usage** | All skills upfront | Only popular skills |
| **User Wait** | 0s (but admin waits hours) | 30s first time, 0s after |
| **Flexibility** | Fixed 100 per skill | Grows with demand |
| **Resource Waste** | High (unused skills) | Low (demand-driven) |

## Best Practices

### 1. **Let It Grow Naturally**
- Don't pre-generate all skills
- Let user demand drive question creation
- Monitor which skills need attention

### 2. **Supplement with Templates**
- Keep template questions as fallback
- Add manual questions for critical skills
- Use templates during rate limit periods

### 3. **Monitor Growth**
- Track question counts weekly
- Identify skills stuck at low counts
- Manually boost important skills

### 4. **Quality Over Quantity**
- 20 good questions > 100 mediocre questions
- Review AI-generated questions periodically
- Remove or improve low-quality questions

## Troubleshooting

### Problem: User waits too long on first assessment
**Solution**: Pre-generate 20 questions for top 5 skills manually

### Problem: Rate limit errors still occurring
**Solution**: 
- Check daily quota (20 requests/day on free tier)
- Template fallback automatically activates
- Wait for quota reset (next day)

### Problem: Questions not improving to 100
**Solution**: Skill might be unpopular. Options:
- Leave it (20 questions sufficient)
- Manually add template questions
- Run targeted generation during off-hours

### Problem: Question quality inconsistent
**Solution**:
- Review questions in Django admin
- Delete low-quality ones
- Regenerate or add manual replacements

## Future Enhancements

### Possible Improvements
1. **Background Task Queue** - Generate without blocking users
2. **Smart Batch Sizing** - Adjust count based on API quota
3. **Quality Scoring** - Users rate questions, auto-remove bad ones
4. **A/B Testing** - Compare AI vs template question performance
5. **Skill Popularity Tracking** - Prioritize generation for trending skills

## Summary

The on-demand system transforms question generation from a **blocker** into a **background process**:

- ✅ No upfront time investment
- ✅ No rate limit issues
- ✅ No API waste
- ✅ Fast user experience
- ✅ Natural growth pattern
- ✅ Works immediately

**Launch your platform today** and let the question bank build itself! 🚀
