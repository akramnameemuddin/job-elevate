"""
Compatibility shim for existing code that imports ai_quiz_generator.
This re-exports the question_generator from ai_service.py
"""
from .ai_service import question_generator

# Alias for backward compatibility
ai_quiz_generator = question_generator

# Export for convenience
__all__ = ['ai_quiz_generator']
