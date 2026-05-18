from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Note, Tag, NoteFolder


@login_required
def note_list(request):
    """List all notes with search, filter, and folder support"""
    notes = Note.objects.filter(user=request.user).prefetch_related('tags')
    
    # Folder filter
    folder_id = request.GET.get('folder')
    current_folder = None
    if folder_id:
        current_folder = get_object_or_404(NoteFolder, id=folder_id, user=request.user)
        notes = notes.filter(folder=current_folder)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        notes = notes.filter(
            Q(title__icontains=query) | 
            Q(content_plain__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    # Tag filter
    tag_filter = request.GET.get('tag')
    if tag_filter:
        notes = notes.filter(tags__name=tag_filter)
    
    # Get all tags and folders for this user
    user_tags = Tag.objects.filter(notes__user=request.user).distinct()
    folders = NoteFolder.objects.filter(user=request.user)
    total_notes = Note.objects.filter(user=request.user).count()
    
    context = {
        'notes': notes,
        'tags': user_tags,
        'folders': folders,
        'total_notes': total_notes,
        'current_folder': current_folder,
        'query': query,
        'tag_filter': tag_filter,
    }
    return render(request, 'notes/note_list.html', context)


@login_required
def note_create(request):
    """Create a new note"""
    if request.method == 'POST':
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        tag_names = request.POST.get('tags', '').split(',')
        folder_id = request.POST.get('folder')
        
        note = Note.objects.create(
            user=request.user,
            title=title,
            content=content,
            folder_id=folder_id if folder_id else None,
        )
        
        # Process tags
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if tag_name:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
                note.tags.add(tag)
        
        # Track activity
        try:
            from core.services.activity_tracker import record_note_created
            record_note_created(request.user)
        except Exception:
            pass
        
        messages.success(request, 'Note created successfully.')
        return redirect('note_detail', pk=note.pk)
    
    # Get folders for dropdown
    folders = NoteFolder.objects.filter(user=request.user)
    return render(request, 'notes/note_form.html', {'folders': folders})


@login_required
def note_detail(request, pk):
    """View note details"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    return render(request, 'notes/note_detail.html', {'note': note})


@login_required
def note_edit(request, pk):
    """Edit an existing note"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    if request.method == 'POST':
        note.title = request.POST.get('title', '')
        note.content = request.POST.get('content', '')
        note.folder_id = request.POST.get('folder') or None
        
        # Update tags
        note.tags.clear()
        tag_names = request.POST.get('tags', '').split(',')
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if tag_name:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
                note.tags.add(tag)
        
        note.save()
        messages.success(request, 'Note updated successfully.')
        return redirect('note_detail', pk=note.pk)
    
    # Get folders for dropdown
    folders = NoteFolder.objects.filter(user=request.user)
    context = {
        'note': note,
        'folders': folders,
        'tags': ', '.join([t.name for t in note.tags.all()]),
    }
    return render(request, 'notes/note_form.html', context)


@login_required
def note_delete(request, pk):
    """Delete a note"""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully.')
        return redirect('note_list')
    
    return render(request, 'notes/note_confirm_delete.html', {'note': note})


@login_required
def folder_create(request):
    """Create a new folder"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '📁')
        color = request.POST.get('color', '#E3F2FD')
        
        if name:
            NoteFolder.objects.create(
                user=request.user,
                name=name,
                icon=icon,
                color=color,
            )
            messages.success(request, f'Folder "{name}" created successfully.')
        else:
            messages.error(request, 'Folder name is required.')
    
    return redirect('note_list')


@login_required
def folder_delete(request, pk):
    """Delete a folder"""
    folder = get_object_or_404(NoteFolder, pk=pk, user=request.user)
    
    if request.method == 'POST':
        name = folder.name
        # Notes in this folder will become folderless (null)
        folder.delete()
        messages.success(request, f'Folder "{name}" deleted.')
        return redirect('note_list')
    
    return render(request, 'notes/folder_confirm_delete.html', {'folder': folder})
