import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Disable foreign key checks temporarily
cursor.execute('PRAGMA foreign_keys = OFF')

print("Deleting all user data...")
cursor.execute('DELETE FROM assessments_useranswer')
print("- User answers deleted")

cursor.execute('DELETE FROM assessments_assessmentattempt')
print("- Assessment attempts deleted")

cursor.execute('DELETE FROM assessments_userskillscore')
print("- User skill scores deleted (verified skills removed)")

cursor.execute('DELETE FROM assessments_questionbank')
print("- All questions deleted")

cursor.execute('UPDATE assessments_skill SET question_count=0, questions_generated=0, questions_generated_at=NULL')
print("- Skills reset")

# Re-enable foreign key checks
cursor.execute('PRAGMA foreign_keys = ON')

print("\n✓ Complete fresh start ready!")
print("✓ All verified skills removed")
print("✓ All questions deleted")
print("✓ All assessment data cleared")
