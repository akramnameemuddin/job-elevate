"""
Quick test script to verify gap analysis view works
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from assessments.views import job_skill_gap_analysis
from recruiter.models import Job

User = get_user_model()

# Create test request
factory = RequestFactory()
user = User.objects.first()
job = Job.objects.get(id=5)

# Create request with user
request = factory.get(f'/assessments/job/{job.id}/gaps/')
request.user = user

# Call the view
try:
    response = job_skill_gap_analysis(request, job_id=job.id)
    print(f"✓ View executed successfully")
    print(f"  Status Code: {response.status_code}")
    print(f"  Content Length: {len(response.content)} bytes")
    
    # Check context
    if hasattr(response, 'context_data'):
        context = response.context_data
        print(f"\n  Context Data:")
        print(f"    - Total gaps: {context.get('total_gaps', 0)}")
        print(f"    - Critical gaps: {len(context.get('critical_gaps', []))}")
        print(f"    - High gaps: {len(context.get('high_gaps', []))}")
        print(f"    - Moderate gaps: {len(context.get('moderate_gaps', []))}")
        print(f"    - Match score: {context.get('match_score', 0)}%")
    
    content_str = response.content.decode('utf-8')
    if 'No Skill Gaps Identified' in content_str:
        print("\n✗ WARNING: Page shows 'No Skill Gaps Identified'")
    else:
        print("\n✓ Page shows gap data")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
