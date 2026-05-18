import json
import logging
import re
import time

import requests
from django.conf import settings

logger = logging.getLogger("core")


class TangredAgentConfigurationError(RuntimeError):
    pass


class TangredAgentError(RuntimeError):
    pass


def tangred_agent_is_configured() -> bool:
    return bool(getattr(settings, "OPENROUTER_API_KEY", "").strip())


def _extract_json_block(text: str) -> dict:
    if not text:
        return {}

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _chat_completion(messages: list[dict], *, model: str, max_tokens: int = 1200) -> dict:
    payload = None
    for attempt in range(3):
        try:
            response = requests.post(
                f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://jaytibirthday.in",
                    "X-Title": "Tangred",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "max_tokens": max_tokens,
                },
                timeout=settings.OPENROUTER_TIMEOUT_SEC,
            )
            if response.status_code in {429, 503} and attempt < 2:
                time.sleep(attempt + 1)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except requests.RequestException as exc:
            logger.warning("Tangred agent request failed: %s", exc)
            if attempt < 2:
                time.sleep(attempt + 1)
                continue
            raise TangredAgentError("Tangred AI request failed. Please try again in a moment.") from exc
        except ValueError as exc:
            raise TangredAgentError("Tangred AI returned an unreadable response.") from exc

    if payload is None:
        raise TangredAgentError("Tangred AI did not return a usable response.")
    if payload.get("error"):
        raise TangredAgentError(payload["error"].get("message", "Unknown Tangred AI error."))

    choice = ((payload.get("choices") or [{}])[0].get("message") or {})
    content = choice.get("content")
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    content = (content or choice.get("reasoning") or "").strip()
    if not content:
        raise TangredAgentError("Tangred AI returned an empty response.")

    return {
        "provider": payload.get("provider", "openrouter"),
        "model": payload.get("model", model),
        "text": content,
        "raw": payload,
    }


def run_tangred_agent(session, photo_count: int) -> dict:
    if not tangred_agent_is_configured():
        raise TangredAgentConfigurationError(
            "Tangred AI is unavailable because OPENROUTER_API_KEY is not configured."
        )

    model = getattr(settings, "OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    system_prompt = (
        "You are Tangred, an in-house agentic wardrobe AI. Build a sharp, practical, personalized styling result "
        "from the user's context. This is not e-commerce copy. It is a private wardrobe intelligence output. "
        "Use refined, direct language. Return JSON only. No markdown."
    )
    user_prompt = f"""
Create a Tangred wardrobe analysis JSON for this person.

Session title: {session.title}
Occasion: {session.occasion or "Not specified"}
Body frame: {session.body_frame or "Not specified"}
Skin tone: {session.skin_tone or "Not specified"}
Preferred palette: {session.preferred_palette or "Not specified"}
Avoid palette: {session.avoid_palette or "Not specified"}
Style goal: {session.style_goal or "Not specified"}
Wardrobe notes: {session.wardrobe_notes or "Not specified"}
Stored reference photos in app: {photo_count}

Return JSON:
{{
  "style_identity": "short title",
  "body_summary": "1 concise paragraph",
  "outfit_direction": "1 concise paragraph describing how the person should look dressed up",
  "wardrobe_blueprint": ["4 to 6 specific outfit or garment recommendations"],
  "accessory_focus": "recommended leather, bag, belt, watch, shoe or layering direction",
  "color_story": "how colors should be used",
  "confidence_notes": "fit, silhouette and grooming notes",
  "visualization_prompt": "rich visual prompt for generating a premium wardrobe styleboard screen",
  "summary": "2 sentence executive summary"
}}
"""
    result = _chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()},
        ],
        model=model,
    )
    parsed = _extract_json_block(result["text"])
    if not parsed:
        raise TangredAgentError("Tangred AI returned a response that could not be parsed into structured advice.")

    parsed["provider"] = "openrouter"
    parsed["model"] = result["model"]
    parsed["raw_response"] = result["raw"]
    return parsed
