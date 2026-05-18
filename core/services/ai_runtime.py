import logging
from dataclasses import dataclass
from functools import lru_cache

from django.conf import settings
import requests

logger = logging.getLogger("core")


@dataclass(frozen=True)
class AICompletion:
    text: str
    provider: str


class AIServiceError(RuntimeError):
    """Base exception for AI runtime failures."""


class AIConfigurationError(AIServiceError):
    """Raised when no AI provider has been configured."""


class AIProviderError(AIServiceError):
    """Raised when configured providers fail to return a response."""


def _has_value(value):
    return bool(value and str(value).strip())


def available_providers():
    providers = []
    if _has_value(getattr(settings, "EMERGENT_API_KEY", "")):
        providers.append("emergent")
    if _has_value(getattr(settings, "GITHUB_MODELS_TOKEN", "")):
        providers.append("github-models")
    if _has_value(getattr(settings, "GEMINI_API_KEY", "")):
        providers.append("gemini")
    if _has_value(getattr(settings, "FIREBASE_PROJECT_ID", "")) and all(
        _has_value(value)
        for value in [
            getattr(settings, "FIREBASE_PRIVATE_KEY_ID", ""),
            getattr(settings, "FIREBASE_PRIVATE_KEY", ""),
            getattr(settings, "FIREBASE_CLIENT_EMAIL", ""),
            getattr(settings, "FIREBASE_CLIENT_ID", ""),
            getattr(settings, "FIREBASE_CLIENT_CERT_URL", ""),
        ]
    ):
        providers.append("vertex")
    return providers


def ai_is_configured():
    return bool(available_providers())


@lru_cache(maxsize=1)
def _get_emergent_client():
    if not _has_value(getattr(settings, "EMERGENT_API_KEY", "")):
        return None

    from openai import OpenAI

    return OpenAI(
        api_key=settings.EMERGENT_API_KEY,
        base_url=settings.EMERGENT_BASE_URL,
    )


@lru_cache(maxsize=1)
def _get_gemini_client():
    if not _has_value(getattr(settings, "GEMINI_API_KEY", "")):
        return None

    from google import genai

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _firebase_service_account_info():
    return {
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY,
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "auth_uri": settings.FIREBASE_AUTH_URI,
        "token_uri": settings.FIREBASE_TOKEN_URI,
        "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_CERT_URL,
        "client_x509_cert_url": settings.FIREBASE_CLIENT_CERT_URL,
    }


@lru_cache(maxsize=1)
def _get_vertex_client():
    if "vertex" not in available_providers():
        return None

    from google import genai
    from google.oauth2 import service_account

    scopes = [
        "https://www.googleapis.com/auth/generative-language",
        "https://www.googleapis.com/auth/cloud-platform",
    ]
    credentials = service_account.Credentials.from_service_account_info(
        _firebase_service_account_info(),
        scopes=scopes,
    )

    return genai.Client(
        vertexai=True,
        project=settings.FIREBASE_PROJECT_ID,
        location=settings.VERTEX_AI_LOCATION,
        credentials=credentials,
    )


def _extract_text(value):
    if not value:
        return ""
    return value.strip()


def _gemini_prompt(system_instruction, prompt, history, user_input):
    parts = []
    if prompt:
        parts.append(prompt.strip())

    if history:
        transcript = []
        for message in history:
            role = message.get("role", "user")
            content = (message.get("content") or "").strip()
            if not content:
                continue
            speaker = "User" if role == "user" else "Assistant"
            transcript.append(f"{speaker}: {content}")
        if transcript:
            parts.append("Conversation so far:\n" + "\n".join(transcript))

    if user_input:
        parts.append(f"User: {user_input.strip()}")
        parts.append("Assistant:")

    return "\n\n".join(parts).strip(), system_instruction or None


def _run_emergent(messages, max_tokens, temperature, top_p):
    client = _get_emergent_client()
    if client is None:
        return None

    response = client.chat.completions.create(
        model=settings.EMERGENT_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )
    content = None
    if response.choices:
        content = response.choices[0].message.content
    text = _extract_text(content)
    if not text:
        raise AIProviderError("Emergent returned an empty response.")
    return AICompletion(text=text, provider="emergent")


def _run_github_models(messages, max_tokens, temperature, top_p):
    if not _has_value(getattr(settings, "GITHUB_MODELS_TOKEN", "")):
        return None

    base_url = settings.GITHUB_MODELS_BASE_URL.rstrip("/")
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.GITHUB_MODELS_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.GITHUB_MODELS_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    content = None
    if payload.get("choices"):
        content = payload["choices"][0].get("message", {}).get("content")
    text = _extract_text(content)
    if not text:
        raise AIProviderError("GitHub Models returned an empty response.")
    return AICompletion(text=text, provider="github-models")


def _run_gemini(system_instruction, prompt, history, user_input, max_tokens, temperature, top_p):
    client = _get_gemini_client()
    if client is None:
        return None

    from google.genai import types

    contents, system_prompt = _gemini_prompt(system_instruction, prompt, history, user_input)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
        ),
    )
    text = _extract_text(getattr(response, "text", None))
    if not text:
        raise AIProviderError("Gemini returned an empty response.")
    return AICompletion(text=text, provider="gemini")


def _run_vertex_gemini(system_instruction, prompt, history, user_input, max_tokens, temperature, top_p):
    client = _get_vertex_client()
    if client is None:
        return None

    from google.genai import types

    contents, system_prompt = _gemini_prompt(system_instruction, prompt, history, user_input)
    response = client.models.generate_content(
        model=settings.VERTEX_GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
        ),
    )
    text = _extract_text(getattr(response, "text", None))
    if not text:
        raise AIProviderError("Vertex Gemini returned an empty response.")
    return AICompletion(text=text, provider="vertex")


def _run_with_fallback(system_instruction, prompt, history, user_input, max_tokens, temperature, top_p):
    configured = available_providers()
    if not configured:
        raise AIConfigurationError(
            "AI is unavailable because no production provider is configured."
        )

    failures = []

    if "emergent" in configured:
        try:
            completion = _run_emergent(
                messages=[
                    *([{"role": "system", "content": system_instruction}] if system_instruction else []),
                    *(history or []),
                    *([{"role": "user", "content": user_input}] if user_input else [{"role": "user", "content": prompt}]),
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            if completion:
                return completion
        except Exception as exc:
            logger.warning("Emergent AI request failed: %s", exc)
            failures.append(f"Emergent: {exc}")

    if "github-models" in configured:
        try:
            completion = _run_github_models(
                messages=[
                    *([{"role": "system", "content": system_instruction}] if system_instruction else []),
                    *(history or []),
                    *([{"role": "user", "content": user_input}] if user_input else [{"role": "user", "content": prompt}]),
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            if completion:
                return completion
        except Exception as exc:
            logger.warning("GitHub Models request failed: %s", exc)
            failures.append(f"GitHub Models: {exc}")

    if "gemini" in configured:
        try:
            completion = _run_gemini(
                system_instruction=system_instruction,
                prompt=prompt,
                history=history,
                user_input=user_input,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            if completion:
                return completion
        except Exception as exc:
            logger.warning("Gemini AI request failed: %s", exc)
            failures.append(f"Gemini: {exc}")

    if "vertex" in configured:
        try:
            completion = _run_vertex_gemini(
                system_instruction=system_instruction,
                prompt=prompt,
                history=history,
                user_input=user_input,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            if completion:
                return completion
        except Exception as exc:
            logger.warning("Vertex AI request failed: %s", exc)
            failures.append(f"Vertex: {exc}")

    raise AIProviderError(" | ".join(failures))


def generate_prompt_response(
    prompt,
    *,
    system_instruction=None,
    max_tokens=300,
    temperature=0.7,
    top_p=0.9,
):
    return _run_with_fallback(
        system_instruction=system_instruction,
        prompt=prompt,
        history=None,
        user_input=None,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )


def generate_chat_response(
    *,
    system_instruction,
    user_input,
    history=None,
    max_tokens=300,
    temperature=0.7,
    top_p=0.9,
):
    return _run_with_fallback(
        system_instruction=system_instruction,
        prompt=None,
        history=history,
        user_input=user_input,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )
