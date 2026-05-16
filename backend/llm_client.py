"""
LLM client adapter.

Goal: let the codebase work on both Emergent (using EMERGENT_LLM_KEY +
`emergentintegrations`) AND on Railway/Render/Fly/local (using the direct
Google Gemini API via `google-generativeai`). Pick the right backend at
startup based on which env var is set — no caller code has to change.

Priority order:
  1. GEMINI_API_KEY (direct, cheaper, portable) — preferred for production
  2. EMERGENT_LLM_KEY (universal key — works only inside Emergent)
  3. None — LLM features are disabled, scrapers fall back to rule-based
     strategies and the classifier returns its default category.

Usage (same shape as the old `LlmChat` calls so we can migrate gradually):
    from llm_client import get_llm_client, LLMMessage

    client = await get_llm_client(
        system_message="You are a JSON diagnostic agent.",
        session_id="scraper_healer",
    )
    if client:
        reply = await client.send(LLMMessage(role="user", content="..."))
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    role: str  # "user" | "system" | "assistant"
    content: str


class _BaseClient:
    """Minimal async interface every backend must satisfy."""

    async def send(self, message: LLMMessage) -> str:  # pragma: no cover
        raise NotImplementedError


class _EmergentClient(_BaseClient):
    """Thin wrapper around `emergentintegrations.LlmChat`."""

    def __init__(self, chat):
        self._chat = chat

    async def send(self, message: LLMMessage) -> str:
        # emergentintegrations expects UserMessage objects
        from emergentintegrations.llm.chat import UserMessage  # type: ignore

        msg = UserMessage(text=message.content)
        return await self._chat.send_message(msg)


class _GeminiClient(_BaseClient):
    """Direct Google Gemini client. Uses `google-generativeai`."""

    def __init__(self, model_name: str, system_message: Optional[str], api_key: str):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "google-generativeai is not installed. Run "
                "`pip install google-generativeai` and add it to requirements.txt."
            ) from e

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_message or None,
        )

    async def send(self, message: LLMMessage) -> str:
        # google-generativeai's generate_content is sync; wrap it in a thread
        # so we don't block the event loop.
        import asyncio
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(message.content),
        )
        return (getattr(resp, "text", None) or "").strip()


async def get_llm_client(
    *, system_message: Optional[str] = None, session_id: str = "default",
    model: str = "gemini-2.5-flash",
) -> Optional[_BaseClient]:
    """
    Return an LLM client backed by whichever key is configured.
    Returns None if no key is set — callers should treat this as "LLM disabled".
    """
    direct_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    emergent_key = os.getenv("EMERGENT_LLM_KEY")

    if direct_key:
        try:
            client = _GeminiClient(model, system_message, direct_key)
            logger.info(
                f"[LLM] Using direct Gemini API (model={model}, session={session_id})"
            )
            return client
        except Exception as e:
            logger.error(f"[LLM] Direct Gemini init failed: {e}")
            # Fall through to Emergent fallback if direct fails

    if emergent_key:
        try:
            from emergentintegrations.llm.chat import LlmChat  # type: ignore

            chat = LlmChat(
                api_key=emergent_key,
                session_id=session_id,
                system_message=system_message or "",
            )
            # emergentintegrations naming: ("gemini", "gemini-2.5-flash")
            chat = chat.with_model("gemini", model)
            logger.info(
                f"[LLM] Using Emergent universal key (model={model}, session={session_id})"
            )
            return _EmergentClient(chat)
        except Exception as e:
            logger.error(f"[LLM] Emergent init failed: {e}")

    logger.warning(
        "[LLM] No API key found (set GEMINI_API_KEY or EMERGENT_LLM_KEY). "
        "LLM-dependent features (scraper healing, classification) are disabled."
    )
    return None
