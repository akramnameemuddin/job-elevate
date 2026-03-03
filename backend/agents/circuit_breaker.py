"""
Circuit Breaker for external AI API calls
==========================================
Prevents repeated calls to the Gemini API when the quota is exhausted or
the service is temporarily unavailable.

State is stored in Django's cache (defaults to in-memory / LocMemCache) so
it is shared across all threads in the same process.

Usage
-----
    from agents.circuit_breaker import is_open, record_error, record_success

    if is_open():
        return []  # skip the API call

    try:
        result = call_api(...)
        record_success()
    except QuotaError:
        record_error()

Thresholds (all configurable via Django settings)
--------------------------------------------------
    CB_FAILURE_THRESHOLD  – errors within window before opening  (default 5)
    CB_RECOVERY_TIMEOUT   – seconds circuit stays open           (default 120)
    CB_ERROR_WINDOW       – seconds to count failures in         (default 60)
"""
from __future__ import annotations

import logging
import time
from threading import Lock

from django.conf import settings

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
_FAILURE_THRESHOLD: int = getattr(settings, "CB_FAILURE_THRESHOLD", 5)
_RECOVERY_TIMEOUT: int  = getattr(settings, "CB_RECOVERY_TIMEOUT", 120)   # seconds
_ERROR_WINDOW: int      = getattr(settings, "CB_ERROR_WINDOW", 60)         # seconds

# ── In-process state (fallback when cache is unavailable) ─────────────────────
_lock = Lock()
_error_timestamps: list[float] = []
_opened_at: float | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _cache_get(key: str, default=None):
    try:
        from django.core.cache import cache
        val = cache.get(key)
        return default if val is None else val
    except Exception:
        return default


def _cache_set(key: str, value, timeout: int = 300):
    try:
        from django.core.cache import cache
        cache.set(key, value, timeout=timeout)
    except Exception:
        pass


# ── Public API ─────────────────────────────────────────────────────────────────

def is_open() -> bool:
    """
    Return ``True`` when the circuit is *open* (i.e. calls should be
    suppressed).  Returns ``False`` (circuit *closed*) in normal operation.
    """
    global _opened_at, _error_timestamps

    now = time.monotonic()

    # --- Check cache-level state first (shared across threads) ---
    opened_at = _cache_get("cb:opened_at")

    if opened_at is not None:
        elapsed = time.time() - opened_at        # wall-clock stored in cache
        if elapsed < _RECOVERY_TIMEOUT:
            logger.debug("Circuit breaker OPEN (%.0fs remaining)", _RECOVERY_TIMEOUT - elapsed)
            return True
        # Recovery timeout elapsed – reset
        _cache_set("cb:opened_at", None)
        _cache_set("cb:errors", [])
        logger.info("Circuit breaker HALF-OPEN – allowing next call")
        return False

    return False


def record_error() -> None:
    """Record a failed API call.  Opens the circuit when threshold is reached."""
    global _opened_at

    now_mono = time.monotonic()
    now_wall = time.time()

    with _lock:
        errors: list[float] = _cache_get("cb:errors", [])
        # Prune timestamps outside the sliding window
        errors = [t for t in errors if now_wall - t < _ERROR_WINDOW]
        errors.append(now_wall)
        _cache_set("cb:errors", errors, timeout=_ERROR_WINDOW + 10)

        if len(errors) >= _FAILURE_THRESHOLD:
            _cache_set("cb:opened_at", now_wall, timeout=_RECOVERY_TIMEOUT + 60)
            logger.warning(
                "Circuit breaker OPENED after %d errors in %ds window",
                len(errors),
                _ERROR_WINDOW,
            )


def record_success() -> None:
    """Record a successful API call.  Resets error counters."""
    with _lock:
        _cache_set("cb:errors", [], timeout=_ERROR_WINDOW + 10)
        _cache_set("cb:opened_at", None)


def reset() -> None:
    """Manually reset the circuit breaker (e.g. from a management command)."""
    with _lock:
        _cache_set("cb:errors", [])
        _cache_set("cb:opened_at", None)
    logger.info("Circuit breaker manually reset")


def status() -> dict:
    """Return a dict with current circuit breaker state (useful for admin/health checks)."""
    opened_at = _cache_get("cb:opened_at")
    errors: list = _cache_get("cb:errors", [])
    now = time.time()

    if opened_at is not None:
        remaining = max(0, _RECOVERY_TIMEOUT - (now - opened_at))
        state = "open"
    else:
        remaining = 0
        state = "closed"

    return {
        "state": state,
        "error_count": len(errors),
        "failure_threshold": _FAILURE_THRESHOLD,
        "recovery_timeout": _RECOVERY_TIMEOUT,
        "recovery_remaining_seconds": round(remaining),
    }
