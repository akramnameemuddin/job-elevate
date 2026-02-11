"""
Seed the community app with sample tags and events.
Run with: python manage.py seed_community
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from community.models import Tag, Event

User = get_user_model()

TAGS = [
    ('python', 'Python'),
    ('javascript', 'JavaScript'),
    ('career-advice', 'Career Advice'),
    ('interview-tips', 'Interview Tips'),
    ('resume-help', 'Resume Help'),
    ('remote-work', 'Remote Work'),
    ('data-science', 'Data Science'),
    ('web-development', 'Web Development'),
    ('machine-learning', 'Machine Learning'),
    ('job-search', 'Job Search'),
    ('networking', 'Networking'),
    ('freelancing', 'Freelancing'),
    ('tech-news', 'Tech News'),
    ('mentorship', 'Mentorship'),
    ('upskilling', 'Upskilling'),
]

EVENTS = [
    {
        'title': 'Advanced React Patterns & Performance',
        'description': 'Deep dive into advanced React concepts including hooks, context, and performance optimization techniques. Learn how to write scalable, maintainable React applications from industry experts.',
        'event_type': 'workshop',
        'speaker_name': 'John Martinez',
        'speaker_title': 'Senior Frontend Developer at Meta',
        'hours_from_now': 72,
        'duration_hours': 2,
        'is_free': False,
        'price': 29,
        'max_attendees': 200,
    },
    {
        'title': 'Tech Professionals Virtual Meetup',
        'description': 'Connect with fellow developers, share experiences, and build meaningful professional relationships. Break-out rooms for specific tech stacks and career stages.',
        'event_type': 'networking',
        'speaker_name': '',
        'speaker_title': '',
        'hours_from_now': 120,
        'duration_hours': 2,
        'is_free': True,
        'price': 0,
        'max_attendees': 150,
    },
    {
        'title': 'From Junior to Senior: Career Progression Tips',
        'description': 'Learn proven strategies for advancing your tech career from industry veterans who have made the journey. Panel discussion with Q&A session.',
        'event_type': 'career',
        'speaker_name': 'Panel of 4 Experts',
        'speaker_title': 'Engineering Leads from FAANG',
        'hours_from_now': 168,
        'duration_hours': 1.5,
        'is_free': True,
        'price': 0,
        'max_attendees': 500,
        'is_featured': True,
    },
    {
        'title': 'Microservices Architecture Deep Dive',
        'description': 'Comprehensive guide to designing, implementing, and scaling microservices in production environments. Hands-on coding exercises included.',
        'event_type': 'tech',
        'speaker_name': 'Alex Thompson',
        'speaker_title': 'Solutions Architect at AWS',
        'hours_from_now': 240,
        'duration_hours': 2,
        'is_free': False,
        'price': 39,
        'max_attendees': 150,
    },
    {
        'title': 'Cloud Security Best Practices',
        'description': 'Essential security strategies for protecting cloud infrastructure and applications in modern environments. Includes downloadable resource pack.',
        'event_type': 'webinar',
        'speaker_name': 'Maria Rodriguez',
        'speaker_title': 'Security Expert at CrowdStrike',
        'hours_from_now': 336,
        'duration_hours': 1.5,
        'is_free': True,
        'price': 0,
        'max_attendees': 500,
    },
    {
        'title': 'Data Science with Python Bootcamp',
        'description': 'Intensive hands-on workshop covering data analysis, visualization, and machine learning fundamentals. Certificate of completion provided.',
        'event_type': 'workshop',
        'speaker_name': 'Dr. Emily Watson',
        'speaker_title': 'Data Scientist at Google',
        'hours_from_now': 480,
        'duration_hours': 8,
        'is_free': False,
        'price': 89,
        'max_attendees': 100,
    },
    {
        'title': 'The Future of AI in Software Development',
        'description': 'Join industry experts as they discuss how artificial intelligence is transforming the software development landscape and what it means for developers careers.',
        'event_type': 'webinar',
        'speaker_name': 'Dr. Sarah Chen',
        'speaker_title': 'CTO at TechCorp',
        'hours_from_now': 48,
        'duration_hours': 1.5,
        'is_free': True,
        'price': 0,
        'max_attendees': 1000,
        'is_featured': True,
    },
    {
        'title': 'Resume & Portfolio Review Session',
        'description': 'Get personalized feedback on your resume and portfolio from hiring managers and experienced recruiters. Limited one-on-one slots available.',
        'event_type': 'career',
        'speaker_name': 'HR Panel',
        'speaker_title': 'Hiring Managers from Top Companies',
        'hours_from_now': 96,
        'duration_hours': 2,
        'is_free': True,
        'price': 0,
        'max_attendees': 80,
    },
]


class Command(BaseCommand):
    help = 'Seed community app with sample tags and events'

    def handle(self, *args, **options):
        # ── Tags ─────────────────────────────
        created_tags = 0
        for slug, name in TAGS:
            _, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': f'Discussions about {name}'},
            )
            if created:
                created_tags += 1
        self.stdout.write(self.style.SUCCESS(f'Tags: {created_tags} created, {len(TAGS) - created_tags} already existed'))

        # ── Events ───────────────────────────
        # Need at least one user to be the event creator
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.WARNING(
                'No users in database – skipping event creation. Create a user first.'
            ))
            return

        now = timezone.now()
        created_events = 0
        for ev in EVENTS:
            if Event.objects.filter(title=ev['title']).exists():
                continue

            start = now + timedelta(hours=ev['hours_from_now'])
            end = start + timedelta(hours=ev['duration_hours'])

            Event.objects.create(
                title=ev['title'],
                description=ev['description'],
                event_type=ev['event_type'],
                speaker_name=ev.get('speaker_name', ''),
                speaker_title=ev.get('speaker_title', ''),
                start_datetime=start,
                end_datetime=end,
                is_free=ev['is_free'],
                price=ev['price'],
                max_attendees=ev['max_attendees'],
                is_featured=ev.get('is_featured', False),
                created_by=user,
            )
            created_events += 1

        self.stdout.write(self.style.SUCCESS(
            f'Events: {created_events} created, {len(EVENTS) - created_events} already existed'
        ))
        self.stdout.write(self.style.SUCCESS('Done! Community data seeded.'))
