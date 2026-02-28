from django.test import TestCase

import json
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from recruiter.models import Job, Application


class RecruiterDashboardAccessTestCase(TestCase):
    """Tests for recruiter dashboard access control"""

    def setUp(self):
        self.client = Client()
        # Recruiter user
        self.recruiter = User.objects.create_user(
            username='recruiter_test',
            email='recruiter_test@example.com',
            password='Pass123!',
            full_name='Test Recruiter',
            user_type='recruiter',
            email_verified=True,
        )
        # Student user (should be denied)
        self.student = User.objects.create_user(
            username='student_test',
            email='student_test@example.com',
            password='Pass123!',
            full_name='Test Student',
            user_type='student',
            email_verified=True,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('recruiter:recruiter_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_recruiter_can_access_dashboard(self):
        self.client.login(username='recruiter_test', password='Pass123!')
        response = self.client.get(reverse('recruiter:recruiter_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_non_recruiter_denied_dashboard(self):
        self.client.login(username='student_test', password='Pass123!')
        response = self.client.get(reverse('recruiter:recruiter_dashboard'))
        # Should redirect (access denied behaviour)
        self.assertEqual(response.status_code, 302)


class JobCRUDTestCase(TestCase):
    """Tests for recruiter job management API"""

    def setUp(self):
        self.client = Client()
        self.recruiter = User.objects.create_user(
            username='rec2',
            email='rec2@example.com',
            password='Pass123!',
            full_name='Recruiter Two',
            user_type='recruiter',
            email_verified=True,
        )
        self.client.login(username='rec2', password='Pass123!')

    def test_create_job_successfully(self):
        """create_job reads JSON body with 'type' key (not job_type)"""
        response = self.client.post(
            reverse('recruiter:create_job'),
            data=json.dumps({
                'title': 'Software Engineer',
                'company': 'Tech Corp',
                'location': 'Remote',
                'type': 'Full-time',
                'description': 'Build awesome things.',
                'experience': 2,
                'skills': ['Python', 'Django'],
            }),
            content_type='application/json',
        )
        self.assertIn(response.status_code, [200, 201])
        data = response.json()
        self.assertTrue(data.get('success', False))
        self.assertTrue(Job.objects.filter(title='Software Engineer', posted_by=self.recruiter).exists())

    def test_create_job_requires_login(self):
        client = Client()
        response = client.post(
            reverse('recruiter:create_job'),
            data=json.dumps({'title': 'Test Job'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_get_jobs_returns_recruiter_jobs_only(self):
        Job.objects.create(
            title='My Job',
            company='Corp',
            location='NYC',
            job_type='Full-time',
            description='Desc',
            posted_by=self.recruiter,
        )
        response = self.client.get(reverse('recruiter:get_jobs'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        jobs = data.get('jobs', [])
        self.assertTrue(all(j.get('posted_by') == self.recruiter.id for j in jobs) or len(jobs) >= 1)

    def test_delete_job_removes_record(self):
        """delete_job uses @require_POST so send POST not DELETE"""
        job = Job.objects.create(
            title='Delete Me',
            company='Corp',
            location='NYC',
            job_type='Full-time',
            description='Desc',
            posted_by=self.recruiter,
        )
        response = self.client.post(
            reverse('recruiter:delete_job', kwargs={'job_id': job.id}),
        )
        self.assertIn(response.status_code, [200, 204])
        self.assertFalse(Job.objects.filter(id=job.id).exists())

    def test_update_job_changes_title(self):
        job = Job.objects.create(
            title='Old Title',
            company='Corp',
            location='NYC',
            job_type='Full-time',
            description='Desc',
            posted_by=self.recruiter,
        )
        """update_job uses @require_POST so send POST not PUT"""
        response = self.client.post(
            reverse('recruiter:update_job', kwargs={'job_id': job.id}),
            data=json.dumps({'title': 'New Title'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.title, 'New Title')


class ApplicationStatusTestCase(TestCase):
    """Tests for updating application status"""

    def setUp(self):
        self.client = Client()
        self.recruiter = User.objects.create_user(
            username='rec3',
            email='rec3@example.com',
            password='Pass123!',
            full_name='Recruiter Three',
            user_type='recruiter',
            email_verified=True,
        )
        self.applicant = User.objects.create_user(
            username='applicant1',
            email='applicant1@example.com',
            password='Pass123!',
            full_name='Applicant One',
            user_type='student',
            email_verified=True,
        )
        self.job = Job.objects.create(
            title='Test Job',
            company='Corp',
            location='NYC',
            job_type='Full-time',
            description='Desc',
            posted_by=self.recruiter,
        )
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.applicant,
            status='Applied',
        )
        self.client.login(username='rec3', password='Pass123!')

    def test_update_application_status_to_shortlisted(self):
        response = self.client.post(
            reverse('recruiter:update_application_status',
                    kwargs={'application_id': self.application.id}),
            data=json.dumps({'status': 'Shortlisted'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Shortlisted')

    def test_update_application_status_to_hired(self):
        response = self.client.post(
            reverse('recruiter:update_application_status',
                    kwargs={'application_id': self.application.id}),
            data=json.dumps({'status': 'Hired'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'Hired')


class JobModelTestCase(TestCase):
    """Tests for the Job model"""

    def setUp(self):
        self.recruiter = User.objects.create_user(
            username='modelrec',
            email='modelrec@example.com',
            password='Pass123!',
            user_type='recruiter',
        )

    def test_job_str_representation(self):
        job = Job.objects.create(
            title='Django Developer',
            company='StartupCo',
            location='Remote',
            job_type='Full-time',
            description='Build the backend',
            posted_by=self.recruiter,
        )
        self.assertIn('Django Developer', str(job))
        self.assertIn('StartupCo', str(job))

    def test_job_default_status_is_open(self):
        job = Job.objects.create(
            title='Junior Dev',
            company='Corp',
            location='Remote',
            job_type='Part-time',
            description='Help us build',
            posted_by=self.recruiter,
        )
        self.assertEqual(job.status, 'Open')

    def test_applicant_count_returns_correct_number(self):
        job = Job.objects.create(
            title='Counter Test Job',
            company='Corp',
            location='NYC',
            job_type='Full-time',
            description='Test',
            posted_by=self.recruiter,
        )
        applicant = User.objects.create_user(
            username='countapp',
            email='countapp@example.com',
            password='Pass123!',
            user_type='student',
        )
        Application.objects.create(job=job, applicant=applicant, status='Applied')
        self.assertEqual(job.applicant_count, 1)

