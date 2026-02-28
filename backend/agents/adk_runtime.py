"""
Google ADK Runtime Helpers
==========================
Thin wrapper around the official ``google-adk`` package.

Sets up environment variables required by ADK (``GOOGLE_API_KEY``,
``GOOGLE_GENAI_USE_VERTEXAI``) and exposes helpers for creating Runners
and calling agents from synchronous Django code.

Usage
-----
    from agents.adk_runtime import call_agent, create_runner, MODEL_GEMINI

    runner = create_runner(root_agent)
    result = call_agent(runner, user_id="u1", session_id="s1", query="Hello")
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# ── ADK model constant ────────────────────────────────────────────────
MODEL_GEMINI = "gemini-2.0-flash"


# ── Environment bootstrap ─────────────────────────────────────────────
def _ensure_env():
    """
    Populate the env-vars that ``google-adk`` reads at import time.
    Called lazily so Django settings are available.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        api_key = getattr(settings, "GOOGLE_API_KEY", None)
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

    # We use Google AI Studio (not Vertex AI)
    if not os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"):
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"


# ── Runner factory ────────────────────────────────────────────────────
def create_runner(agent, *, app_name: str = "job_elevate"):
    """
    Create an ADK ``Runner`` with an ``InMemorySessionService``
    for the given *agent*.
    """
    _ensure_env()
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    return Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )


# ── Synchronous helper ────────────────────────────────────────────────
def call_agent(
    runner,
    *,
    user_id: str,
    session_id: str,
    query: str,
) -> str:
    """
    Send *query* to the runner's agent and return the final text response.

    This is a **synchronous** wrapper suitable for Django views.
    Internally it runs the async ADK loop via ``asyncio.run()`` (or
    uses a thread-pool if a loop is already running).
    """
    async def _inner() -> str:
        from google.genai import types

        # Ensure a session exists (idempotent for InMemorySessionService)
        try:
            await runner.session_service.create_session(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            pass  # session may already exist

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)],
        )

        final_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text or ""
                break
        return final_text

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _inner()).result(timeout=120)
    else:
        return asyncio.run(_inner())


async def call_agent_async(
    runner,
    *,
    user_id: str,
    session_id: str,
    query: str,
) -> str:
    """Async version of ``call_agent``."""
    from google.genai import types

    try:
        await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )
    except Exception:
        pass

    content = types.Content(
        role="user",
        parts=[types.Part(text=query)],
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text or ""
            break
    return final_text
