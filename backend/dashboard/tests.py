from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User


class DashboardHomeTestCase(TestCase):
    """Tests for the main dashboard home view"""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='dashstudent',
            email='dashstudent@example.com',
            password='Pass123!',
            full_name='Dash Student',
            user_type='student',
            email_verified=True,
        )
        self.professional = User.objects.create_user(
            username='dashpro',
            email='dashpro@example.com',
            password='Pass123!',
            full_name='Dash Professional',
            user_type='professional',
            email_verified=True,
        )
        self.recruiter = User.objects.create_user(
            username='dashrec',
            email='dashrec@example.com',
            password='Pass123!',
            full_name='Dash Recruiter',
            user_type='recruiter',
            email_verified=True,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_student_can_access_dashboard(self):
        self.client.login(username='dashstudent', password='Pass123!')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)

    def test_professional_can_access_dashboard(self):
        self.client.login(username='dashpro', password='Pass123!')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)

    def test_recruiter_is_redirected_from_dashboard(self):
        self.client.login(username='dashrec', password='Pass123!')
        response = self.client.get(reverse('dashboard:home'))
        # Recruiter should be redirected to recruiter dashboard
        self.assertEqual(response.status_code, 302)

    def test_dashboard_context_contains_user(self):
        self.client.login(username='dashstudent', password='Pass123!')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.context['user'], self.student)

    def test_dashboard_context_contains_profile_completion(self):
        self.client.login(username='dashstudent', password='Pass123!')
        response = self.client.get(reverse('dashboard:home'))
        self.assertIn('profile_completion', response.context)


class ProfileViewTestCase(TestCase):
    """Tests for the profile view (dashboard/profile)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profiledash',
            email='profiledash@example.com',
            password='Pass123!',
            full_name='Profile Dash User',
            user_type='student',
            email_verified=True,
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('dashboard:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_returns_200_for_authenticated_user(self):
        self.client.login(username='profiledash', password='Pass123!')
        response = self.client.get(reverse('dashboard:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_post_updates_full_name(self):
        self.client.login(username='profiledash', password='Pass123!')
        response = self.client.post(reverse('dashboard:profile'), {
            'full_name': 'Updated Name',
            'phone_number': '1234567890',
            'user_type': 'student',
            'technical_skills': 'Python,Django',
            'soft_skills': 'Communication',
            'objective': 'To learn.',
            'linkedin_profile': '',
            'github_profile': '',
            'portfolio_website': '',
            'university': 'Test Uni',
            'degree': 'BSc CS',
            'work_experience_count': '0',
            'certification_count': '0',
            'project_count': '0',
            'internship_count': '0',
        })
        self.assertIn(response.status_code, [200, 302])
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')

    def test_profile_post_updates_technical_skills(self):
        self.client.login(username='profiledash', password='Pass123!')
        self.client.post(reverse('dashboard:profile'), {
            'full_name': 'Profile Dash User',
            'phone_number': '',
            'user_type': 'student',
            'technical_skills': 'Python,Django,React',
            'soft_skills': '',
            'objective': '',
            'linkedin_profile': '',
            'github_profile': '',
            'portfolio_website': '',
            'university': '',
            'degree': '',
            'work_experience_count': '0',
            'certification_count': '0',
            'project_count': '0',
            'internship_count': '0',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.technical_skills, 'Python,Django,React')

    def test_profile_context_contains_user(self):
        self.client.login(username='profiledash', password='Pass123!')
        response = self.client.get(reverse('dashboard:profile'))
        self.assertEqual(response.context['user'], self.user)

