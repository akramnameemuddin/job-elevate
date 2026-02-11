"""
Google ADK-Style Runtime Abstraction
=====================================
Implements the core Agent + Tool + Orchestrator pattern modelled after
Google's Agent Development Kit (ADK) concepts.

Architecture
------------
• **BaseAgent**  – wraps ``google.generativeai`` (Gemini).  Each agent has
  a *name*, *description*, registered *tools*, and a ``run()`` method that
  builds a prompt, optionally invokes tools, calls Gemini, and returns
  structured JSON.

• **@tool** decorator – marks ordinary Python methods so they are
  discoverable by the agent at runtime. Tool metadata (name, docstring,
  parameter hints) is automatically collected and injected into the LLM
  prompt so Gemini can decide which tool to call.

• **ToolRegistry** – per-agent registry that stores decorated tools and
  provides helper methods to build the "available tools" section of a
  prompt and to dispatch calls.

Usage
-----
    from agents.adk_runtime import BaseAgent, tool

    class MyAgent(BaseAgent):
        name = "MyAgent"
        description = "Does something useful."

        @tool
        def fetch_data(self, query: str) -> dict:
            \"\"\"Fetch data from the database.\"\"\"
            ...

        def run(self, message, context=None):
            return super().run(message, context)
"""
from __future__ import annotations

import functools
import inspect
import json
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool decorator & registry
# ---------------------------------------------------------------------------

_TOOL_ATTR = "_adk_tool_meta"


def tool(func: Callable) -> Callable:
    """
    Decorator that marks a method as an ADK-style *tool*.

    The agent's prompt will include tool metadata so the LLM can decide to
    invoke it.  The decorated method keeps its original behaviour – the
    decorator only attaches hidden metadata.

    Example::

        class MyAgent(BaseAgent):
            @tool
            def lookup_user(self, user_id: int) -> dict:
                \"\"\"Look up a user by ID.\"\"\"
                ...
    """
    sig = inspect.signature(func)
    params = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        annotation = param.annotation
        param_type = "string"
        if annotation is not inspect.Parameter.empty:
            if annotation in (int, float):
                param_type = "number"
            elif annotation is bool:
                param_type = "boolean"
            elif annotation in (list, List):
                param_type = "array"
            elif annotation in (dict, Dict):
                param_type = "object"
        params[name] = {"type": param_type}

    meta = {
        "name": func.__name__,
        "description": (func.__doc__ or "").strip(),
        "parameters": params,
    }
    setattr(func, _TOOL_ATTR, meta)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    setattr(wrapper, _TOOL_ATTR, meta)
    return wrapper


class ToolRegistry:
    """Collects ``@tool``-decorated methods from a class instance."""

    def __init__(self, owner: "BaseAgent"):
        self._tools: Dict[str, Callable] = {}
        for attr_name in dir(owner):
            try:
                attr = getattr(owner, attr_name)
            except Exception:
                continue
            meta = getattr(attr, _TOOL_ATTR, None)
            if meta is not None:
                self._tools[meta["name"]] = attr

    @property
    def tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> str:
        """Return a formatted list of tools for inclusion in the LLM prompt."""
        lines: list[str] = []
        for attr in self._tools.values():
            meta = getattr(attr, _TOOL_ATTR)
            params_str = ", ".join(
                f"{k}: {v['type']}" for k, v in meta["parameters"].items()
            )
            lines.append(
                f"- **{meta['name']}**({params_str}): {meta['description']}"
            )
        return "\n".join(lines) if lines else "(no tools registered)"

    def call(self, name: str, kwargs: dict) -> Any:
        """Dispatch a tool call by name."""
        fn = self._tools.get(name)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        return fn(**kwargs)


# ---------------------------------------------------------------------------
# BaseAgent
# ---------------------------------------------------------------------------

class BaseAgent:
    """
    ADK-style base agent wrapping Google Gemini (``google-generativeai``).

    Sub-classes must set ``name`` and ``description`` and may override
    ``build_system_prompt`` to customise instructions.  Tools are
    automatically discovered from ``@tool``-decorated methods.

    Key method – ``run(message, context=None)``:
        1. Builds a system prompt that includes tool descriptions.
        2. Appends the user message (plus optional context).
        3. Calls Gemini.
        4. Parses the response as JSON (falls back to raw text wrapped in
           ``{"response": ...}`` on parse failure).
    """

    # Subclasses must provide these:
    name: str = "BaseAgent"
    description: str = "A generic ADK agent."
    model_name: str = "gemini-2.5-flash-lite"

    def __init__(self):
        self._registry = ToolRegistry(self)
        self._client = None

    # ------------------------------------------------------------------
    # Gemini client (lazy, so import errors only surface when actually used)
    # ------------------------------------------------------------------
    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                api_key = getattr(settings, "GOOGLE_API_KEY", None) or os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    raise RuntimeError("GOOGLE_API_KEY is not set in settings or environment.")
                self._client = genai.Client(api_key=api_key)
            except ImportError:
                raise ImportError(
                    "google-generativeai (google-genai) is required. "
                    "Install with: pip install google-genai"
                )
        return self._client

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    def build_system_prompt(self) -> str:
        """
        Build the system-level instructions injected before every call.
        Override in subclasses for domain-specific instructions.
        """
        tools_desc = self._registry.get_tool_descriptions()
        return (
            f"You are **{self.name}** – {self.description}\n\n"
            f"## Available Tools\n{tools_desc}\n\n"
            "## Response Format\n"
            "Always respond with **valid JSON only** (no markdown fences, no extra text).\n"
            "If you decide to call a tool, respond with:\n"
            '{"tool_call": {"name": "<tool_name>", "arguments": {<args>}}}\n\n'
            "Otherwise, respond with a JSON object containing your analysis/results.\n"
        )

    def _build_prompt(self, message: str, context: Optional[dict] = None) -> str:
        """Combine system prompt, optional context, and user message."""
        parts = [self.build_system_prompt()]
        if context:
            parts.append(f"## Context\n```json\n{json.dumps(context, default=str)}\n```\n")
        parts.append(f"## User Message\n{message}")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Core run loop
    # ------------------------------------------------------------------
    def run(self, message: str, context: Optional[dict] = None) -> dict:
        """
        Execute the agent:
        1. Build prompt  →  2. Call Gemini  →  3. Parse JSON  →
        4. If tool_call → execute tool, re-run with result  →  5. Return dict.
        """
        prompt = self._build_prompt(message, context)
        raw = self._call_gemini(prompt)
        result = self._parse_json(raw)

        # Handle tool calls (one level of recursion)
        if "tool_call" in result:
            tc = result["tool_call"]
            tool_name = tc.get("name", "")
            tool_args = tc.get("arguments", {})
            logger.info("[%s] Tool call → %s(%s)", self.name, tool_name, tool_args)
            try:
                tool_result = self._registry.call(tool_name, tool_args)
            except Exception as exc:
                logger.error("[%s] Tool %s failed: %s", self.name, tool_name, exc)
                tool_result = {"error": str(exc)}

            # Feed tool output back into Gemini for final answer
            follow_up = (
                f"Tool '{tool_name}' returned:\n"
                f"```json\n{json.dumps(tool_result, default=str)}\n```\n"
                "Now produce your final JSON response."
            )
            raw = self._call_gemini(self._build_prompt(follow_up, context))
            result = self._parse_json(raw)

        return result

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------
    def _call_gemini(self, prompt: str) -> str:
        """Send *prompt* to Gemini and return the raw text response."""
        from agents.circuit_breaker import is_open, remaining_cooldown, record_error

        if is_open():
            logger.info(
                "[%s] Circuit breaker OPEN – skipping Gemini (%ds left)",
                self.name, remaining_cooldown(),
            )
            return json.dumps({"error": "Gemini API temporarily unavailable (quota cooldown)"})

        try:
            from google.genai import types

            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                ),
            )
            return response.text.strip()
        except Exception as exc:
            record_error(exc)
            logger.error("[%s] Gemini call failed: %s", self.name, exc)
            return json.dumps({"error": f"Gemini call failed: {exc}"})

    # ------------------------------------------------------------------
    # JSON parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_json(text: str) -> dict:
        """
        Best-effort extraction of a JSON object from LLM output.
        Handles markdown code fences and stray text.
        """
        # Strip markdown fences
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (with optional language tag)
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try to extract the first JSON object with brace matching
        brace_start = cleaned.find("{")
        if brace_start != -1:
            depth = 0
            for i in range(brace_start, len(cleaned)):
                if cleaned[i] == "{":
                    depth += 1
                elif cleaned[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(cleaned[brace_start : i + 1])
                        except json.JSONDecodeError:
                            break

        # Fallback: wrap raw text
        return {"response": text}
