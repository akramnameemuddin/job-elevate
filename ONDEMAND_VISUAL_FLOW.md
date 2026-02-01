# On-Demand Question Generation: Visual Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   USER STARTS ASSESSMENT                     │
│                  (e.g., Python skill)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         CHECK QUESTION BANK FOR SKILL                        │
│         QuestionBank.objects.filter(skill=Python)            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
              ┌─────────┴─────────┐
              │  Count Questions  │
              └─────────┬─────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    Count >= 100    Count > 0      Count = 0
    ┌───────┐     ┌─────────┐    ┌─────────┐
    │ 100+  │     │ 1-99    │    │   0     │
    └───┬───┘     └────┬────┘    └────┬────┘
        │              │              │
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ USE EXISTING │ │ USE EXISTING │ │  GENERATE    │
│ NO GENERATE  │ │ + GENERATE   │ │  FIRST BATCH │
│              │ │ 20 MORE      │ │  (20 Q's)    │
│ Instant! ✓   │ │ (background) │ │ Wait 30s ⏱️  │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  SELECT 20 QUESTIONS   │
           │  (8 easy, 6 med, 6 hard)│
           └────────────┬───────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  RANDOMIZE & SHUFFLE   │
           │  (anti-cheating)       │
           └────────────┬───────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  CREATE ASSESSMENT     │
           │  ATTEMPT               │
           └────────────┬───────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  SHOW ASSESSMENT PAGE  │
           │  User takes test       │
           └────────────────────────┘
```

## Question Growth Over Time

```
User 1 starts Python assessment:
├─ Questions before: 0
├─ Action: Generate 20 (BLOCKS user ~30s)
├─ Questions after: 20
└─ Result: ████░░░░░░ 20% complete

User 2 starts Python assessment:
├─ Questions before: 20
├─ Action: Use 20 + Generate 20 more (background)
├─ Questions after: 40
└─ Result: ████████░░ 40% complete

User 3 starts Python assessment:
├─ Questions before: 40
├─ Action: Use 40 + Generate 20 more (background)
├─ Questions after: 60
└─ Result: ██████████ 60% complete

User 4 starts Python assessment:
├─ Questions before: 60
├─ Action: Use 60 + Generate 20 more (background)
├─ Questions after: 80
└─ Result: ████████████ 80% complete

User 5 starts Python assessment:
├─ Questions before: 80
├─ Action: Use 80 + Generate 20 more (background)
├─ Questions after: 100
└─ Result: ██████████████ 100% TARGET REACHED! ✓

User 6+ starts Python assessment:
├─ Questions before: 100
├─ Action: Use 100 (NO generation)
├─ Questions after: 100
└─ Result: ██████████████ Instant assessment! ⚡
```

## Rate Limit Handling

```
Generation Attempt:
│
├─ Try AI Generation (Google Gemini)
│  │
│  ├─ Success? → Save questions → Done ✓
│  │
│  └─ Rate Limit (429)?
│     │
│     ├─ Retry 1: Wait 15s → Try again
│     │  └─ Success? → Done ✓
│     │
│     ├─ Retry 2: Wait 30s → Try again
│     │  └─ Success? → Done ✓
│     │
│     └─ Retry 3: Wait 45s → Try again
│        │
│        ├─ Success? → Done ✓
│        │
│        └─ Still failing?
│           │
│           └─ FALLBACK: Use Template Questions
│              └─ Generate 6-8 generic questions → Done ✓
```

## Comparison: Traditional vs On-Demand

### Traditional Bulk Generation
```
TIME: Hour 0
├─ Admin: python manage.py generate_skill_questions
├─ System: Generating for 25 skills...
├─ [████░░░░░░░░░░] 10% (30 minutes)
├─ [████████░░░░░░] 50% (2.5 hours)
├─ [████████████░░] 80% (4 hours)
└─ [██████████████] 100% (6 hours) ✓

Result: Admin waits 6 hours, users get instant access
```

### On-Demand Generation  
```
TIME: Day 0
└─ Questions: 0 for all skills

TIME: Day 1 (5 users try Python)
├─ User 1: Wait 30s → 20 questions
├─ User 2: Instant → 40 questions  
├─ User 3: Instant → 60 questions
├─ User 4: Instant → 80 questions
└─ User 5: Instant → 100 questions ✓

TIME: Day 2 (10 users try JavaScript)
├─ User 1: Wait 30s → 20 questions
├─ Users 2-10: Instant access
└─ Growing to 100...

TIME: Week 1
└─ Popular skills: 60-100 questions
    Niche skills: 0-20 questions (perfectly matched to demand!)

Result: Zero admin time, questions match actual usage
```

## System States

```
SKILL STATE MACHINE:

[Empty]              [Building]           [Complete]
0 questions    →    1-99 questions    →   100 questions
│                    │                     │
├─ First user waits  ├─ Users get instant ├─ All users instant
├─ Generates 20      ├─ Grows by 20/user  ├─ No generation
└─ Moves to Building └─ Moves to Complete └─ Permanent state
```

## API Quota Management

```
FREE TIER LIMITS:
├─ Per Minute: 5 requests
│  └─ Generates: ~8 questions (template fallback)
│
└─ Per Day: 20 requests  
   └─ Generates: ~20 questions for 1 skill OR
                  ~8 questions for 3 skills OR
                  Template fallback for many skills

ON-DEMAND APPROACH:
├─ Spreads requests across days/weeks
├─ Only generates for skills users need
├─ No quota waste on unpopular skills
└─ Natural rate limiting through user activity
```

## Real-World Timeline

```
WEEK 1: Launch
├─ Monday: 10 users test platform
│  ├─ Python: 0 → 60 questions (6 users)
│  ├─ JavaScript: 0 → 40 questions (4 users)
│  └─ Other skills: 0 (no users = no waste!)
│
├─ Friday: 50 total users
│  ├─ Python: 100 questions ✓ COMPLETE
│  ├─ JavaScript: 80 questions (4 more users)
│  ├─ SQL: 40 questions (2 users)
│  └─ 20 other skills still at 0 (perfect!)

WEEK 2-4: Growth
├─ Popular skills reach 100 early
├─ Medium skills grow to 60-80
├─ Niche skills stay low (20-40)
└─ No wasted API calls!

MONTH 2+: Stable
├─ Top 10 skills: 100 questions each
├─ Medium 10 skills: 40-80 questions each
├─ Niche 5 skills: 0-20 questions each
└─ Total: ~1200 questions (vs 2500 if pre-generated all!)
```

## Benefits Summary

```
┌─────────────────────────────────────────────┐
│         ON-DEMAND GENERATION WINS           │
├─────────────────────────────────────────────┤
│ ✓ Zero setup time (vs 6 hours)             │
│ ✓ No rate limit errors (spread over time)   │
│ ✓ 50% less API usage (demand-driven)        │
│ ✓ 30s first wait (vs hours bulk generation) │
│ ✓ Natural quality feedback loop             │
│ ✓ Matches actual user demand                │
│ ✓ Works with free tier limits               │
│ ✓ Self-maintaining system                   │
└─────────────────────────────────────────────┘
```

---

**The beauty**: It just works! No configuration, no maintenance, no waiting. Launch and let user activity drive question generation naturally. 🚀
