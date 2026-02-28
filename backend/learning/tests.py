from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from assessments.models import SkillCategory, Skill, UserSkillScore
from learning.models import Course, SkillGap, LearningPath


class LearningDashboardTestCase(TestCase):
    """Tests for the learning dashboard view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='learner1',
            email='learner1@example.com',
            password='Pass123!',
            full_name='Learner One',
            user_type='student',
            email_verified=True,
        )

    def test_learning_dashboard_requires_login(self):
        response = self.client.get(reverse('learning:learning_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_learning_dashboard_returns_200(self):
        self.client.login(username='learner1', password='Pass123!')
        response = self.client.get(reverse('learning:learning_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_learning_dashboard_context_keys(self):
        self.client.login(username='learner1', password='Pass123!')
        response = self.client.get(reverse('learning:learning_dashboard'))
        self.assertIn('learning_paths', response.context)
        self.assertIn('user_skill_scores', response.context)
        self.assertIn('critical_gaps', response.context)


class SkillGapsViewTestCase(TestCase):
    """Tests for the skill gaps page"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='gapuser',
            email='gapuser@example.com',
            password='Pass123!',
            full_name='Gap User',
            user_type='student',
            email_verified=True,
        )
        self.category = SkillCategory.objects.create(
            name='Test Category',
            description='Testing',
        )
        self.skill = Skill.objects.create(
            category=self.category,
            name='Python',
            description='Python programming',
            is_active=True,
        )

    def test_skill_gaps_requires_login(self):
        response = self.client.get(reverse('learning:skill_gaps'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_skill_gaps_returns_200(self):
        self.client.login(username='gapuser', password='Pass123!')
        response = self.client.get(reverse('learning:skill_gaps'))
        self.assertEqual(response.status_code, 200)

    def test_skill_gaps_shows_user_gaps(self):
        SkillGap.objects.create(
            user=self.user,
            skill=self.skill,
            current_level=2.0,
            required_level=7.0,
            gap_value=5.0,
            gap_severity=0.71,
            priority='high',
        )
        self.client.login(username='gapuser', password='Pass123!')
        response = self.client.get(reverse('learning:skill_gaps'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('skill_gaps', response.context)


class CourseCatalogTestCase(TestCase):
    """Tests for the course catalog view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='cataloguser',
            email='cataloguser@example.com',
            password='Pass123!',
            full_name='Catalog User',
            user_type='student',
            email_verified=True,
        )
        self.category = SkillCategory.objects.create(
            name='Programming',
            description='Programming skills',
        )
        self.skill = Skill.objects.create(
            category=self.category,
            name='Django',
            description='Django framework',
            is_active=True,
        )

    def test_course_catalog_requires_login(self):
        response = self.client.get(reverse('learning:course_catalog'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_course_catalog_returns_200(self):
        self.client.login(username='cataloguser', password='Pass123!')
        response = self.client.get(reverse('learning:course_catalog'))
        self.assertEqual(response.status_code, 200)

    def test_course_catalog_shows_active_courses(self):
        Course.objects.create(
            title='Django for Beginners',
            description='Learn Django from scratch.',
            skill=self.skill,
            course_type='video',
            difficulty_level='beginner',
            platform='internal',
            url='https://example.com/django',
            is_active=True,
        )
        self.client.login(username='cataloguser', password='Pass123!')
        response = self.client.get(reverse('learning:course_catalog'))
        self.assertContains(response, 'Django for Beginners')


class MyCourseTestCase(TestCase):
    """Tests for my courses view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mycourseuser',
            email='mycourseuser@example.com',
            password='Pass123!',
            full_name='My Course User',
            user_type='student',
            email_verified=True,
        )

    def test_my_courses_requires_login(self):
        response = self.client.get(reverse('learning:my_courses'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_my_courses_returns_200(self):
        self.client.login(username='mycourseuser', password='Pass123!')
        response = self.client.get(reverse('learning:my_courses'))
        self.assertEqual(response.status_code, 200)


class SkillGapModelTestCase(TestCase):
    """Tests for the SkillGap model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='sgmodeluser',
            email='sgmodeluser@example.com',
            password='Pass123!',
        )
        self.category = SkillCategory.objects.create(name='Backend')
        self.skill = Skill.objects.create(
            category=self.category,
            name='Node.js',
            is_active=True,
        )

    def test_skill_gap_creation(self):
        """SkillGap save() auto-computes priority from gap_value and job_criticality.
        gap_value >= 4 → 'critical', so use gap_value=3 (required=5, current=2) for 'high'.
        With job_criticality=0 and gap_value=3: priority_score = (0.6*0.4)+(0*0.6)=0.24
        and gap_value >= 2 → 'high'."""
        gap = SkillGap.objects.create(
            user=self.user,
            skill=self.skill,
            current_level=2.0,
            required_level=5.0,
            job_criticality=0.0,
        )
        # With required=5, current=2: gap_value=3, gap_severity=0.6
        # priority_score = (0.6*0.4)+(0.0*0.6)=0.24; gap_value=3 (>=2) → 'high'
        self.assertEqual(gap.gap_value, 3.0)
        self.assertEqual(gap.priority, 'high')
        self.assertFalse(gap.is_addressed)

    def test_skill_gap_str(self):
        gap = SkillGap.objects.create(
            user=self.user,
            skill=self.skill,
            current_level=2.0,
            required_level=6.0,
            gap_value=4.0,
        )
        self.assertIn('Node.js', str(gap))


class LearningPathModelTestCase(TestCase):
    """Tests for the LearningPath model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='lpmodeluser',
            email='lpmodeluser@example.com',
            password='Pass123!',
        )
        self.category = SkillCategory.objects.create(name='Frontend')
        self.skill = Skill.objects.create(
            category=self.category,
            name='React',
            is_active=True,
        )
        self.gap = SkillGap.objects.create(
            user=self.user,
            skill=self.skill,
            current_level=1.0,
            required_level=7.0,
            gap_value=6.0,
        )

    def test_learning_path_creation(self):
        path = LearningPath.objects.create(
            user=self.user,
            skill_gap=self.gap,
            title='React Learning Path',
            description='Master React',
        )
        self.assertEqual(path.title, 'React Learning Path')
        self.assertEqual(path.user, self.user)

    def test_learning_path_str(self):
        path = LearningPath.objects.create(
            user=self.user,
            skill_gap=self.gap,
            title='React Path',
        )
        self.assertIn('React', str(path))

