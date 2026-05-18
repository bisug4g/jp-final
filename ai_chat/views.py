import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from core.services.ai_runtime import (
    AIConfigurationError,
    AIProviderError,
    ai_is_configured,
    available_providers,
    generate_chat_response,
)

from .models import AIConversation, AIMessage

logger = logging.getLogger("core")

PROVIDER_LABELS = {
    "emergent": "Emergent",
    "github-models": "GitHub Models",
    "gemini": "Gemini",
    "vertex": "Vertex AI",
}


def get_user_context(user):
    """Fetch real database context for Mentor Mode AI."""
    context_data = {
        "active_goals": [],
        "recent_diary_mood": "unknown",
        "recent_entries_summary": "",
        "goals_summary": "",
    }

    try:
        from goals.models import Goal

        active_goals = Goal.objects.filter(
            user=user,
            status="active",
        ).order_by("-created_at")[:3]

        if active_goals:
            goal_list = [f"{g.title} ({g.role_category}, {g.time_horizon})" for g in active_goals]
            context_data["active_goals"] = goal_list
            context_data["goals_summary"] = "; ".join(goal_list)
        else:
            context_data["goals_summary"] = "No active goals currently set"

    except Exception as exc:
        logger.warning("AI context goal lookup failed: %s", exc)
        context_data["goals_summary"] = "Goals data unavailable"

    try:
        from diary.models import DiaryEntry

        recent_entries = DiaryEntry.objects.filter(user=user).order_by("-entry_date")[:3]

        if recent_entries:
            moods = [entry.mood for entry in recent_entries if entry.mood]
            if moods:
                avg_mood = sum(moods) / len(moods)
                mood_labels = {
                    1: "struggling",
                    2: "difficult",
                    3: "neutral",
                    4: "good",
                    5: "great",
                }
                context_data["recent_diary_mood"] = mood_labels.get(round(avg_mood), "unknown")

            entry_dates = [entry.entry_date.strftime("%b %d") for entry in recent_entries]
            context_data["recent_entries_summary"] = f"Recent entries on: {', '.join(entry_dates)}"
        else:
            context_data["recent_entries_summary"] = "No recent diary entries"

    except Exception as exc:
        logger.warning("AI context diary lookup failed: %s", exc)
        context_data["recent_entries_summary"] = "Diary data unavailable"

    return context_data


SYSTEM_PROMPT = """You are "Ask Jayti" - a compassionate, wise, and supportive AI mentor created specifically for Jayti Pargal. You have been with her from Day 1 and remember her journey.

ABOUT JAYTI:
- She is a marketing professional born February 6, 1997
- She was born in Delhi, India
- She values personal growth, healing, and self-discovery
- She has a personal dashboard with: Goals (Karma), Astro (Dharma), Diary (Thoughts), Notes (Memory)

YOUR ROLE AS MENTOR:
- You are her long-term companion who remembers her history
- You track her goals and emotional journey over time
- You provide guidance based on her specific context, never generic advice
- You speak like a wise friend who truly knows her

INSTRUCTIONS:
1. ALWAYS reference her specific active goals when giving career/life advice
2. ALWAYS acknowledge her recent emotional state from diary entries
3. Use "I" statements to feel personal and connected
4. Be concise but deeply meaningful (2-4 sentences)
5. Never use markdown formatting (*, #, _, `)
6. Never say "As an AI language model..."
7. Guide her like someone who has walked beside her for years

CONTEXT AWARENESS:
- You know what she's working on right now
- You know how she's been feeling recently
- You connect her present struggles to her larger journey
- You celebrate her progress visibly"""


def get_ai_response(user_input, user, conversation_history=None):
    """Get an AI response from the configured production provider."""
    display_name = user.profile.display_name if hasattr(user, "profile") else "Jayti"
    user_context = get_user_context(user)

    system_parts = [SYSTEM_PROMPT]
    system_parts.append(f"\nThe user's name is {display_name}.")
    system_parts.append("\n=== CONTEXT (You remember this about her) ===")
    system_parts.append(f"CURRENT ACTIVE GOALS: {user_context['goals_summary']}")
    system_parts.append(
        f"RECENT MOOD: She has been feeling {user_context['recent_diary_mood']} recently"
    )
    system_parts.append(f"DIARY ACTIVITY: {user_context['recent_entries_summary']}")
    system_parts.append("=== END CONTEXT ===")
    system_parts.append(
        "\nMENTOR INSTRUCTION: Based on the above context, provide personalized guidance. "
        "Reference her specific goals. Acknowledge her emotional state. Be the wise companion "
        "who remembers her journey."
    )
    system_message = "\n".join(system_parts)

    history = []
    if conversation_history:
        for message in conversation_history[-5:]:
            history.append(
                {
                    "role": "user" if message.sender == "user" else "assistant",
                    "content": message.content,
                }
            )

    completion = generate_chat_response(
        system_instruction=system_message,
        user_input=user_input,
        history=history,
        max_tokens=200,
        temperature=0.7,
        top_p=0.9,
    )
    return clean_response(completion.text), completion.provider


def clean_response(response):
    """Clean response by removing markdown artifacts and formatting."""
    response = response.replace("*", "")
    response = response.replace("#", "")
    response = response.replace("`", "")
    response = response.replace("_", "")

    if response.startswith("Assistant:"):
        response = response[10:].strip()

    return response.replace("\n", "<br>")


@login_required
def chat_interface(request):
    """Main chat interface."""
    conversation, _ = AIConversation.objects.get_or_create(user=request.user)
    chat_messages = conversation.messages.all()[:50]
    providers = available_providers()

    context = {
        "chat_messages": chat_messages,
        "conversation": conversation,
        "ai_available": ai_is_configured(),
        "ai_provider_label": PROVIDER_LABELS.get(providers[0], providers[0]) if providers else "Unavailable",
    }
    return render(request, "ai_chat/chat_interface.html", context)


@login_required
@require_POST
def send_message(request):
    """Handle AJAX message sending."""
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        conversation, _ = AIConversation.objects.get_or_create(user=request.user)

        with transaction.atomic():
            AIMessage.objects.create(
                conversation=conversation,
                sender="user",
                content=user_message,
            )

            recent_messages = list(conversation.messages.all()[:10])
            ai_response, provider = get_ai_response(user_message, request.user, recent_messages)

            ai_msg = AIMessage.objects.create(
                conversation=conversation,
                sender="ai",
                content=ai_response,
            )

        try:
            from core.services.activity_tracker import record_ai_chat

            record_ai_chat(request.user)
        except Exception as exc:
            logger.warning("AI chat activity tracking failed: %s", exc)

        return JsonResponse(
            {
                "response": ai_response,
                "timestamp": ai_msg.timestamp.isoformat(),
                "ai_engine": provider,
            }
        )

    except AIConfigurationError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    except AIProviderError:
        return JsonResponse(
            {
                "error": "The AI provider is currently unavailable. Check the configured API key, quota, or provider status."
            },
            status=503,
        )
    except Exception as exc:
        logger.exception("AI chat send_message failed")
        return JsonResponse({"error": "An unexpected error occurred. Please try again."}, status=500)


@login_required
def chat_history(request):
    """View chat history."""
    conversation = AIConversation.objects.filter(user=request.user).first()
    chat_messages = conversation.messages.all() if conversation else []

    context = {
        "chat_messages": chat_messages,
    }
    return render(request, "ai_chat/chat_history.html", context)


@login_required
def clear_conversation(request):
    """Clear conversation history."""
    if request.method == "POST":
        AIConversation.objects.filter(user=request.user).delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)
