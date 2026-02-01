# How to Add Questions for New Skills

## Problem: Recruiter Posts Job with Skill Not in System

**Example:** Recruiter posts job requiring "Hadoop" skill, but system has 0 Hadoop questions.

**What happens now:**
1. Job seeker claims Hadoop skill from job
2. System redirects to assessment
3. System finds 0 questions in QuestionBank for Hadoop
4. Falls back to 6-8 generic template questions (poor quality)
5. Assessment runs but results are meaningless

---

## Solution: 3 Methods to Add Questions

### **Method 1: Add to Template Command** ⭐ RECOMMENDED

This is the best approach - questions are version-controlled, reusable, and pre-populated.

**Step 1:** Add question method in `assessments/management/commands/populate_technical_questions.py`

```python
def get_hadoop_questions(self):
    """30 Hadoop questions"""
    return [
        # Easy questions (12) - 5 points each
        {
            'question': 'What is Hadoop?',
            'options': [
                'Distributed data processing framework',
                'Database',
                'Programming language',
                'Operating system'
            ],
            'correct_answer': 'Distributed data processing framework',
            'difficulty': 'easy',
            'points': 5
        },
        # ... add 11 more easy questions
        
        # Medium questions (9) - 10 points each
        {
            'question': 'What is speculative execution?',
            'options': [
                'Launching duplicate tasks when one is slow',
                'Predicting results',
                'Planning execution',
                'Optimizing queries'
            ],
            'correct_answer': 'Launching duplicate tasks when one is slow',
            'difficulty': 'medium',
            'points': 10
        },
        # ... add 8 more medium questions
        
        # Hard questions (9) - 15 points each
        {
            'question': 'What is HDFS Federation?',
            'options': [
                'Multiple independent NameNodes for scalability',
                'Data federation',
                'Network federation',
                'Cluster federation'
            ],
            'correct_answer': 'Multiple independent NameNodes for scalability',
            'difficulty': 'hard',
            'points': 15
        },
        # ... add 8 more hard questions
    ]
```

**Step 2:** Add to skill mapping dictionary (around line 100-122)

```python
skill_questions = {
    'Python': self.get_python_questions(),
    'SQL': self.get_sql_questions(),
    # ... existing skills
    'Hadoop': self.get_hadoop_questions(),
    'hadoop': self.get_hadoop_questions(),  # Case variation
}
```

**Step 3:** Run populate command

```bash
cd backend
python manage.py populate_technical_questions --skill="Hadoop"
```

**Output:**
```
[OK] Hadoop: Added 30 questions (Total: 30/100)
```

---

### **Method 2: Django Admin Panel** (Quick & Easy)

For quick testing or one-off questions.

**Steps:**

1. Go to Django admin: `http://localhost:8000/admin/`
2. Navigate to **Assessments → Question Banks**
3. Click **"Add Question Bank"**
4. Fill in:
   - **Skill:** Select "Hadoop" (or create new skill first)
   - **Question Text:** "What is Hadoop?"
   - **Options:** `["Framework", "Database", "Language", "OS"]`
   - **Correct Answer:** "Framework" (exact text match!)
   - **Difficulty:** Easy/Medium/Hard
   - **Points:** 5/10/15
   - **Explanation:** (optional)
5. Click **Save**
6. Repeat for 20-30 questions

**Pros:**
- ✅ No coding required
- ✅ Immediate availability
- ✅ Good for testing

**Cons:**
- ❌ Time-consuming for many questions
- ❌ Not version-controlled
- ❌ Hard to backup/replicate

---

### **Method 3: Database Script** (Bulk Import)

For importing questions from Excel/CSV files.

**Example:** You have 100 Hadoop questions in Excel

**Step 1:** Create import script `backend/import_hadoop_questions.py`

```python
import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from assessments.models import Skill, QuestionBank

# Get or create Hadoop skill
hadoop_skill, created = Skill.objects.get_or_create(
    name='Hadoop',
    defaults={
        'description': 'Distributed data processing framework',
        'category': SkillCategory.objects.get_or_create(name='Big Data')[0],
        'is_active': True
    }
)

# Read questions from CSV
with open('hadoop_questions.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        QuestionBank.objects.create(
            skill=hadoop_skill,
            question_text=row['question'],
            options=[row['option1'], row['option2'], row['option3'], row['option4']],
            correct_answer=row['correct_answer'],
            difficulty=row['difficulty'],
            points=int(row['points']),
            explanation=row.get('explanation', ''),
            created_by_ai=False
        )

print(f"Imported {QuestionBank.objects.filter(skill=hadoop_skill).count()} questions")
```

**Step 2:** Create CSV file `hadoop_questions.csv`

```csv
question,option1,option2,option3,option4,correct_answer,difficulty,points,explanation
"What is Hadoop?","Framework","Database","Language","OS","Framework","easy",5,"Distributed processing"
"What is HDFS?","File System","Database","Network","Protocol","File System","easy",5,"Hadoop storage"
```

**Step 3:** Run import

```bash
cd backend
python import_hadoop_questions.py
```

---

## System Flow When New Skill Added

### Before Adding Questions:

```
Recruiter posts job → Job has "Hadoop" skill
   ↓
Job seeker claims skill → System redirects to assessment
   ↓
System checks QuestionBank → Finds 0 Hadoop questions
   ↓
Falls back to templates → Uses 6-8 generic questions
   ↓
Assessment runs → Results are poor quality ❌
```

### After Adding Questions (Method 1):

```
Developer adds get_hadoop_questions() method
   ↓
Runs: python manage.py populate_technical_questions --skill="Hadoop"
   ↓
30 Hadoop questions inserted into QuestionBank
   ↓
Recruiter posts job → Job has "Hadoop" skill
   ↓
Job seeker claims skill → System redirects to assessment
   ↓
System checks QuestionBank → Finds 30 Hadoop questions ✓
   ↓
Randomly selects 20 questions (8 easy, 6 medium, 6 hard)
   ↓
Assessment runs → Results are accurate and meaningful ✓
```

---

## Question Format Requirements

**CRITICAL:** All questions must follow this exact structure:

```python
{
    'question': 'Question text here?',           # Required: String
    'options': [                                  # Required: Array of 4 strings
        'Option A',
        'Option B', 
        'Option C',
        'Option D'
    ],
    'correct_answer': 'Option B',                # Required: EXACT TEXT from options
    'difficulty': 'easy',                        # Required: 'easy', 'medium', or 'hard'
    'points': 10,                                # Required: 5 (easy), 10 (medium), 15 (hard)
    'explanation': 'Optional explanation'        # Optional: String
}
```

**Common Mistakes:**

❌ **Wrong:** `'correct_answer': 1` (index)
✅ **Right:** `'correct_answer': 'Option B'` (exact text)

❌ **Wrong:** `'options': "A, B, C, D"` (string)
✅ **Right:** `'options': ['A', 'B', 'C', 'D']` (array)

❌ **Wrong:** `'difficulty': 'Hard'` (capitalized)
✅ **Right:** `'difficulty': 'hard'` (lowercase)

---

## Distribution Guidelines

**For 30 questions per skill:**
- **12 Easy questions** (40%) - 5 points each = 60 points max
- **9 Medium questions** (30%) - 10 points each = 90 points max  
- **9 Hard questions** (30%) - 15 points each = 135 points max

**For assessments (20 questions selected):**
- **8 Easy** (40%)
- **6 Medium** (30%)
- **6 Hard** (30%)

**Minimum for functional assessments:** 14 questions (system will use all available)

---

## Testing New Questions

After adding questions, test them:

```bash
# Check question count
python manage.py shell -c "
from assessments.models import Skill, QuestionBank
skill = Skill.objects.get(name='Hadoop')
print(f'Hadoop questions: {QuestionBank.objects.filter(skill=skill).count()}')
"

# Take test assessment
# 1. Create a job with Hadoop skill
# 2. Claim the skill
# 3. Take the assessment
# 4. Verify 20 questions appear
# 5. Verify results page shows correct scoring
```

---

## Current System Status

**Skills with 20+ questions (assessment-ready):**

| Skill | Questions | Status |
|-------|-----------|--------|
| Python | 48 | ✅ Ready |
| JavaScript | 46 | ✅ Ready |
| Java | 46 | ✅ Ready |
| Git | 45 | ✅ Ready |
| SQL | 44 | ✅ Ready |
| NumPy | 44 | ✅ Ready |
| Excel | 37 | ✅ Ready |
| Power BI | 37 | ✅ Ready |
| Django | 32 | ✅ Ready |
| React | 32 | ✅ Ready |
| **Hadoop** | **30** | **✅ Ready** (just added!) |
| Pandas | 30 | ✅ Ready |
| HTML/CSS | 30 | ✅ Ready |
| Tableau | 37 | ✅ Ready |

**Skills needing questions:**

| Skill | Questions | Needed |
|-------|-----------|--------|
| C++ | 0 | 30 |
| TypeScript | 7 | 23 |
| Docker | 20 | 10 |
| AWS | 20 | 10 |
| REST APIs | 3 | 27 |

---

## Pro Tips

1. **Use Method 1** for all production skills - it's version-controlled and maintainable
2. **Write realistic questions** - pull from actual job interviews
3. **Test difficulty balance** - easy shouldn't be trivial, hard shouldn't be obscure
4. **Update regularly** - technology changes, questions should too
5. **Add explanations** - helps users learn from mistakes

---

## Need Help?

- Check existing questions in the file for reference
- Python questions (line 125): Best example of structure
- React questions (line 269): Good modern framework example
- Hadoop questions (line 665): Just added - see current implementation

**Total questions in system:** 671 across 25 skills
**Average per skill:** 26.8 questions
**System status:** Production-ready with template-only approach (no AI dependency)
