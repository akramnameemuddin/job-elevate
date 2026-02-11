"""
Circuit Breaker for Gemini API calls
=====================================
After a 429 / RESOURCE_EXHAUSTED error, all subsequent Gemini calls are
skipped for ``COOLDOWN_SECONDS`` (default 5 minutes).  This prevents:

• Log spam from repeated failures
• Wasted network round-trips
• Slow page loads while waiting for timeouts

The breaker is process-global (module-level) so every agent shares state.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────
COOLDOWN_SECONDS: int = 300          # 5 minutes
_QUOTA_KEYWORDS = ("RESOURCE_EXHAUSTED", "429", "quota")

# ── Shared state (thread-safe) ──────────────────────────────────────
_lock = threading.Lock()
_tripped_at: float = 0.0             # epoch when breaker last tripped


def is_open() -> bool:
    """Return *True* if the breaker is currently open (calls should be skipped)."""
    with _lock:
        if _tripped_at == 0.0:
            return False
        elapsed = time.time() - _tripped_at
        if elapsed >= COOLDOWN_SECONDS:
            # Cooldown expired → reset and allow calls through
            return False
        return True


def remaining_cooldown() -> int:
    """Seconds left until the breaker resets (0 if closed)."""
    with _lock:
        if _tripped_at == 0.0:
            return 0
        left = COOLDOWN_SECONDS - (time.time() - _tripped_at)
        return max(int(left), 0)


def trip(reason: str = "") -> None:
    """Open the breaker – all future calls will be skipped until cooldown."""
    with _lock:
        global _tripped_at
        _tripped_at = time.time()
    logger.warning(
        "Circuit breaker OPEN – Gemini calls disabled for %ds. Reason: %s",
        COOLDOWN_SECONDS,
        reason[:200],
    )


def record_error(exc: Exception) -> bool:
    """
    Inspect *exc* and trip the breaker if it looks like a quota error.
    Returns ``True`` if the breaker was tripped.
    """
    msg = str(exc)
    if any(kw in msg for kw in _QUOTA_KEYWORDS):
        trip(msg)
        return True
    return False


def reset() -> None:
    """Manually close the breaker (e.g. after changing the API key)."""
    with _lock:
        global _tripped_at
        _tripped_at = 0.0
    logger.info("Circuit breaker RESET – Gemini calls re-enabled.")
