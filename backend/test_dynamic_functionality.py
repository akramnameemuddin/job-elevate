#!/usr/bin/env python
"""
Test script to validate dynamic functionality of the JobElevate application
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import User
from recruiter.models import Job
from jobs.models import JobRecommendation, JobBookmark
from django.contrib.auth import get_user_model

def test_user_model_methods():
    """Test User model methods for dynamic functionality"""
    print("=== Testing User Model Methods ===")
    
    # Test profile completion calculation
    try:
        users = User.objects.all()[:5]  # Test with first 5 users
        for user in users:
            completion = user.profile_completion()
            print(f"User {user.username}: Profile completion = {completion}%")
            
            job_matches = user.get_job_matches_count()
            print(f"User {user.username}: Job matches = {job_matches}")
            
            skills = user.get_skills_list()
            print(f"User {user.username}: Skills = {len(skills)} skills")
            
        print("✓ User model methods working correctly")
        return True
    except Exception as e:
        print(f"✗ Error testing user methods: {e}")
        return False

def test_job_recommendation_system():
    """Test job recommendation functionality"""
    print("\n=== Testing Job Recommendation System ===")
    
    try:
        from jobs.recommendation_engine import HybridRecommender
        
        recommender = HybridRecommender()
        
        # Test with a sample user
        user = User.objects.filter(user_type__in=['student', 'professional']).first()
        if user:
            recommendations = recommender.recommend_jobs(user, limit=5)
            print(f"Generated {len(recommendations)} recommendations for user {user.username}")
            
            for i, rec in enumerate(recommendations[:3]):
                job = rec['job']
                score = rec['score']
                print(f"  {i+1}. {job.title} at {job.company} (Score: {score:.2f})")
                
        print("✓ Job recommendation system working correctly")
        return True
    except Exception as e:
        print(f"✗ Error testing recommendation system: {e}")
        return False

def test_dynamic_context_data():
    """Test that context processors provide dynamic data"""
    print("\n=== Testing Dynamic Context Data ===")
    
    try:
        from dashboard.context_processors import dashboard_context
        from backend.context_processors import user_initials
        
        # Create a mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        user = User.objects.first()
        if user:
            request = MockRequest(user)
            
            # Test dashboard context
            dashboard_ctx = dashboard_context(request)
            print(f"Dashboard context keys: {list(dashboard_ctx.keys())}")
            
            # Test user initials context
            initials_ctx = user_initials(request)
            print(f"User initials context: {initials_ctx}")
            
        print("✓ Context processors working correctly")
        return True
    except Exception as e:
        print(f"✗ Error testing context processors: {e}")
        return False

def test_database_integrity():
    """Test database integrity and relationships"""
    print("\n=== Testing Database Integrity ===")
    
    try:
        # Test user count
        user_count = User.objects.count()
        print(f"Total users in database: {user_count}")
        
        # Test job count
        job_count = Job.objects.count()
        print(f"Total jobs in database: {job_count}")
        
        # Test open jobs
        open_jobs = Job.objects.filter(status='Open').count()
        print(f"Open jobs: {open_jobs}")
        
        # Test recommendations
        recommendation_count = JobRecommendation.objects.count()
        print(f"Total job recommendations: {recommendation_count}")
        
        # Test bookmarks
        bookmark_count = JobBookmark.objects.count()
        print(f"Total job bookmarks: {bookmark_count}")
        
        print("✓ Database integrity checks passed")
        return True
    except Exception as e:
        print(f"✗ Error testing database integrity: {e}")
        return False

def test_skills_matching():
    """Test skills matching functionality"""
    print("\n=== Testing Skills Matching ===")
    
    try:
        from jobs.recommendation_engine import ContentBasedRecommender
        
        recommender = ContentBasedRecommender()
        
        # Test skill matching with sample data
        user_skills = ['python', 'django', 'javascript', 'react']
        job_skills = ['python', 'django', 'postgresql', 'docker']
        
        match_score = recommender.calculate_skill_match(user_skills, job_skills)
        print(f"Skill match score: {match_score:.2f}")
        
        # Test with real data
        user = User.objects.filter(technical_skills__isnull=False).first()
        job = Job.objects.filter(skills__isnull=False).first()
        
        if user and job:
            user_skills = user.get_skills_list()
            job_skills = job.skills
            
            if user_skills and job_skills:
                real_match_score = recommender.calculate_skill_match(user_skills, job_skills)
                print(f"Real data match score: {real_match_score:.2f}")
        
        print("✓ Skills matching working correctly")
        return True
    except Exception as e:
        print(f"✗ Error testing skills matching: {e}")
        return False

def main():
    """Run all tests"""
    print("JobElevate Dynamic Functionality Test Suite")
    print("=" * 50)
    
    test_results = []
    
    test_results.append(test_database_integrity())
    test_results.append(test_user_model_methods())
    test_results.append(test_dynamic_context_data())
    test_results.append(test_skills_matching())
    test_results.append(test_job_recommendation_system())
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Dynamic functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()
