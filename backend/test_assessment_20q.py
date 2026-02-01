"""
Test script to verify 20-question assessments work correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from assessments.models import QuestionBank, Skill

def test_question_availability():
    """Check if we have enough questions for 20-question assessments"""
    print("=" * 60)
    print("TESTING ASSESSMENT SYSTEM - 20 QUESTIONS")
    print("=" * 60)
    
    # Check main skills
    skills_to_check = ['Python', 'JavaScript', 'Java', 'SQL', 'Git', 'aws', 'docker', 'Data Analysis', 'Machine Learning']
    
    print("\n1. CHECKING QUESTION AVAILABILITY:")
    print("-" * 60)
    
    all_good = True
    for skill_name in skills_to_check:
        # Try to find the skill
        skill_query = Skill.objects.filter(name__icontains=skill_name)
        if not skill_query.exists():
            print(f"⚠️  {skill_name}: Skill not found in database")
            continue
            
        skill = skill_query.first()
        
        # Count questions by difficulty
        easy = QuestionBank.objects.filter(skill=skill, difficulty='easy').count()
        medium = QuestionBank.objects.filter(skill=skill, difficulty='medium').count()
        hard = QuestionBank.objects.filter(skill=skill, difficulty='hard').count()
        total = easy + medium + hard
        
        # Check if we have enough (8 easy, 6 medium, 6 hard = 20 total)
        has_enough = easy >= 8 and medium >= 6 and hard >= 6
        status = "✓" if has_enough else "✗"
        
        print(f"{status} {skill.name:25} | Easy: {easy:2}/8 | Medium: {medium:2}/6 | Hard: {hard:2}/6 | Total: {total:3}")
        
        if not has_enough:
            all_good = False
    
    print("-" * 60)
    
    if all_good:
        print("\n✓ ALL SKILLS HAVE SUFFICIENT QUESTIONS!")
    else:
        print("\n✗ Some skills need more questions")
    
    print("\n2. TESTING QUESTION SELECTION LOGIC:")
    print("-" * 60)
    
    # Test the selection logic from views.py
    from assessments.views import _select_balanced_questions
    
    test_skills = ['Python', 'aws', 'docker']
    for skill_name in test_skills:
        skill_query = Skill.objects.filter(name__icontains=skill_name)
        if skill_query.exists():
            skill = skill_query.first()
            questions_queryset = QuestionBank.objects.filter(skill=skill)
            questions = _select_balanced_questions(questions_queryset)
            
            if questions:
                easy_count = sum(1 for q in questions if q.difficulty == 'easy')
                medium_count = sum(1 for q in questions if q.difficulty == 'medium')
                hard_count = sum(1 for q in questions if q.difficulty == 'hard')
                
                expected = (easy_count == 8 and medium_count == 6 and hard_count == 6)
                status = "✓" if expected else "✗"
                
                print(f"{status} {skill.name:25} | Selected: Easy={easy_count}, Medium={medium_count}, Hard={hard_count}, Total={len(questions)}")
            else:
                print(f"✗ {skill.name:25} | No questions returned!")
    
    print("-" * 60)
    
    print("\n3. PROFICIENCY CALCULATION TEST:")
    print("-" * 60)
    
    # Test proficiency calculation
    test_scores = [
        (20, 20),  # 100%
        (15, 20),  # 75%
        (12, 20),  # 60%
        (10, 20),  # 50%
    ]
    
    for score, total in test_scores:
        percentage = (score / total) * 100
        proficiency = round((percentage / 100) * 10, 1)
        passed = percentage >= 60
        status = "PASSED" if passed else "FAILED"
        print(f"Score: {score:2}/{total} ({percentage:5.1f}%) → Proficiency: {proficiency:3.1f}/10 [{status}]")
    
    print("-" * 60)
    
    print("\n4. TOTAL QUESTION COUNT:")
    print("-" * 60)
    total_questions = QuestionBank.objects.count()
    print(f"Total questions in database: {total_questions}")
    print("-" * 60)
    
    print("\n✓ ASSESSMENT SYSTEM TEST COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    test_question_availability()
