from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from .models import Resume, ResumeTemplate

User = get_user_model()


class ResumeDeleteTestCase(TestCase):
    """Test cases for resume delete functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            full_name='Test User One'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            full_name='Test User Two'
        )

        # Create a test template
        self.template = ResumeTemplate.objects.create(
            name='Test Template',
            description='A test template',
            html_structure='<div>Test HTML</div>',
            css_structure='body { color: black; }',
            is_active=True
        )

        # Create test resumes
        self.resume1 = Resume.objects.create(
            user=self.user1,
            template=self.template,
            title='Test Resume 1',
            status='draft'
        )

        self.resume2 = Resume.objects.create(
            user=self.user1,
            template=self.template,
            title='Test Resume 2 (Edited)',
            status='published'
        )

        self.resume3 = Resume.objects.create(
            user=self.user2,
            template=self.template,
            title='Other User Resume',
            status='draft'
        )

        self.client = Client()

    def test_delete_own_resume_success(self):
        """Test that a user can delete their own resume"""
        self.client.login(username='testuser1', password='testpass123')

        # Verify resume exists
        self.assertTrue(Resume.objects.filter(id=self.resume1.id).exists())

        # Delete the resume
        response = self.client.post(
            reverse('resume_builder:delete_resume', args=[self.resume1.id])
        )

        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('resume_builder:resume_builder'))

        # Verify resume is deleted
        self.assertFalse(Resume.objects.filter(id=self.resume1.id).exists())

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('deleted successfully' in str(m) for m in messages))

    def test_delete_edited_resume_success(self):
        """Test that edited resumes can be deleted (the main issue being fixed)"""
        self.client.login(username='testuser1', password='testpass123')

        # Simulate editing the resume (update timestamp)
        self.resume2.title = 'Updated Resume Title'
        self.resume2.save()

        # Verify resume exists
        self.assertTrue(Resume.objects.filter(id=self.resume2.id).exists())

        # Delete the edited resume
        response = self.client.post(
            reverse('resume_builder:delete_resume', args=[self.resume2.id])
        )

        # Check redirect
        self.assertEqual(response.status_code, 302)

        # Verify resume is deleted
        self.assertFalse(Resume.objects.filter(id=self.resume2.id).exists())

    def test_cannot_delete_other_user_resume(self):
        """Test that a user cannot delete another user's resume"""
        self.client.login(username='testuser1', password='testpass123')

        # Try to delete another user's resume
        response = self.client.post(
            reverse('resume_builder:delete_resume', args=[self.resume3.id])
        )

        # Should return 404 (get_object_or_404 with user filter)
        self.assertEqual(response.status_code, 404)

        # Verify resume still exists
        self.assertTrue(Resume.objects.filter(id=self.resume3.id).exists())

    def test_delete_nonexistent_resume(self):
        """Test deleting a non-existent resume"""
        self.client.login(username='testuser1', password='testpass123')

        # Try to delete non-existent resume
        response = self.client.post(
            reverse('resume_builder:delete_resume', args=[99999])
        )

        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_delete_requires_login(self):
        """Test that delete requires authentication"""
        # Try to delete without login
        response = self.client.post(
            reverse('resume_builder:delete_resume', args=[self.resume1.id])
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        # Verify resume still exists
        self.assertTrue(Resume.objects.filter(id=self.resume1.id).exists())

    def test_delete_get_request_redirects(self):
        """Test that GET requests to delete URL redirect without deleting"""
        self.client.login(username='testuser1', password='testpass123')

        # Try GET request (should not delete)
        response = self.client.get(
            reverse('resume_builder:delete_resume', args=[self.resume1.id])
        )

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Verify resume still exists
        self.assertTrue(Resume.objects.filter(id=self.resume1.id).exists())


class ResumeDashboardTestCase(TestCase):
    """Test cases for resume dashboard functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )

        self.template = ResumeTemplate.objects.create(
            name='Test Template',
            description='A test template',
            html_structure='<div>Test HTML</div>',
            css_structure='body { color: black; }',
            is_active=True
        )

        self.client = Client()

    def test_dashboard_shows_delete_buttons(self):
        """Test that delete buttons are properly rendered with data attributes"""
        # Create a resume
        resume = Resume.objects.create(
            user=self.user,
            template=self.template,
            title='Test Resume',
            status='draft'
        )

        self.client.login(username='testuser', password='testpass123')

        # Get dashboard page
        response = self.client.get(reverse('resume_builder:resume_builder'))

        # Check that delete button is present with correct attributes
        self.assertContains(response, f'data-resume-id="{resume.id}"')
        self.assertContains(response, 'btn-outline-danger')
        self.assertContains(response, 'Delete')

    def test_dashboard_shows_delete_modal(self):
        """Test that delete modal is present in the dashboard"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('resume_builder:resume_builder'))

        # Check that modal elements are present
        self.assertContains(response, 'delete-resume-modal')
        self.assertContains(response, 'delete-resume-form')
        self.assertContains(response, 'Are you sure you want to delete this resume?')
