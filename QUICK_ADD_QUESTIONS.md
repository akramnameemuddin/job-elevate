# Quick Reference: Adding Questions for New Skills

## When Recruiter Posts Job with New Skill (e.g., Hadoop)

### ❌ What Happens WITHOUT Questions
```
Recruiter posts "Hadoop Developer" job
  ↓
Job seeker clicks "Add & Take Assessment"
  ↓
System finds 0 Hadoop questions in database
  ↓
Falls back to 6-8 generic template questions
  ↓
Assessment is poor quality and meaningless ❌
```

### ✅ What Happens WITH Questions  
```
Developer adds 30 Hadoop questions (one-time)
  ↓
Recruiter posts "Hadoop Developer" job
  ↓
Job seeker clicks "Add & Take Assessment"
  ↓
System finds 30 Hadoop questions in database
  ↓
Randomly selects 20 questions (8 easy, 6 medium, 6 hard)
  ↓
Assessment is high quality and meaningful ✅
```

---

## 3-Step Process to Add Questions

### Step 1: Add Question Method

**File:** `backend/assessments/management/commands/populate_technical_questions.py`

**Location:** After `get_aws_questions()` method (around line 665)

```python
def get_hadoop_questions(self):
    """30 Hadoop questions"""
    return [
        # 12 Easy (5 points each)
        {'question': 'What is Hadoop?', 'options': ['Framework', 'Database', 'Language', 'OS'], 'correct_answer': 'Framework', 'difficulty': 'easy', 'points': 5},
        # ... 11 more easy
        
        # 9 Medium (10 points each)
        {'question': 'What is speculative execution?', 'options': ['...'], 'correct_answer': '...', 'difficulty': 'medium', 'points': 10},
        # ... 8 more medium
        
        # 9 Hard (15 points each)  
        {'question': 'What is HDFS Federation?', 'options': ['...'], 'correct_answer': '...', 'difficulty': 'hard', 'points': 15},
        # ... 8 more hard
    ]
```

### Step 2: Add to Skill Mapping

**Same file, around line 100-122:**

```python
skill_questions = {
    'Python': self.get_python_questions(),
    # ... existing skills
    'Hadoop': self.get_hadoop_questions(),  # Add this
    'hadoop': self.get_hadoop_questions(),  # Case variation
}
```

### Step 3: Create Skill & Populate

```bash
# Terminal 1: Create skill in database
cd backend
python manage.py shell -c "
from assessments.models import Skill, SkillCategory
category, _ = SkillCategory.objects.get_or_create(name='Big Data')
Skill.objects.create(name='Hadoop', description='Distributed processing', category=category, is_active=True)
"

# Terminal 2: Populate questions
python manage.py populate_technical_questions --skill="Hadoop"
```

**Output:**
```
[OK] Hadoop: Added 30 questions (Total: 30/100)
[SUCCESS] Question population completed!
```

---

## Question Format Template

```python
{
    'question': 'Your question here?',
    'options': [
        'Option A',
        'Option B',
        'Option C', 
        'Option D'
    ],
    'correct_answer': 'Option A',  # EXACT TEXT, not index!
    'difficulty': 'easy',          # easy, medium, or hard
    'points': 5,                   # 5=easy, 10=medium, 15=hard
    'explanation': 'Optional'      # Why this answer is correct
}
```

---

## Current System Status

**Total:** 708 questions across 26 skills (27.2 avg per skill)

**✅ Ready for Assessments (20+ questions):**
- Python (48), JavaScript (46), Java (46)
- Git (45), SQL (44), NumPy (44)
- Excel (37), Power BI (37)
- Django (32), React (39)
- **Hadoop (30)** ⭐ Just added!
- Pandas (30), HTML/CSS (30)
- Data Analysis (20), Machine Learning (20)
- AWS (20), Docker (20)

**⚠️ Need More Questions:**
- C++ (0), Communication (0)
- TypeScript (7), Tableau (7), Flask (7)
- REST APIs (3)

---

## Testing Your New Questions

After adding questions, test the full workflow:

```bash
# 1. Verify questions were added
python manage.py shell -c "
from assessments.models import Skill, QuestionBank
skill = Skill.objects.get(name='Hadoop')
print(f'Questions: {QuestionBank.objects.filter(skill=skill).count()}')
"

# 2. Start Django server
python manage.py runserver

# 3. In browser:
# - Login as recruiter
# - Post job with Hadoop skill
# - Login as job seeker  
# - Claim Hadoop skill from job
# - Take assessment (should see 20 questions)
# - Check results page
```

---

## Tips

✅ **DO:**
- Write 30 questions per skill (12 easy, 9 medium, 9 hard)
- Use exact text match for `correct_answer`
- Test questions before deploying
- Add explanations for learning value
- Keep questions realistic and practical

❌ **DON'T:**
- Use indices for correct answers (use text)
- Make easy questions trivial or hard questions obscure
- Forget to add both "Skill" and "skill" case variations
- Skip testing - always verify questions work

---

## Quick Commands

```bash
# See all skills and question counts
python manage.py shell -c "
from assessments.models import Skill, QuestionBank
for s in Skill.objects.filter(is_active=True):
    print(f'{s.name}: {QuestionBank.objects.filter(skill=s).count()}')
"

# Populate specific skill
python manage.py populate_technical_questions --skill="Hadoop"

# Populate all skills at once
python manage.py populate_technical_questions

# Create new skill
python manage.py shell -c "
from assessments.models import Skill, SkillCategory
cat = SkillCategory.objects.get_or_create(name='Your Category')[0]
Skill.objects.create(name='Your Skill', description='...', category=cat, is_active=True)
"
```

---

## Example: Real-World Scenario

**Scenario:** Company needs "Kubernetes" assessments

**Solution:**

1. **Write 30 questions** following the template
2. **Add method** in populate_technical_questions.py:
   ```python
   def get_kubernetes_questions(self):
       return [...]  # 30 questions
   ```
3. **Add to mapping**:
   ```python
   'Kubernetes': self.get_kubernetes_questions(),
   'kubernetes': self.get_kubernetes_questions(),
   ```
4. **Create skill & populate**:
   ```bash
   python manage.py shell -c "..."  # Create skill
   python manage.py populate_technical_questions --skill="Kubernetes"
   ```
5. **Done!** Kubernetes is now available for assessments

**Time investment:** 1-2 hours to write quality questions = Unlimited assessments forever!

---

For detailed guide, see: `HOW_TO_ADD_QUESTIONS.md`
