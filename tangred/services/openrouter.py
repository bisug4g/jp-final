import logging
import re
import time

import requests
from django.conf import settings

logger = logging.getLogger("core")


class OpenRouterConfigurationError(RuntimeError):
    pass


class OpenRouterAPIError(RuntimeError):
    pass


def openrouter_is_configured() -> bool:
    return bool(getattr(settings, "OPENROUTER_API_KEY", "").strip())


def _clean_optimized_prompt(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    # Drop common meta-prefaces from open models and keep only the final prompt text.
    for marker in ["Let's craft:", "Final prompt:", "Optimized prompt:"]:
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[1].strip()

    quoted_prompt = re.search(r'["“](Design|Create|Craft|Build)(.*?)["”]\s*$', cleaned, re.IGNORECASE | re.DOTALL)
    if quoted_prompt:
        cleaned = f"{quoted_prompt.group(1)}{quoted_prompt.group(2)}".strip()

    direct_start = re.search(r"\b(Design|Create|Craft|Build)\b.*", cleaned, re.IGNORECASE | re.DOTALL)
    if direct_start:
        cleaned = direct_start.group(0).strip()

    return cleaned.strip().strip('"').strip("“").strip("”").strip()


def optimize_tan_studio_prompt(*, project_title: str, project_description: str, prompt: str, device_type: str) -> dict[str, str]:
    if not openrouter_is_configured():
        raise OpenRouterConfigurationError(
            "OpenRouter is unavailable because OPENROUTER_API_KEY is not configured."
        )

    system_prompt = (
        "You are the Tan Studio prompt optimizer. Rewrite the user's idea into one powerful, production-ready "
        "screen-generation prompt for Stitch. Keep it to a single screen. Make the result concrete, visual, and "
        "implementation-aware. Include layout hierarchy, copy tone, component details, trust cues, spacing, interaction hints, "
        "accessibility considerations, and color/material direction when useful. Preserve the user's intent. "
        "Return only the final prompt text. Do not include reasoning, prefaces, meta commentary, labels, quoted wrappers, "
        "or phrases like 'We need to', 'Let's craft', or 'Here is the prompt'. No markdown and no bullet list."
    )
    user_prompt = (
        f"Project title: {project_title or 'Untitled Project'}\n"
        f"Project description: {project_description or 'No extra project description provided.'}\n"
        f"Target device: {device_type}\n"
        f"User brief: {prompt}\n\n"
        "Rewrite this into a single high-clarity Stitch screen prompt."
    )

    payload = None
    for attempt in range(3):
        try:
            response = requests.post(
                f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://jaytibirthday.in",
                    "X-Title": "Tan Studio",
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "max_tokens": 400,
                },
                timeout=settings.OPENROUTER_TIMEOUT_SEC,
            )
            if response.status_code in {429, 503} and attempt < 2:
                logger.warning(
                    "OpenRouter temporary upstream issue for Tan Studio model %s (status %s, attempt %s)",
                    settings.OPENROUTER_MODEL,
                    response.status_code,
                    attempt + 1,
                )
                time.sleep(attempt + 1)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except requests.RequestException as exc:
            logger.warning("OpenRouter prompt optimization failed: %s", exc)
            if attempt < 2:
                time.sleep(attempt + 1)
                continue
            raise OpenRouterAPIError("OpenRouter prompt optimization failed. Please try again in a moment.") from exc
        except ValueError as exc:
            logger.warning("OpenRouter returned invalid JSON for Tan Studio")
            raise OpenRouterAPIError("OpenRouter returned an unreadable response.") from exc

    if payload is None:
        raise OpenRouterAPIError("OpenRouter prompt optimization did not return a usable response.")

    if payload.get("error"):
        message = payload["error"].get("message", "Unknown OpenRouter error.")
        raise OpenRouterAPIError(message)

    content = ""
    if payload.get("choices"):
        content = (payload["choices"][0].get("message", {}) or {}).get("content", "")
    optimized_prompt = _clean_optimized_prompt(content)
    if not optimized_prompt:
        raise OpenRouterAPIError("OpenRouter returned an empty prompt optimization result.")

    return {
        "prompt": optimized_prompt,
        "provider": "openrouter",
        "model": settings.OPENROUTER_MODEL,
    }
