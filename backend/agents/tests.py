"""
Basic smoke tests for the agents app.
Run with: python manage.py test agents
"""
from django.test import TestCase
from .models import AgentMessage, AgentRunLog


class AgentMessageModelTest(TestCase):
    def test_create_message(self):
        msg = AgentMessage.objects.create(
            sender_agent="CareerGuidanceAgent",
            receiver_agent="RecruiterMatchingAgent",
            intent="evaluate_candidates_for_job",
            payload={"job_id": 1},
        )
        self.assertEqual(msg.sender_agent, "CareerGuidanceAgent")
        self.assertIn("evaluate_candidates", str(msg))

    def test_run_log(self):
        run = AgentRunLog.objects.create(
            run_type="full_multi_agent",
            status="running",
        )
        msg = AgentMessage.objects.create(
            sender_agent="Orchestrator",
            receiver_agent="CareerGuidanceAgent",
            intent="test",
            payload={},
        )
        run.messages.add(msg)
        self.assertEqual(run.messages.count(), 1)
