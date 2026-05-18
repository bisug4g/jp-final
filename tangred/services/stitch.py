import json
import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger("core")


class StitchConfigurationError(RuntimeError):
    pass


class StitchAPIError(RuntimeError):
    pass


def stitch_is_configured() -> bool:
    return bool(getattr(settings, "STITCH_API_KEY", "").strip())


def _headers() -> dict[str, str]:
    if not stitch_is_configured():
        raise StitchConfigurationError("Stitch MCP is unavailable because STITCH_API_KEY is not configured.")
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.STITCH_API_KEY,
    }


def _parse_tool_result(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("isError"):
        message = ""
        for content in result.get("content", []):
            if content.get("type") == "text":
                message = content.get("text", "")
                break
        raise StitchAPIError(message or "Stitch MCP returned an unknown error.")

    if result.get("structuredContent"):
        return result["structuredContent"]

    for content in result.get("content", []):
        text = content.get("text")
        if not text:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}

    return {}


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments,
        },
    }
    try:
        response = requests.post(
            settings.STITCH_MCP_URL,
            headers=_headers(),
            json=payload,
            timeout=settings.STITCH_TIMEOUT_SEC,
        )
        response.raise_for_status()
        body = response.json()
    except requests.RequestException as exc:
        logger.warning("Stitch MCP request failed for tool %s: %s", name, exc)
        raise StitchAPIError("Stitch MCP request failed. Please try again in a moment.") from exc
    except ValueError as exc:
        logger.warning("Stitch MCP returned invalid JSON for tool %s", name)
        raise StitchAPIError("Stitch MCP returned an unreadable response.") from exc

    if "error" in body:
        raise StitchAPIError(body["error"].get("message", "Unknown Stitch MCP error."))
    return _parse_tool_result(body.get("result", {}))


def list_projects() -> list[dict[str, Any]]:
    payload = call_tool("list_projects", {})
    return payload.get("projects", [])


def create_project(title: str) -> dict[str, Any]:
    return call_tool("create_project", {"title": title})


def generate_screen_from_text(project_id: str, prompt: str, *, device_type: str, model_id: str) -> dict[str, Any]:
    return call_tool(
        "generate_screen_from_text",
        {
            "projectId": project_id,
            "prompt": prompt,
            "deviceType": device_type,
            "modelId": model_id,
        },
    )


def get_screen(name: str, project_id: str, screen_id: str) -> dict[str, Any]:
    return call_tool(
        "get_screen",
        {
            "name": name,
            "projectId": project_id,
            "screenId": screen_id,
        },
    )


def stitch_project_id(name: str) -> str:
    return name.split("/")[-1]


def stitch_screen_id(name: str) -> str:
    return name.split("/")[-1]


def extract_primary_output(generation: dict[str, Any]) -> dict[str, Any]:
    output_components = generation.get("outputComponents", [])
    first_screen = {}
    summary = ""
    suggestions = []

    for component in output_components:
        if not summary and component.get("text"):
            summary = component["text"]
        if component.get("suggestion"):
            suggestions.append(component["suggestion"])
        design = component.get("design")
        if design and design.get("screens") and not first_screen:
            first_screen = design["screens"][0]

    return {
        "session_id": generation.get("sessionId", ""),
        "project_id": generation.get("projectId", ""),
        "screen": first_screen,
        "summary": summary,
        "suggestions": suggestions,
        "raw_response": generation,
    }
