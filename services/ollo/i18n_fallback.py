"""Language-aware fallback text for when the AI provider is unavailable.

Not a full i18n framework -- OLLO's system/user prompts are already sent to
the LLM in whatever language the founder writes in, so the model naturally
replies in-language. This module only covers the one place that can't go
through the model: the retried-out-empty fallback message shown when the AI
call itself failed, which previously stayed hardcoded English regardless of
the UI's selected language.
"""

from __future__ import annotations

_AI_UNAVAILABLE = {
    "en": "Founder, I couldn't reach the AI service right now ({error}). Please try again in a moment.",
    "tr": "Kurucu, şu anda AI servisine ulaşamadım ({error}). Lütfen birazdan tekrar deneyin.",
}

_BRIEFING_UNAVAILABLE = {
    "en": "Founder, I couldn't generate this briefing right now ({error}). Please try again in a moment.",
    "tr": "Kurucu, şu anda bu brifingi oluşturamadım ({error}). Lütfen birazdan tekrar deneyin.",
}


def ai_unavailable_message(error: str, language: str = "en") -> str:
    template = _AI_UNAVAILABLE.get(language, _AI_UNAVAILABLE["en"])
    return template.format(error=error)


def briefing_unavailable_message(error: str, language: str = "en") -> str:
    template = _BRIEFING_UNAVAILABLE.get(language, _BRIEFING_UNAVAILABLE["en"])
    return template.format(error=error)
