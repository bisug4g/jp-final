from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import TangredProject, TangredScreen, TangredSession, TangredSessionPhoto
from .services.agent import (
    TangredAgentConfigurationError,
    TangredAgentError,
    run_tangred_agent,
    tangred_agent_is_configured,
)
from .services.private_media import read_session_photo, save_session_photo, tangred_private_media_backend
from .services.openrouter import (
    OpenRouterAPIError,
    OpenRouterConfigurationError,
    openrouter_is_configured,
    optimize_tan_studio_prompt,
)
from .services.stitch import (
    StitchAPIError,
    StitchConfigurationError,
    create_project,
    extract_primary_output,
    generate_screen_from_text,
    get_screen,
    list_projects,
    stitch_is_configured,
    stitch_project_id,
    stitch_screen_id,
)


def _sync_remote_projects(user):
    if not stitch_is_configured():
        return

    try:
        for remote in list_projects():
            name = remote.get("name", "")
            if not name.startswith("projects/"):
                continue
            TangredProject.objects.update_or_create(
                stitch_project_id=stitch_project_id(name),
                defaults={
                    "user": user,
                    "title": remote.get("title") or "Untitled Stitch Project",
                    "last_synced_at": timezone.now(),
                },
            )
    except Exception:
        # Both Tangred and Tan Studio should remain usable even if Stitch sync is temporarily down.
        pass


def _studio_status_counts(projects):
    total_screens = sum(project.screens.count() for project in projects)
    return {
        "project_count": len(projects),
        "screen_count": total_screens,
        "configured": stitch_is_configured(),
    }


def _tangred_status_counts(sessions):
    ready_sessions = sum(1 for session in sessions if session.status == "READY")
    total_photos = sum(session.photo_count for session in sessions)
    return {
        "session_count": len(sessions),
        "ready_count": ready_sessions,
        "photo_count": total_photos,
    }


def _save_generated_screen(
    project,
    prompt,
    optimized_prompt,
    device_type,
    model_id,
    optimizer_provider,
    optimizer_model,
    generation,
):
    parsed = extract_primary_output(generation)
    screen = parsed.get("screen") or {}
    screenshot = screen.get("screenshot") or {}
    html_code = screen.get("htmlCode") or {}
    screen_name = screen.get("name", "")
    title = screen.get("title") or "Generated Screen"
    metadata = screen.get("screenMetadata") or {}

    return TangredScreen.objects.create(
        project=project,
        title=title,
        prompt=prompt,
        optimized_prompt=optimized_prompt,
        device_type=device_type,
        model_id=model_id,
        prompt_optimizer_provider=optimizer_provider,
        prompt_optimizer_model=optimizer_model,
        stitch_session_id=parsed.get("session_id", ""),
        stitch_screen_name=screen_name,
        stitch_screen_id=stitch_screen_id(screen_name) if screen_name else "",
        screenshot_url=screenshot.get("downloadUrl", ""),
        html_url=html_code.get("downloadUrl", ""),
        summary=parsed.get("summary", ""),
        suggestions=parsed.get("suggestions", []),
        status=metadata.get("status", "UNKNOWN"),
        raw_response=parsed.get("raw_response", {}),
    )


def _create_styleboard(session: TangredSession) -> tuple[TangredProject | None, TangredScreen | None]:
    if not stitch_is_configured() or not session.visualization_prompt:
        return None, None

    project = TangredProject.objects.filter(
        user=session.user,
        title=f"Tangred Styleboard - {session.title}",
    ).first()
    if project is None:
        remote = create_project(f"Tangred Styleboard - {session.title}")
        project = TangredProject.objects.create(
            user=session.user,
            title=remote.get("title") or f"Tangred Styleboard - {session.title}",
            description=f"Tangred wardrobe board for {session.title}",
            stitch_project_id=stitch_project_id(remote.get("name", "")),
            last_synced_at=timezone.now(),
        )

    styleboard_prompt = (
        "Create a polished mobile wardrobe AI result screen for Tangred. "
        "The screen should feel like a premium personal stylist dashboard with a hero outfit visualization panel, "
        "style identity, color story chips, wardrobe blueprint cards, leather accessory focus, and confident editorial typography. "
        f"Use this recommendation as the design basis: {session.visualization_prompt}"
    )
    generation = generate_screen_from_text(
        project.stitch_project_id,
        styleboard_prompt,
        device_type="MOBILE",
        model_id="GEMINI_3_FLASH",
    )
    screen = _save_generated_screen(
        project,
        styleboard_prompt,
        styleboard_prompt,
        "MOBILE",
        "GEMINI_3_FLASH",
        "tangred-agent",
        "tangred-styleboard",
        generation,
    )
    project.last_synced_at = timezone.now()
    project.save(update_fields=["last_synced_at", "modified_at"])
    return project, screen


@login_required
def tangred_home(request):
    sessions = list(
        TangredSession.objects.filter(user=request.user)
        .prefetch_related("photos")
        .select_related("styleboard_screen")
    )
    context = {
        "sessions": sessions,
        "stats": _tangred_status_counts(sessions),
        "agent_ready": tangred_agent_is_configured(),
        "stitch_ready": stitch_is_configured(),
        "photo_storage_backend": tangred_private_media_backend(),
    }
    return render(request, "tangred/tangred_home.html", context)


@login_required
@require_POST
def create_session_view(request):
    title = request.POST.get("title", "").strip()
    if not title:
        messages.error(request, "A session title helps Tangred organize the wardrobe brief.")
        return redirect("tangred_home")

    session = TangredSession.objects.create(
        user=request.user,
        title=title,
        occasion=request.POST.get("occasion", "").strip(),
        body_frame=request.POST.get("body_frame", "").strip(),
        skin_tone=request.POST.get("skin_tone", "").strip(),
        preferred_palette=request.POST.get("preferred_palette", "").strip(),
        avoid_palette=request.POST.get("avoid_palette", "").strip(),
        style_goal=request.POST.get("style_goal", "").strip(),
        wardrobe_notes=request.POST.get("wardrobe_notes", "").strip(),
    )
    for photo in request.FILES.getlist("photos"):
        saved = save_session_photo(uploaded_file=photo, session=session)
        TangredSessionPhoto.objects.create(
            session=session,
            image=saved["image_name"],
            storage_backend=saved["backend"],
            storage_path=saved["storage_path"],
            original_name=saved["original_name"],
            content_type=saved["content_type"],
            size_bytes=saved["size_bytes"],
            binary_content=saved["binary_content"],
        )

    messages.success(request, "Tangred session created. Uploads are saved inside the app and ready for analysis.")
    return redirect("tangred_session_detail", pk=session.pk)


@login_required
def session_detail(request, pk):
    session = get_object_or_404(
        TangredSession.objects.select_related("styleboard_screen", "styleboard_project").prefetch_related("photos"),
        pk=pk,
        user=request.user,
    )
    context = {
        "session": session,
        "agent_ready": tangred_agent_is_configured(),
        "stitch_ready": stitch_is_configured(),
        "photo_storage_backend": tangred_private_media_backend(),
    }
    return render(request, "tangred/session_detail.html", context)


@login_required
def session_photo_view(request, pk):
    photo = get_object_or_404(
        TangredSessionPhoto.objects.select_related("session"),
        pk=pk,
        session__user=request.user,
    )
    payload = read_session_photo(photo)
    response = HttpResponse(payload, content_type=photo.content_type or "application/octet-stream")
    response["Content-Length"] = str(photo.size_bytes or len(payload))
    response["Cache-Control"] = "private, max-age=300"
    if photo.original_name:
        response["Content-Disposition"] = f'inline; filename="{photo.original_name}"'
    return response


@login_required
@require_POST
def run_session_view(request, pk):
    session = get_object_or_404(TangredSession.objects.prefetch_related("photos"), pk=pk, user=request.user)
    if session.photo_count == 0:
        messages.error(request, "Add at least one reference photo before running Tangred.")
        return redirect("tangred_session_detail", pk=session.pk)

    try:
        session.status = "PROCESSING"
        session.save(update_fields=["status", "modified_at"])

        result = run_tangred_agent(session, session.photo_count)
        session.style_identity = result.get("style_identity", "")
        session.body_summary = result.get("body_summary", "")
        session.outfit_direction = result.get("outfit_direction", "")
        session.wardrobe_blueprint = result.get("wardrobe_blueprint", [])
        session.accessory_focus = result.get("accessory_focus", "")
        session.color_story = result.get("color_story", "")
        session.confidence_notes = result.get("confidence_notes", "")
        session.visualization_prompt = result.get("visualization_prompt", "")
        session.openrouter_provider = result.get("provider", "openrouter")
        session.openrouter_model = result.get("model", "")
        session.raw_agent_response = result.get("raw_response", {})
        session.status = "READY"

        try:
            project, screen = _create_styleboard(session)
            if project and screen:
                session.styleboard_project = project
                session.styleboard_screen = screen
        except (StitchConfigurationError, StitchAPIError) as exc:
            messages.warning(request, f"Tangred analysis is saved, but the Tan Studio styleboard could not be generated: {exc}")

        session.save()
        messages.success(request, "Tangred finished the wardrobe analysis and saved the result in-app.")
    except (TangredAgentConfigurationError, TangredAgentError) as exc:
        session.status = "ERROR"
        session.save(update_fields=["status", "modified_at"])
        messages.error(request, str(exc))

    return redirect("tangred_session_detail", pk=session.pk)


@login_required
def studio_home(request):
    _sync_remote_projects(request.user)
    projects = list(TangredProject.objects.filter(user=request.user).prefetch_related("screens"))
    context = {
        "projects": projects,
        "stats": _studio_status_counts(projects),
        "model_choices": TangredScreen.MODEL_CHOICES,
        "device_choices": TangredScreen.DEVICE_CHOICES,
        "stitch_ready": stitch_is_configured(),
        "prompt_ai_ready": openrouter_is_configured(),
    }
    return render(request, "tangred/studio_home.html", context)


@login_required
@require_POST
def create_project_view(request):
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    if not title:
        messages.error(request, "Project title is required.")
        return redirect("tan_studio_home")

    try:
        remote = create_project(title)
        name = remote.get("name", "")
        project = TangredProject.objects.create(
            user=request.user,
            title=remote.get("title") or title,
            description=description,
            stitch_project_id=stitch_project_id(name),
            last_synced_at=timezone.now(),
        )
        messages.success(request, "Tan Studio project created and connected to Stitch.")
        return redirect("tan_studio_project_detail", pk=project.pk)
    except (StitchConfigurationError, StitchAPIError) as exc:
        messages.error(request, str(exc))
        return redirect("tan_studio_home")


@login_required
def project_detail(request, pk):
    project = get_object_or_404(TangredProject, pk=pk, user=request.user)
    screens = project.screens.all()
    context = {
        "project": project,
        "screens": screens,
        "stitch_ready": stitch_is_configured(),
        "prompt_ai_ready": openrouter_is_configured(),
        "model_choices": TangredScreen.MODEL_CHOICES,
        "device_choices": TangredScreen.DEVICE_CHOICES,
    }
    return render(request, "tangred/project_detail.html", context)


@login_required
@require_POST
def generate_screen_view(request, pk):
    project = get_object_or_404(TangredProject, pk=pk, user=request.user)
    prompt = request.POST.get("prompt", "").strip()
    device_type = request.POST.get("device_type", "MOBILE")
    model_id = request.POST.get("model_id", "GEMINI_3_FLASH")
    if not prompt:
        messages.error(request, "Screen prompt is required.")
        return redirect("tan_studio_project_detail", pk=project.pk)

    try:
        optimization = optimize_tan_studio_prompt(
            project_title=project.title,
            project_description=project.description,
            prompt=prompt,
            device_type=device_type,
        )
        generation = generate_screen_from_text(
            project.stitch_project_id,
            optimization["prompt"],
            device_type=device_type,
            model_id=model_id,
        )
        screen = _save_generated_screen(
            project,
            prompt,
            optimization["prompt"],
            device_type,
            model_id,
            optimization["provider"],
            optimization["model"],
            generation,
        )
        project.last_synced_at = timezone.now()
        project.save(update_fields=["last_synced_at", "modified_at"])
        messages.success(request, "Screen generated successfully with OpenRouter-guided Stitch generation.")
        return redirect("tan_studio_screen_detail", pk=screen.pk)
    except (
        StitchConfigurationError,
        StitchAPIError,
        OpenRouterConfigurationError,
        OpenRouterAPIError,
    ) as exc:
        messages.error(request, str(exc))
        return redirect("tan_studio_project_detail", pk=project.pk)


@login_required
def screen_detail(request, pk):
    screen = get_object_or_404(TangredScreen.objects.select_related("project"), pk=pk, project__user=request.user)
    context = {
        "screen": screen,
        "project": screen.project,
    }
    return render(request, "tangred/screen_detail.html", context)


@login_required
@require_POST
def refresh_screen_view(request, pk):
    screen = get_object_or_404(TangredScreen.objects.select_related("project"), pk=pk, project__user=request.user)
    if not screen.stitch_screen_name or not screen.stitch_screen_id:
        messages.error(request, "This screen cannot be refreshed because Stitch did not return a persisted screen id.")
        return redirect("tan_studio_screen_detail", pk=screen.pk)

    try:
        remote = get_screen(
            name=screen.stitch_screen_name,
            project_id=screen.project.stitch_project_id,
            screen_id=screen.stitch_screen_id,
        )
        screenshot = remote.get("screenshot") or {}
        html_code = remote.get("htmlCode") or {}
        metadata = remote.get("screenMetadata") or {}
        screen.title = remote.get("title") or screen.title
        screen.screenshot_url = screenshot.get("downloadUrl", screen.screenshot_url)
        screen.html_url = html_code.get("downloadUrl", screen.html_url)
        screen.status = metadata.get("status", screen.status)
        screen.raw_response = remote
        screen.save()
        messages.success(request, "Screen refreshed from Stitch.")
    except (StitchConfigurationError, StitchAPIError) as exc:
        messages.error(request, str(exc))

    return redirect("tan_studio_screen_detail", pk=screen.pk)
