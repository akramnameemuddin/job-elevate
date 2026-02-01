# Assessment Flow - Quick Reference

## 🔄 Complete User Journey

### 1. Job Seeker Views Job
**URL**: `/jobs/{job_id}/`
- See job details
- View required skills with proficiency levels
- See gap analysis showing missing/insufficient skills

### 2. Claim Skill
**Button**: "Claim Skill from Job"
- Redirects to: `/assessments/start/{skill_id}/?from_job={job_id}`
- Shows assessment instructions
- Displays: 20 questions, 40% easy, 30% medium, 30% hard
- Time limit and scoring rules

### 3. Take Assessment
**URL**: `/assessments/take/{attempt_id}/`
- Displays 20 multiple-choice questions
- Each question shows:
  - Question number
  - Difficulty badge (Easy/Medium/Hard)
  - Question text
  - 4 radio button options
- "Submit Assessment" button at bottom

### 4. View Results
**URL**: `/assessments/result/{attempt_id}/`
- Shows:
  - Score (e.g., 15/20)
  - Percentage (e.g., 75%)
  - Proficiency Level (e.g., 7.5/10)
  - Pass/Fail status
  - Individual question results
- "Return to Job" button if from job

### 5. Return to Job
- Gap analysis updated
- New proficiency score visible
- Match percentage recalculated

## 📊 Scoring System

### Points per Question
- Easy: 5 points
- Medium: 10 points  
- Hard: 15 points

### Maximum Score
8 easy × 5 = 40 points
6 medium × 10 = 60 points
6 hard × 15 = 90 points
**Total: 190 points**

### Proficiency Calculation
```python
percentage = (score / total) * 100
proficiency_level = round((percentage / 100) * 10, 1)
passed = percentage >= 60
```

### Pass Threshold
- Need: 60% or higher
- That's: 12+ correct answers out of 20
- Status: Updates UserSkillScore with proficiency

## 🗄️ Database Changes

### AssessmentAttempt Model
Stores each assessment attempt with:
- `user` - Who took it
- `skill` - Which skill
- `score` - Raw score (0-190)
- `total_score` - Same as score
- `proficiency_level` - 0-10 scale
- `passed` - Boolean (True if ≥60%)
- `selected_question_ids` - JSON of question IDs
- `shuffle_seed` - For reproducible order
- `created_at` - Timestamp

### UserSkillScore Model  
Updated after successful assessment:
- `proficiency_score` - Set to proficiency_level
- Triggers gap analysis recalculation
- Updates job match percentages

## 🔍 Gap Analysis Impact

### Before Assessment
```
Required: Python 8/10
User has: None
Gap: 8.0 points
```

### After Assessment (75% score)
```
Required: Python 8/10
User has: Python 7.5/10
Gap: 0.5 points
```

### Match Calculation
- Old match: 0%
- New match: 93.75% (7.5/8)
- Overall job match updated

## 🐛 Known Issues Fixed

1. ✅ Options not displaying → Fixed template syntax
2. ✅ NOT NULL constraint errors → Added missing fields
3. ✅ Insufficient questions → Added 229 questions
4. ✅ Wrong distribution → Changed to 8/6/6
5. ✅ Proficiency not calculating → Added calculation logic

## 🎯 Testing Checklist

- [ ] Create job with skill requirements
- [ ] View job as job seeker
- [ ] Click "Claim Skill from Job"
- [ ] Start assessment
- [ ] See 20 questions with proper distribution
- [ ] All options display correctly
- [ ] Submit assessment
- [ ] See correct score and proficiency
- [ ] Return to job
- [ ] Verify gap is reduced/closed
- [ ] Check UserSkillScore updated

## 📞 Key URLs

| Action | URL Pattern |
|--------|-------------|
| Job Detail | `/jobs/{job_id}/` |
| Start Assessment | `/assessments/start/{skill_id}/?from_job={job_id}` |
| Take Assessment | `/assessments/take/{attempt_id}/` |
| View Results | `/assessments/result/{attempt_id}/` |
| Recruiter Dashboard | `/recruiter/dashboard/` |
| Job Seeker Dashboard | `/dashboard/` |

## 💡 Tips

1. **For Testing**: Use Python, JavaScript, or AWS (all have 20 questions)
2. **Pass Rate**: Need 12+ correct (60%) to pass
3. **Proficiency Range**: 0-10 scale (10 = perfect score)
4. **Retakes**: Users can retake assessments
5. **Question Pool**: Randomly selected from 20 available per skill
