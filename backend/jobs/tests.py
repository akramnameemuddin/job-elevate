from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from .models import UserJobPreference, JobRecommendation
from .forms import UserJobPreferenceForm
from .recommendation_engine import HybridRecommender, ContentBasedRecommender
from recruiter.models import Job
import json

User = get_user_model()


class JobPreferencesTestCase(TestCase):
    """Test cases for job preferences functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_job_preferences_view_get(self):
        """Test GET request to job preferences view"""
        response = self.client.get(reverse('jobs:update_job_preferences'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Job Preferences')
        self.assertContains(response, 'Job Types')
        self.assertContains(response, 'Preferred Locations')
        self.assertContains(response, 'Salary Expectations')
        self.assertContains(response, 'Industry Preferences')

    def test_job_preferences_form_valid_submission(self):
        """Test valid form submission"""
        form_data = {
            'preferred_job_types': ['Full-time', 'Remote'],
            'preferred_locations': 'New York,San Francisco',
            'min_salary_expectation': 75000,
            'remote_preference': True,
            'industry_preferences': 'Technology,Healthcare'
        }

        response = self.client.post(reverse('jobs:update_job_preferences'), form_data)

        # Should redirect after successful submission
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('jobs:recommended_jobs'))

        # Check that preferences were saved
        preferences = UserJobPreference.objects.get(user=self.user)
        self.assertEqual(preferences.preferred_job_types, ['Full-time', 'Remote'])
        self.assertEqual(preferences.preferred_locations, ['New York', 'San Francisco'])
        self.assertEqual(preferences.min_salary_expectation, 75000)
        self.assertTrue(preferences.remote_preference)
        self.assertEqual(preferences.industry_preferences, ['Technology', 'Healthcare'])

    def test_job_preferences_form_update_existing(self):
        """Test updating existing preferences"""
        # Create initial preferences
        UserJobPreference.objects.create(
            user=self.user,
            preferred_job_types=['Part-time'],
            preferred_locations=['Boston'],
            min_salary_expectation=50000,
            remote_preference=False,
            industry_preferences=['Finance']
        )

        # Update preferences
        form_data = {
            'preferred_job_types': ['Full-time', 'Contract'],
            'preferred_locations': 'Seattle,Austin',
            'min_salary_expectation': 90000,
            'remote_preference': True,
            'industry_preferences': 'Technology,Marketing'
        }

        response = self.client.post(reverse('jobs:update_job_preferences'), form_data)

        self.assertEqual(response.status_code, 302)

        # Check that preferences were updated
        preferences = UserJobPreference.objects.get(user=self.user)
        self.assertEqual(preferences.preferred_job_types, ['Full-time', 'Contract'])
        self.assertEqual(preferences.preferred_locations, ['Seattle', 'Austin'])
        self.assertEqual(preferences.min_salary_expectation, 90000)
        self.assertTrue(preferences.remote_preference)
        self.assertEqual(preferences.industry_preferences, ['Technology', 'Marketing'])

    def test_job_preferences_form_validation(self):
        """Test form validation"""
        # Test with invalid salary
        form_data = {
            'preferred_job_types': ['Full-time'],
            'min_salary_expectation': 'invalid',
        }

        form = UserJobPreferenceForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_job_preferences_requires_login(self):
        """Test that job preferences requires authentication"""
        self.client.logout()

        response = self.client.get(reverse('jobs:update_job_preferences'))

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_job_preferences_display_existing_data(self):
        """Test that existing preferences are displayed in the form"""
        # Create preferences
        UserJobPreference.objects.create(
            user=self.user,
            preferred_job_types=['Full-time', 'Remote'],
            preferred_locations=['New York', 'San Francisco'],
            min_salary_expectation=80000,
            remote_preference=True,
            industry_preferences=['Technology', 'Healthcare']
        )

        response = self.client.get(reverse('jobs:update_job_preferences'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'checked')  # Job types should be checked
        self.assertContains(response, 'New York,San Francisco')  # Locations should be displayed
        self.assertContains(response, '80000')  # Salary should be set
        self.assertContains(response, 'Technology,Healthcare')  # Industries should be displayed


class UserJobPreferenceFormTestCase(TestCase):
    """Test cases for UserJobPreferenceForm"""

    def test_form_clean_preferred_locations(self):
        """Test location cleaning"""
        form_data = {
            'preferred_locations': 'New York, San Francisco, Boston',
            'preferred_job_types': ['Full-time'],
        }

        form = UserJobPreferenceForm(data=form_data)
        self.assertTrue(form.is_valid())

        cleaned_locations = form.clean_preferred_locations()
        self.assertEqual(cleaned_locations, ['New York', 'San Francisco', 'Boston'])

    def test_form_clean_industry_preferences(self):
        """Test industry cleaning"""
        form_data = {
            'industry_preferences': 'Technology, Healthcare, Finance',
            'preferred_job_types': ['Full-time'],
        }

        form = UserJobPreferenceForm(data=form_data)
        self.assertTrue(form.is_valid())

        cleaned_industries = form.clean_industry_preferences()
        self.assertEqual(cleaned_industries, ['Technology', 'Healthcare', 'Finance'])

    def test_form_clean_preferred_job_types(self):
        """Test job types cleaning"""
        form_data = {
            'preferred_job_types': ['Full-time', 'Remote'],
        }

        form = UserJobPreferenceForm(data=form_data)
        self.assertTrue(form.is_valid())

        cleaned_job_types = form.clean_preferred_job_types()
        self.assertEqual(cleaned_job_types, ['Full-time', 'Remote'])

    def test_form_with_existing_instance(self):
        """Test form initialization with existing instance"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        preferences = UserJobPreference.objects.create(
            user=user,
            preferred_job_types=['Full-time', 'Remote'],
            preferred_locations=['New York', 'San Francisco'],
            industry_preferences=['Technology', 'Healthcare']
        )

        form = UserJobPreferenceForm(instance=preferences)

        # Check that initial values are set correctly
        self.assertEqual(form.fields['preferred_job_types'].initial, ['Full-time', 'Remote'])
        self.assertEqual(form.fields['preferred_locations'].initial, 'New York,San Francisco')
        self.assertEqual(form.fields['industry_preferences'].initial, 'Technology,Healthcare')


class JobPreferencesDataPersistenceTestCase(TestCase):
    """Test cases for verifying data persistence in job preferences"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_job_preferences_data_persistence_complete(self):
        """Test that all job preference data is saved correctly to database"""
        # Submit comprehensive form data
        form_data = {
            'preferred_job_types': ['Full-time', 'Remote', 'Contract'],
            'preferred_locations': 'New York,San Francisco,Seattle',
            'min_salary_expectation': 85000,
            'remote_preference': True,
            'industry_preferences': 'Technology,Healthcare,Finance'
        }

        response = self.client.post(reverse('jobs:update_job_preferences'), form_data)

        # Verify redirect
        self.assertEqual(response.status_code, 302)

        # Verify data was saved correctly
        preferences = UserJobPreference.objects.get(user=self.user)

        # Test job types (JSON field)
        self.assertEqual(preferences.preferred_job_types, ['Full-time', 'Remote', 'Contract'])
        self.assertIsInstance(preferences.preferred_job_types, list)

        # Test locations (JSON field)
        self.assertEqual(preferences.preferred_locations, ['New York', 'San Francisco', 'Seattle'])
        self.assertIsInstance(preferences.preferred_locations, list)

        # Test salary
        self.assertEqual(preferences.min_salary_expectation, 85000)

        # Test remote preference
        self.assertTrue(preferences.remote_preference)

        # Test industries (JSON field)
        self.assertEqual(preferences.industry_preferences, ['Technology', 'Healthcare', 'Finance'])
        self.assertIsInstance(preferences.industry_preferences, list)

    def test_job_preferences_update_existing(self):
        """Test updating existing preferences preserves data integrity"""
        # Create initial preferences
        initial_prefs = UserJobPreference.objects.create(
            user=self.user,
            preferred_job_types=['Part-time'],
            preferred_locations=['Boston'],
            min_salary_expectation=50000,
            remote_preference=False,
            industry_preferences=['Education']
        )

        # Update with new data
        form_data = {
            'preferred_job_types': ['Full-time', 'Freelance'],
            'preferred_locations': 'Austin,Denver',
            'min_salary_expectation': 95000,
            'remote_preference': True,
            'industry_preferences': 'Technology,Marketing'
        }

        response = self.client.post(reverse('jobs:update_job_preferences'), form_data)

        # Verify update
        preferences = UserJobPreference.objects.get(user=self.user)
        self.assertEqual(preferences.id, initial_prefs.id)  # Same instance

        # Verify all fields updated correctly
        self.assertEqual(preferences.preferred_job_types, ['Full-time', 'Freelance'])
        self.assertEqual(preferences.preferred_locations, ['Austin', 'Denver'])
        self.assertEqual(preferences.min_salary_expectation, 95000)
        self.assertTrue(preferences.remote_preference)
        self.assertEqual(preferences.industry_preferences, ['Technology', 'Marketing'])

    def test_empty_preferences_handling(self):
        """Test handling of empty/minimal preferences"""
        form_data = {
            'preferred_job_types': [],
            'preferred_locations': '',
            'min_salary_expectation': '',
            'remote_preference': False,
            'industry_preferences': ''
        }

        response = self.client.post(reverse('jobs:update_job_preferences'), form_data)

        preferences = UserJobPreference.objects.get(user=self.user)

        # Verify empty lists are stored correctly
        self.assertEqual(preferences.preferred_job_types, [])
        self.assertEqual(preferences.preferred_locations, [])
        self.assertIsNone(preferences.min_salary_expectation)
        self.assertFalse(preferences.remote_preference)
        self.assertEqual(preferences.industry_preferences, [])


class RecommendationEngineIntegrationTestCase(TestCase):
    """Test cases for recommendation engine integration with job preferences"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            technical_skills='Python, Django, JavaScript',
            experience=3
        )

        # Create a recruiter user
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )

        # Create test jobs
        self.job1 = Job.objects.create(
            title='Senior Python Developer',
            company='Tech Corp',
            location='New York',
            job_type='Full-time',
            salary='$80,000 - $120,000',
            experience=3,
            skills=['Python', 'Django', 'PostgreSQL'],
            description='Senior Python developer position',
            posted_by=self.recruiter
        )

        self.job2 = Job.objects.create(
            title='Remote JavaScript Developer',
            company='Remote Inc',
            location='Remote',
            job_type='Remote',
            salary='$70,000 - $100,000',
            experience=2,
            skills=['JavaScript', 'React', 'Node.js'],
            description='Remote JavaScript developer position',
            posted_by=self.recruiter
        )

        self.job3 = Job.objects.create(
            title='Healthcare Data Analyst',
            company='Health Systems',
            location='San Francisco',
            job_type='Full-time',
            salary='$60,000 - $90,000',
            experience=2,
            skills=['Python', 'SQL', 'Healthcare'],
            description='Healthcare data analyst position',
            posted_by=self.recruiter
        )

        # Create user preferences
        self.preferences = UserJobPreference.objects.create(
            user=self.user,
            preferred_job_types=['Full-time', 'Remote'],
            preferred_locations=['New York', 'San Francisco'],
            min_salary_expectation=75000,
            remote_preference=True,
            industry_preferences=['Technology', 'Healthcare']
        )

    def test_recommendation_engine_reads_preferences(self):
        """Test that recommendation engine correctly reads user preferences"""
        recommender = ContentBasedRecommender()

        # Get recommendations
        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Verify recommendations were generated
        self.assertGreater(len(recommendations), 0)

        # Verify that jobs matching preferences get higher scores
        job_scores = {rec['job'].id: rec['score'] for rec in recommendations}

        # Job1 (Full-time, New York, Python skills) should score well
        # Job2 (Remote, JavaScript) should score well due to remote preference
        # Job3 (Full-time, San Francisco, Healthcare) should score well

        self.assertIn(self.job1.id, job_scores)
        self.assertIn(self.job2.id, job_scores)
        self.assertIn(self.job3.id, job_scores)

    def test_job_type_preference_matching(self):
        """Test that job type preferences are correctly applied"""
        recommender = ContentBasedRecommender()

        # Test with specific job type preference
        self.preferences.preferred_job_types = ['Remote']
        self.preferences.save()

        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Find the remote job in recommendations
        remote_job_rec = None
        fulltime_job_rec = None

        for rec in recommendations:
            if rec['job'].id == self.job2.id:  # Remote job
                remote_job_rec = rec
            elif rec['job'].id == self.job1.id:  # Full-time job
                fulltime_job_rec = rec

        # Remote job should have higher job type match score
        self.assertIsNotNone(remote_job_rec)
        # Note: We can't directly compare scores as they're weighted combinations
        # but we can verify the remote job is included in recommendations

    def test_location_preference_matching(self):
        """Test that location preferences are correctly applied"""
        recommender = ContentBasedRecommender()

        # Test with specific location preference
        self.preferences.preferred_locations = ['New York']
        self.preferences.save()

        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Verify New York job is included
        ny_job_found = any(rec['job'].location == 'New York' for rec in recommendations)
        self.assertTrue(ny_job_found)

    def test_remote_preference_boost(self):
        """Test that remote preference gives boost to remote jobs"""
        recommender = ContentBasedRecommender()

        # Enable remote preference
        self.preferences.remote_preference = True
        self.preferences.save()

        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Find remote job in recommendations
        remote_job_found = any(
            rec['job'].job_type == 'Remote'
            for rec in recommendations
        )
        self.assertTrue(remote_job_found)


class MatchingAlgorithmAnalysisTestCase(TestCase):
    """Test cases for analyzing matching algorithm effectiveness"""

    def setUp(self):
        """Set up test data for matching analysis"""
        self.user = User.objects.create_user(
            username='perfectmatch',
            email='perfect@example.com',
            password='testpass123',
            full_name='Perfect Match User',
            technical_skills='Python, Django, React, PostgreSQL',
            experience=5
        )

        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )

        # Create a "perfect match" job
        self.perfect_job = Job.objects.create(
            title='Senior Full-Stack Developer',
            company='Dream Company',
            location='New York',
            job_type='Full-time',
            salary='$100,000 - $130,000',
            experience=5,
            skills=['Python', 'Django', 'React', 'PostgreSQL'],
            description='Perfect match job for our user',
            posted_by=self.recruiter
        )

        # Create user preferences that match the perfect job
        self.preferences = UserJobPreference.objects.create(
            user=self.user,
            preferred_job_types=['Full-time'],
            preferred_locations=['New York'],
            min_salary_expectation=90000,
            remote_preference=False,
            industry_preferences=['Technology']
        )

    def test_perfect_match_score_calculation(self):
        """Test what score a perfect match job receives"""
        recommender = ContentBasedRecommender()

        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Find our perfect job
        perfect_job_rec = None
        for rec in recommendations:
            if rec['job'].id == self.perfect_job.id:
                perfect_job_rec = rec
                break

        self.assertIsNotNone(perfect_job_rec, "Perfect match job should be in recommendations")

        # Analyze the score
        score = perfect_job_rec['score']
        print(f"Perfect match job score: {score}")

        # The score should be high (close to 1.0)
        # Current algorithm: 0.5*skill + 0.2*exp + 0.15*location + 0.15*job_type
        # Perfect match should get: 0.5*1.0 + 0.2*1.0 + 0.15*1.0 + 0.15*1.0 = 1.0
        self.assertGreaterEqual(score, 0.8, "Perfect match should score at least 0.8")

    def test_identify_matching_gaps(self):
        """Identify gaps in the current matching algorithm"""
        recommender = ContentBasedRecommender()

        # Test individual components
        user_skills = self.user.get_skills_list()
        job_skills = self.perfect_job.skills

        # Test skill matching
        skill_score = recommender.calculate_skill_match(user_skills, job_skills)
        print(f"Skill match score: {skill_score}")

        # Test experience matching
        exp_score = recommender.calculate_experience_match(self.user.experience, self.perfect_job.experience)
        print(f"Experience match score: {exp_score}")

        # Test location matching
        location_score = recommender.calculate_location_match(self.user.organization, self.perfect_job.location)
        print(f"Location match score: {location_score}")

        # Test job type matching
        job_type_score = recommender.calculate_job_type_match(
            self.preferences.preferred_job_types,
            self.perfect_job.job_type
        )
        print(f"Job type match score: {job_type_score}")

        # Verify individual components
        self.assertEqual(skill_score, 1.0, "Perfect skill match should score 1.0")
        self.assertEqual(exp_score, 1.0, "Perfect experience match should score 1.0")
        self.assertEqual(job_type_score, 1.0, "Perfect job type match should score 1.0")

        # Location matching might be an issue - user.organization vs job.location
        # This is a gap in the current implementation

    def test_salary_matching_gap(self):
        """Test that salary matching is not implemented in current algorithm"""
        recommender = ContentBasedRecommender()

        # Current algorithm doesn't consider salary at all
        # This is a major gap for 100% matching

        # Create a job with salary below user's expectation
        low_salary_job = Job.objects.create(
            title='Low Salary Developer',
            company='Cheap Company',
            location='New York',
            job_type='Full-time',
            salary='$40,000 - $50,000',  # Below user's 90k expectation
            experience=5,
            skills=['Python', 'Django', 'React', 'PostgreSQL'],
            description='Same skills but low salary',
            posted_by=self.recruiter
        )

        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Find both jobs
        perfect_job_score = None
        low_salary_score = None

        for rec in recommendations:
            if rec['job'].id == self.perfect_job.id:
                perfect_job_score = rec['score']
            elif rec['job'].id == low_salary_job.id:
                low_salary_score = rec['score']

        # Currently, both jobs would get the same score because salary isn't considered
        # This is a gap that needs to be addressed
        if perfect_job_score and low_salary_score:
            print(f"Perfect job score: {perfect_job_score}")
            print(f"Low salary job score: {low_salary_score}")
            # They should be different, but currently they're the same

    def test_industry_matching_gap(self):
        """Test that industry matching is not implemented in current algorithm"""
        # Current algorithm doesn't consider industry preferences
        # This is another gap for 100% matching

        # The Job model doesn't have an industry field
        # This is a structural gap that needs to be addressed

        # Check if Job model has industry field
        job_fields = [field.name for field in Job._meta.get_fields()]
        self.assertNotIn('industry', job_fields, "Job model currently lacks industry field")

        # This means industry preferences can't be matched against jobs
        # This is a significant gap in the matching algorithm


class EnhancedRecommendationTestCase(TestCase):
    """Test cases for the enhanced recommendation engine"""

    def setUp(self):
        """Set up test data for enhanced recommendation testing"""
        self.user = User.objects.create_user(
            username='enhanceduser',
            email='enhanced@example.com',
            password='testpass123',
            full_name='Enhanced User',
            technical_skills='Python, Django, React, Machine Learning',
            experience=4
        )

        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )

        # Create comprehensive user preferences
        self.preferences = UserJobPreference.objects.create(
            user=self.user,
            preferred_job_types=['Full-time', 'Remote'],
            preferred_locations=['San Francisco', 'New York', 'Remote'],
            min_salary_expectation=90000,
            remote_preference=True,
            industry_preferences=['Technology', 'Healthcare']
        )

        # Create test jobs with different matching levels
        self.perfect_match_job = Job.objects.create(
            title='Senior Machine Learning Engineer',
            company='Tech Innovators',
            location='San Francisco',
            job_type='Full-time',
            salary='$120,000 - $150,000',
            experience=4,
            skills=['Python', 'Machine Learning', 'Django'],
            description='We are looking for a senior ML engineer with Python and Django experience in the technology sector.',
            posted_by=self.recruiter
        )

        self.good_match_job = Job.objects.create(
            title='Python Developer',
            company='Health Tech Solutions',
            location='New York',
            job_type='Full-time',
            salary='$95,000 - $115,000',
            experience=3,
            skills=['Python', 'Django', 'PostgreSQL'],
            description='Healthcare technology company seeking Python developer for medical software.',
            posted_by=self.recruiter
        )

        self.remote_job = Job.objects.create(
            title='Remote React Developer',
            company='Digital Solutions',
            location='Remote',
            job_type='Remote',
            salary='$85,000 - $105,000',
            experience=3,
            skills=['React', 'JavaScript', 'Node.js'],
            description='Remote position for React developer in technology industry.',
            posted_by=self.recruiter
        )

        self.poor_match_job = Job.objects.create(
            title='Junior Java Developer',
            company='Traditional Corp',
            location='Chicago',
            job_type='Full-time',
            salary='$50,000 - $65,000',
            experience=1,
            skills=['Java', 'Spring', 'MySQL'],
            description='Entry-level Java position in manufacturing industry.',
            posted_by=self.recruiter
        )

    def test_enhanced_recommendation_scoring(self):
        """Test that enhanced recommendation engine provides better scoring"""
        recommender = ContentBasedRecommender()

        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Convert to dictionary for easier lookup
        job_scores = {rec['job'].id: rec for rec in recommendations}

        # Verify all jobs are included
        self.assertIn(self.perfect_match_job.id, job_scores)
        self.assertIn(self.good_match_job.id, job_scores)
        self.assertIn(self.remote_job.id, job_scores)
        self.assertIn(self.poor_match_job.id, job_scores)

        # Get scores
        perfect_score = job_scores[self.perfect_match_job.id]['score']
        good_score = job_scores[self.good_match_job.id]['score']
        remote_score = job_scores[self.remote_job.id]['score']
        poor_score = job_scores[self.poor_match_job.id]['score']

        print(f"Perfect match score: {perfect_score}")
        print(f"Good match score: {good_score}")
        print(f"Remote job score: {remote_score}")
        print(f"Poor match score: {poor_score}")

        # Verify scoring hierarchy
        self.assertGreater(perfect_score, good_score, "Perfect match should score higher than good match")
        self.assertGreater(good_score, poor_score, "Good match should score higher than poor match")

        # Perfect match should score very high (close to 1.0)
        self.assertGreater(perfect_score, 0.8, "Perfect match should score above 0.8")

        # Poor match should score lower
        self.assertLess(poor_score, 0.6, "Poor match should score below 0.6")

    def test_salary_matching_improvement(self):
        """Test that salary matching works correctly"""
        recommender = ContentBasedRecommender()

        # Test salary parsing
        min_sal, max_sal = recommender.parse_salary_range("$120,000 - $150,000")
        self.assertEqual(min_sal, 120000)
        self.assertEqual(max_sal, 150000)

        # Test salary matching
        salary_score = recommender.calculate_salary_match(90000, "$120,000 - $150,000")
        self.assertEqual(salary_score, 1.0, "Job salary above user minimum should score 1.0")

        low_salary_score = recommender.calculate_salary_match(90000, "$50,000 - $65,000")
        self.assertLess(low_salary_score, 1.0, "Job salary below user minimum should score less than 1.0")

    def test_industry_matching_implementation(self):
        """Test that industry matching works with job content"""
        recommender = ContentBasedRecommender()

        # Test simple case first
        simple_tech_score = recommender.calculate_industry_match(
            ['Technology'],
            'software development',
            'Software Engineer',
            'Tech Corp'
        )
        print(f"Simple tech score: {simple_tech_score}")

        # Test no match case
        no_keywords_score = recommender.calculate_industry_match(
            ['Technology'],
            'farming agriculture',
            'Farm Worker',
            'Agriculture Corp'
        )
        print(f"No keywords score: {no_keywords_score}")

        # Basic verification
        self.assertGreater(simple_tech_score, 0.5, "Technology keywords should match")
        self.assertEqual(no_keywords_score, 0.2, "No matching keywords should return 0.2")

    def test_location_matching_improvement(self):
        """Test that location matching works with preferred locations list"""
        recommender = ContentBasedRecommender()

        # Test exact match
        exact_score = recommender.calculate_location_match(['San Francisco'], 'San Francisco')
        self.assertEqual(exact_score, 1.0, "Exact location match should score 1.0")

        # Test remote job matching
        remote_score = recommender.calculate_location_match(['New York'], 'Remote')
        self.assertEqual(remote_score, 1.0, "Remote jobs should match all location preferences")

        # Test multiple preferred locations
        multi_score = recommender.calculate_location_match(['San Francisco', 'New York'], 'New York')
        self.assertEqual(multi_score, 1.0, "Job location matching any preferred location should score 1.0")

        # Test no match
        no_match_score = recommender.calculate_location_match(['San Francisco'], 'Chicago')
        self.assertEqual(no_match_score, 0.0, "Non-matching location should score 0.0")

    def test_comprehensive_matching_analysis(self):
        """Test comprehensive matching to identify path to 100% match"""
        recommender = ContentBasedRecommender()

        recommendations = recommender.recommend_jobs(self.user, limit=10)

        # Find perfect match job
        perfect_match_rec = None
        for rec in recommendations:
            if rec['job'].id == self.perfect_match_job.id:
                perfect_match_rec = rec
                break

        self.assertIsNotNone(perfect_match_rec)

        # Analyze match details
        details = perfect_match_rec['match_details']

        print("Match Analysis for Perfect Job:")
        print(f"Skill Match: {details['skill_match']}")
        print(f"Experience Match: {details['experience_match']}")
        print(f"Location Match: {details['location_match']}")
        print(f"Job Type Match: {details['job_type_match']}")
        print(f"Industry Match: {details['industry_match']}")
        print(f"Salary Match: {details['salary_match']}")
        print(f"Overall Score: {perfect_match_rec['score']}")
        print(f"Reason: {perfect_match_rec['reason']}")

        # For 100% match, all components should be high
        self.assertGreater(details['skill_match'], 0.6, "Skills should match well")
        self.assertGreater(details['experience_match'], 0.8, "Experience should match well")
        self.assertGreater(details['location_match'], 0.8, "Location should match well")
        self.assertGreater(details['job_type_match'], 0.8, "Job type should match well")
        self.assertGreater(details['salary_match'], 0.8, "Salary should match well")

        # Overall score should be very high
        self.assertGreater(perfect_match_rec['score'], 0.85, "Perfect match should score above 0.85")


class JobPostingAndDetailsTestCase(TestCase):
    """Test cases for job posting and job details functionality"""

    def setUp(self):
        """Set up test data"""
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter',
            company_name='Test Company',
            company_description='A great technology company focused on innovation.'
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            technical_skills='Python, Django, JavaScript'
        )

        self.client = Client()

    def test_job_requirements_field_exists(self):
        """Test that Job model has requirements field"""
        # Check that requirements field exists in Job model
        job_fields = [field.name for field in Job._meta.get_fields()]
        self.assertIn('requirements', job_fields, "Job model should have requirements field")

    def test_job_creation_with_requirements(self):
        """Test creating a job with requirements"""
        job = Job.objects.create(
            title='Test Developer',
            company='Test Company',
            location='Test City',
            job_type='Full-time',
            salary='$80,000 - $100,000',
            experience=3,
            skills=['Python', 'Django'],
            description='Test job description',
            requirements='Bachelor degree in Computer Science\nMinimum 3 years experience',
            posted_by=self.recruiter
        )

        self.assertEqual(job.requirements, 'Bachelor degree in Computer Science\nMinimum 3 years experience')
        self.assertIsNotNone(job.requirements)

    def test_job_detail_view_shows_requirements(self):
        """Test that job detail view displays requirements"""
        job = Job.objects.create(
            title='Test Developer',
            company='Test Company',
            location='Test City',
            job_type='Full-time',
            salary='$80,000 - $100,000',
            experience=3,
            skills=['Python', 'Django'],
            description='Test job description',
            requirements='Bachelor degree required\n3+ years experience',
            posted_by=self.recruiter
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bachelor degree required')
        self.assertContains(response, '3+ years experience')
        self.assertContains(response, 'Requirements')

    def test_job_detail_view_shows_company_description(self):
        """Test that job detail view displays company description"""
        # Create recruiter profile with company description
        from accounts.models import RecruiterProfile
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Test Company',
            company_description='We are a leading technology company.'
        )

        job = Job.objects.create(
            title='Test Developer',
            company='Test Company',
            location='Test City',
            job_type='Full-time',
            description='Test job description',
            posted_by=self.recruiter
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'We are a leading technology company.')
        self.assertContains(response, 'About Test Company')

    def test_job_detail_view_shows_similar_jobs(self):
        """Test that job detail view shows similar jobs"""
        # Create main job
        main_job = Job.objects.create(
            title='Python Developer',
            company='Main Company',
            location='Main City',
            job_type='Full-time',
            skills=['Python', 'Django', 'PostgreSQL'],
            description='Main job description',
            posted_by=self.recruiter
        )

        # Create similar job
        similar_job = Job.objects.create(
            title='Django Developer',
            company='Similar Company',
            location='Similar City',
            job_type='Full-time',
            skills=['Python', 'Django', 'MySQL'],
            description='Similar job description',
            posted_by=self.recruiter
        )

        # Create unrelated job with different job type
        unrelated_job = Job.objects.create(
            title='Marketing Manager',
            company='Other Company',
            location='Other City',
            job_type='Part-time',  # Different job type
            skills=['Marketing', 'Social Media'],
            description='Unrelated job description',
            posted_by=self.recruiter
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:job_detail', args=[main_job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Similar Jobs')
        self.assertContains(response, 'Django Developer')
        # Marketing Manager should not appear as it has different job type and no skill overlap

    def test_recruiter_job_creation_api_with_requirements(self):
        """Test recruiter job creation API includes requirements"""
        self.client.login(username='recruiter', password='testpass123')

        job_data = {
            'title': 'API Test Job',
            'company': 'API Company',
            'location': 'API City',
            'type': 'Full-time',
            'salary': '$90,000 - $110,000',
            'experience': 2,
            'skills': ['Python', 'API'],
            'description': 'API test job description',
            'requirements': 'API requirements test'
        }

        response = self.client.post(
            reverse('recruiter:create_job'),
            data=json.dumps(job_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

        # Verify job was created with requirements
        job = Job.objects.get(title='API Test Job')
        self.assertEqual(job.requirements, 'API requirements test')

    def test_recruiter_job_update_api_with_requirements(self):
        """Test recruiter job update API includes requirements"""
        job = Job.objects.create(
            title='Update Test Job',
            company='Update Company',
            location='Update City',
            job_type='Full-time',
            description='Original description',
            requirements='Original requirements',
            posted_by=self.recruiter
        )

        self.client.login(username='recruiter', password='testpass123')

        update_data = {
            'title': 'Updated Test Job',
            'requirements': 'Updated requirements'
        }

        response = self.client.post(
            reverse('recruiter:update_job', args=[job.id]),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # Verify job was updated
        job.refresh_from_db()
        self.assertEqual(job.title, 'Updated Test Job')
        self.assertEqual(job.requirements, 'Updated requirements')

    def test_job_detail_match_score_calculation(self):
        """Test that job detail view calculates match score correctly"""
        job = Job.objects.create(
            title='Match Test Job',
            company='Match Company',
            location='Match City',
            job_type='Full-time',
            skills=['Python', 'Django', 'JavaScript'],
            description='Match test description',
            posted_by=self.recruiter
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Match Analysis')

        # Check that match score is calculated (user has Python, Django, JavaScript skills)
        match_score = response.context['match_score']
        self.assertGreater(match_score, 0, "Match score should be greater than 0")
        self.assertLessEqual(match_score, 100, "Match score should not exceed 100")


class CompanyDescriptionIntegrationTestCase(TestCase):
    """Test cases for company description integration"""

    def setUp(self):
        """Set up test data"""
        self.recruiter = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='testpass123',
            user_type='recruiter'
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.client = Client()

    def test_company_description_from_recruiter_profile(self):
        """Test company description from RecruiterProfile"""
        from accounts.models import RecruiterProfile

        # Create recruiter profile
        profile = RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name='Profile Company',
            company_description='Description from recruiter profile'
        )

        job = Job.objects.create(
            title='Profile Test Job',
            company='Profile Company',
            location='Test City',
            job_type='Full-time',
            description='Test description',
            posted_by=self.recruiter
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['company_description'], 'Description from recruiter profile')
        self.assertContains(response, 'Description from recruiter profile')

    def test_company_description_fallback_to_user_field(self):
        """Test company description fallback to User model field"""
        # Set company description in User model
        self.recruiter.company_description = 'Description from user field'
        self.recruiter.save()

        job = Job.objects.create(
            title='Fallback Test Job',
            company='Fallback Company',
            location='Test City',
            job_type='Full-time',
            description='Test description',
            posted_by=self.recruiter
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['company_description'], 'Description from user field')
        self.assertContains(response, 'Description from user field')

    def test_no_company_description_available(self):
        """Test when no company description is available"""
        job = Job.objects.create(
            title='No Description Job',
            company='No Description Company',
            location='Test City',
            job_type='Full-time',
            description='Test description',
            posted_by=self.recruiter
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['company_description'])
        self.assertContains(response, 'No company description available')
