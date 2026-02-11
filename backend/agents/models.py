"""
Multi-Agent System Models
=========================
Stores inter-agent messages and run logs for the Google-ADK-style
multi-agent orchestration layer.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AgentMessage(models.Model):
    """
    Persistent log of every message exchanged between agents.
    Used for demo transparency and debugging the multi-agent pipeline.

    Fields
    ------
    sender_agent : str   – logical name of the sending agent (e.g. "CareerGuidanceAgent")
    receiver_agent : str – logical name of the receiving agent (e.g. "RecruiterMatchingAgent")
    intent : str         – action the sender wants the receiver to perform
                           (e.g. "evaluate_candidates_for_job")
    payload : JSON       – structured data attached to the message
    created_at : dt      – auto-set timestamp
    """
    sender_agent = models.CharField(
        _('sender agent'),
        max_length=100,
        help_text="Logical name of the sending agent"
    )
    receiver_agent = models.CharField(
        _('receiver agent'),
        max_length=100,
        help_text="Logical name of the receiving agent"
    )
    intent = models.CharField(
        _('intent'),
        max_length=200,
        help_text="Action the sender wants the receiver to perform"
    )
    payload = models.JSONField(
        _('payload'),
        default=dict,
        help_text="Structured data attached to the message"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('agent message')
        verbose_name_plural = _('agent messages')
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender_agent} → {self.receiver_agent}] {self.intent}"


class AgentRunLog(models.Model):
    """
    High-level run log for an orchestrator session.
    Groups multiple AgentMessages under one run so the demo UI can
    display an end-to-end timeline.
    """
    STATUS_CHOICES = [
        ('running', _('Running')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent_runs',
        verbose_name=_('user'),
        null=True,
        blank=True,
    )
    run_type = models.CharField(
        _('run type'),
        max_length=100,
        help_text="e.g. career_flow, recruiter_flow, full_multi_agent"
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='running',
    )
    result = models.JSONField(
        _('result'),
        default=dict,
        blank=True,
    )
    messages = models.ManyToManyField(
        AgentMessage,
        related_name='runs',
        blank=True,
        verbose_name=_('messages'),
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('agent run log')
        verbose_name_plural = _('agent run logs')
        ordering = ['-started_at']

    def __str__(self):
        return f"Run #{self.pk} ({self.run_type}) – {self.status}"
