from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from accounts.models import User


class HomeViewTestCase(TestCase):
    """Tests for the home/landing page"""

    def setUp(self):
        self.client = Client()

    def test_home_page_returns_200(self):
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_correct_template(self):
        response = self.client.get(reverse('accounts:home'))
        self.assertTemplateUsed(response, 'accounts/index.html')


class SignupViewTestCase(TestCase):
    """Tests for the signup view"""

    def setUp(self):
        self.client = Client()

    def test_signup_page_returns_200(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)

    def test_signup_page_uses_correct_template(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertTemplateUsed(response, 'accounts/signup.html')

    def test_signup_step1_missing_fields_returns_error(self):
        """Step 1 with empty data should return JSON error"""
        response = self.client.post(
            reverse('accounts:signup'),
            data={'step': '1', 'email': '', 'password': '', 'username': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('success', True))

    def test_signup_step1_mismatched_passwords_returns_error(self):
        response = self.client.post(
            reverse('accounts:signup'),
            data={
                'step': '1',
                'full_name': 'Test User',
                'username': 'testuser_new',
                'email': 'new@example.com',
                'password': 'Password123!',
                'confirm_password': 'DifferentPassword!',
                'user_type': 'student',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('success', True))

    def test_signup_step2_without_session_data_returns_error(self):
        """Step 2 with no session signup data should fail"""
        response = self.client.post(
            reverse('accounts:signup'),
            data={'step': '2', 'otp': '123456'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('success', True))


class LoginViewTestCase(TestCase):
    """Tests for the login view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logintest',
            email='logintest@example.com',
            password='SecurePass123!',
            full_name='Login Test User',
            user_type='student',
            email_verified=True,
        )

    def test_login_page_returns_200(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_uses_correct_template(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_with_valid_credentials_redirects(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'logintest@example.com',
            'password': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/', response.url)

    def test_login_with_wrong_password_shows_error(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'logintest@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('Invalid' in m or 'invalid' in m for m in msgs))

    def test_login_with_nonexistent_email_shows_error(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'nobody@nowhere.com',
            'password': 'any',
        })
        self.assertEqual(response.status_code, 200)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('Invalid' in m or 'invalid' in m for m in msgs))

    def test_login_with_unverified_email_shows_error(self):
        unverified = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='Pass123!',
            full_name='Unverified',
            user_type='student',
            email_verified=False,
        )
        response = self.client.post(reverse('accounts:login'), {
            'email': 'unverified@example.com',
            'password': 'Pass123!',
        })
        self.assertEqual(response.status_code, 200)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('verify' in m.lower() for m in msgs))

    def test_login_missing_fields_shows_error(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': '',
            'password': '',
        })
        self.assertEqual(response.status_code, 200)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(len(msgs) > 0)

    def test_recruiter_login_redirects_to_recruiter_dashboard(self):
        recruiter = User.objects.create_user(
            username='recruiter1',
            email='recruiter1@example.com',
            password='Pass123!',
            full_name='Recruiter One',
            user_type='recruiter',
            email_verified=True,
        )
        response = self.client.post(reverse('accounts:login'), {
            'email': 'recruiter1@example.com',
            'password': 'Pass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('recruiter', response.url)


class LogoutViewTestCase(TestCase):
    """Tests for the logout view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logouttest',
            email='logouttest@example.com',
            password='Pass123!',
            full_name='Logout Test',
            user_type='student',
            email_verified=True,
        )

    def test_logout_redirects(self):
        self.client.login(username='logouttest', password='Pass123!')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_after_logout_user_is_unauthenticated(self):
        self.client.login(username='logouttest', password='Pass123!')
        self.client.get(reverse('accounts:logout'))
        # Profile should now require login
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class ProfileViewTestCase(TestCase):
    """Tests for the profile view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profiletest',
            email='profiletest@example.com',
            password='Pass123!',
            full_name='Profile Test',
            user_type='student',
            email_verified=True,
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_redirects_or_renders_when_authenticated(self):
        """accounts:profile either renders or redirects - just check no crash"""
        self.client.login(username='profiletest', password='Pass123!')
        response = self.client.get(reverse('accounts:profile'))
        # Either a success page or redirect (but not server error)
        self.assertIn(response.status_code, [200, 301, 302])


class UserModelTestCase(TestCase):
    """Tests for the User model"""

    def test_create_student_user(self):
        user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='Pass123!',
            user_type='student',
        )
        self.assertEqual(user.user_type, 'student')
        self.assertTrue(user.check_password('Pass123!'))

    def test_create_recruiter_user(self):
        user = User.objects.create_user(
            username='recruiter2',
            email='recruiter2@example.com',
            password='Pass123!',
            user_type='recruiter',
        )
        self.assertEqual(user.user_type, 'recruiter')

    def test_get_skills_list_returns_list(self):
        user = User.objects.create_user(
            username='skillstest',
            email='skillstest@example.com',
            password='Pass123!',
        )
        user.technical_skills = 'Python,Django,React'
        user.save()
        skills = user.get_skills_list()
        self.assertIsInstance(skills, list)
        self.assertIn('Python', skills)

    def test_email_verified_default_false(self):
        user = User.objects.create_user(
            username='unver2',
            email='unver2@example.com',
            password='Pass123!',
        )
        self.assertFalse(user.email_verified)

