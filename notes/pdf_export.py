from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from .models import Note
import html

@login_required
def export_notes_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor='#D4A5A5', spaceAfter=12)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor='#4A4A4A', spaceAfter=8)
    body_style = ParagraphStyle('CustomBody', parent=styles['BodyText'], fontSize=11, leading=14, textColor='#2C2C2C')
    
    story = []
    
    # Title page
    story.append(Paragraph("My Notes", title_style))
    story.append(Paragraph(f"Exported by {request.user.get_full_name() or request.user.username}", body_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Get all notes
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    
    for note in notes:
        story.append(Paragraph(html.escape(note.title or "Untitled"), heading_style))
        story.append(Paragraph(f"Created: {note.created_at.strftime('%B %d, %Y')}", body_style))
        
        if note.tags.exists():
            tags = ", ".join([tag.name for tag in note.tags.all()])
            story.append(Paragraph(f"Tags: {tags}", body_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        content = html.escape(note.content_plain or note.content)
        story.append(Paragraph(content, body_style))
        story.append(PageBreak())
    
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="my_notes.pdf"'
    return response
