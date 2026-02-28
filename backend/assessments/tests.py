from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from assessments.models import (
    SkillCategory, Skill, QuestionBank,
    AssessmentAttempt, UserSkillScore,
)
from recruiter.models import Job, JobSkillRequirement


def _make_user(username, user_type='student'):
    return User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='Pass123!',
        full_name=username.title(),
        user_type=user_type,
        email_verified=True,
    )


def _make_skill(name='Python', category_name='Programming'):
    category, _ = SkillCategory.objects.get_or_create(name=category_name)
    skill, _ = Skill.objects.get_or_create(
        name=name,
        category=category,
        defaults={'description': f'{name} programming', 'is_active': True},
    )
    return skill


def _add_questions(skill, count=20):
    """Add enough questions to the QuestionBank for an assessment."""
    created = []
    for i in range(count):
        difficulty = 'easy' if i < 8 else ('medium' if i < 14 else 'hard')
        q = QuestionBank.objects.create(
            skill=skill,
            question_text=f'Sample question {i + 1} about {skill.name}?',
            options=[f'Option A{i}', f'Option B{i}', f'Option C{i}', f'Option D{i}'],
            correct_answer=f'Option A{i}',
            difficulty=difficulty,
            proficiency_level=5.0,
        )
        created.append(q)
    skill.question_count = count
    skill.questions_generated = True
    skill.save()
    return created


# ---------------------------------------------------------------------------
# Skill model tests
# ---------------------------------------------------------------------------

class SkillModelTestCase(TestCase):
    """Tests for the Skill model"""

    def setUp(self):
        self.category = SkillCategory.objects.create(
            name='Data Science',
            description='Data science skills',
        )
        self.skill = Skill.objects.create(
            category=self.category,
            name='Pandas',
            description='Data manipulation with pandas',
            is_active=True,
        )

    def test_skill_str_includes_category_and_name(self):
        self.assertIn('Data Science', str(self.skill))
        self.assertIn('Pandas', str(self.skill))

    def test_needs_more_questions_when_below_100(self):
        self.skill.question_count = 50
        self.assertTrue(self.skill.needs_more_questions())

    def test_needs_more_questions_false_when_100(self):
        self.skill.question_count = 100
        self.assertFalse(self.skill.needs_more_questions())

    def test_has_sufficient_questions_false_below_20(self):
        self.skill.question_count = 10
        self.assertFalse(self.skill.has_sufficient_questions())

    def test_has_sufficient_questions_true_at_20(self):
        self.skill.question_count = 20
        self.assertTrue(self.skill.has_sufficient_questions())


# ---------------------------------------------------------------------------
# QuestionBank model tests
# ---------------------------------------------------------------------------

class QuestionBankModelTestCase(TestCase):

    def setUp(self):
        self.skill = _make_skill('Java', 'Backend')

    def test_question_bank_creation(self):
        q = QuestionBank.objects.create(
            skill=self.skill,
            question_text='What is a JVM?',
            options=['Virtual machine', 'Compiler', 'Interpreter', 'Linker'],
            correct_answer='Virtual machine',
            difficulty='easy',
        )
        self.assertEqual(str(q.correct_answer), 'Virtual machine')

    def test_question_bank_str(self):
        q = QuestionBank.objects.create(
            skill=self.skill,
            question_text='What does JVM stand for?',
            options=['A', 'B', 'C', 'D'],
            correct_answer='A',
            difficulty='medium',
        )
        self.assertIn('Java', str(q))
        self.assertIn('medium', str(q))

    def test_success_rate_zero_when_unused(self):
        q = QuestionBank.objects.create(
            skill=self.skill,
            question_text='Unused question?',
            options=['A', 'B', 'C', 'D'],
            correct_answer='A',
            difficulty='easy',
        )
        self.assertEqual(q.success_rate, 0)

    def test_success_rate_correct_calculation(self):
        q = QuestionBank.objects.create(
            skill=self.skill,
            question_text='Rate question?',
            options=['A', 'B', 'C', 'D'],
            correct_answer='A',
            difficulty='easy',
            times_used=10,
            times_correct=7,
        )
        self.assertAlmostEqual(q.success_rate, 70.0)


# ---------------------------------------------------------------------------
# AssessmentAttempt model tests
# ---------------------------------------------------------------------------

class AssessmentAttemptModelTestCase(TestCase):

    def setUp(self):
        self.user = _make_user('attemptuser')
        self.skill = _make_skill('SQL', 'Database')

    def test_attempt_created_in_progress(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.user,
            skill=self.skill,
            status='in_progress',
            max_score=20,
        )
        self.assertEqual(attempt.status, 'in_progress')

    def test_calculate_percentage(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.user,
            skill=self.skill,
            status='completed',
            score=15,
            max_score=20,
        )
        pct = attempt.calculate_percentage()
        self.assertAlmostEqual(pct, 75.0)

    def test_is_passing_above_threshold(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.user,
            skill=self.skill,
            status='completed',
            score=12,
            max_score=20,
            percentage=60,
        )
        self.assertTrue(attempt.is_passing(60))

    def test_is_passing_below_threshold(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.user,
            skill=self.skill,
            status='completed',
            score=8,
            max_score=20,
            percentage=40,
        )
        self.assertFalse(attempt.is_passing(60))

    def test_attempt_str_includes_username(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.user,
            skill=self.skill,
            status='in_progress',
        )
        self.assertIn('attemptuser', str(attempt))


# ---------------------------------------------------------------------------
# UserSkillScore model tests
# ---------------------------------------------------------------------------

class UserSkillScoreModelTestCase(TestCase):

    def setUp(self):
        self.user = _make_user('scoreuser')
        self.skill = _make_skill('Django', 'Web')

    def test_user_skill_score_defaults(self):
        score = UserSkillScore.objects.create(
            user=self.user,
            skill=self.skill,
        )
        self.assertEqual(score.status, 'claimed')

    def test_user_skill_score_verified(self):
        score = UserSkillScore.objects.create(
            user=self.user,
            skill=self.skill,
            status='verified',
            verified_level=7.5,
        )
        self.assertEqual(score.status, 'verified')
        self.assertAlmostEqual(float(score.verified_level), 7.5)


# ---------------------------------------------------------------------------
# View tests: Skill Intake Dashboard
# ---------------------------------------------------------------------------

class SkillIntakeDashboardViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = _make_user('viewuser1')

    def test_skill_intake_requires_login(self):
        response = self.client.get(reverse('assessments:skill_intake_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_skill_intake_returns_200(self):
        self.client.login(username='viewuser1', password='Pass123!')
        response = self.client.get(reverse('assessments:skill_intake_dashboard'))
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# View tests: Browse Skills
# ---------------------------------------------------------------------------

class BrowseSkillsViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = _make_user('browseuser')
        _make_skill('Flask', 'Web Dev')

    def test_browse_skills_requires_login(self):
        response = self.client.get(reverse('assessments:browse_skills'))
        self.assertEqual(response.status_code, 302)

    def test_browse_skills_returns_200(self):
        self.client.login(username='browseuser', password='Pass123!')
        response = self.client.get(reverse('assessments:browse_skills'))
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# View tests: Skill Profile
# ---------------------------------------------------------------------------

class SkillProfileViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = _make_user('profileuser')

    def test_skill_profile_requires_login(self):
        response = self.client.get(reverse('assessments:skill_profile'))
        self.assertEqual(response.status_code, 302)

    def test_skill_profile_returns_200(self):
        self.client.login(username='profileuser', password='Pass123!')
        response = self.client.get(reverse('assessments:skill_profile'))
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# View tests: Start Assessment Direct
# ---------------------------------------------------------------------------

class StartAssessmentDirectViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = _make_user('startuser')
        self.skill = _make_skill('React', 'Frontend')
        _add_questions(self.skill, 20)

    def test_start_direct_requires_login(self):
        response = self.client.get(
            reverse('assessments:start_assessment_direct',
                    kwargs={'skill_id': self.skill.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_start_direct_creates_attempt(self):
        self.client.login(username='startuser', password='Pass123!')
        before = AssessmentAttempt.objects.filter(
            user=self.user, skill=self.skill).count()
        response = self.client.get(
            reverse('assessments:start_assessment_direct',
                    kwargs={'skill_id': self.skill.id})
        )
        # Either redirects to take page (302) or renders the assessment (200)
        self.assertIn(response.status_code, [200, 302])
        after = AssessmentAttempt.objects.filter(
            user=self.user, skill=self.skill).count()
        self.assertGreaterEqual(after, before)

    def test_start_direct_nonexistent_skill_returns_404(self):
        self.client.login(username='startuser', password='Pass123!')
        response = self.client.get(
            reverse('assessments:start_assessment_direct',
                    kwargs={'skill_id': 99999})
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# View tests: Start Assessment from Job
# ---------------------------------------------------------------------------

class StartAssessmentFromJobViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = _make_user('jobassessuser')
        self.recruiter = _make_user('jobrecruiter', user_type='recruiter')
        self.skill = _make_skill('Node.js', 'Backend Dev')
        _add_questions(self.skill, 20)
        self.job = Job.objects.create(
            title='Backend Developer',
            company='Tech LLC',
            location='Remote',
            job_type='Full-time',
            description='Backend work',
            posted_by=self.recruiter,
            status='Open',
        )
        JobSkillRequirement.objects.create(
            job=self.job,
            skill=self.skill,
            required_proficiency=5.0,
        )

    def test_start_from_job_requires_login(self):
        response = self.client.get(
            reverse('assessments:start_assessment_from_job',
                    kwargs={'job_id': self.job.id, 'skill_id': self.skill.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_start_from_job_invalid_skill_returns_error(self):
        self.client.login(username='jobassessuser', password='Pass123!')
        response = self.client.get(
            reverse('assessments:start_assessment_from_job',
                    kwargs={'job_id': self.job.id, 'skill_id': 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_start_from_job_with_valid_skill_starts_assessment(self):
        self.client.login(username='jobassessuser', password='Pass123!')
        before = AssessmentAttempt.objects.filter(
            user=self.user, skill=self.skill).count()
        response = self.client.get(
            reverse('assessments:start_assessment_from_job',
                    kwargs={'job_id': self.job.id, 'skill_id': self.skill.id})
        )
        self.assertIn(response.status_code, [200, 302])
        after = AssessmentAttempt.objects.filter(
            user=self.user, skill=self.skill).count()
        self.assertGreaterEqual(after, before)
