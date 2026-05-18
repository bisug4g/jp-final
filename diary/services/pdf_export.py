"""
PDF Export Service for Diary Entries
Requires: pip install reportlab
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from django.utils import timezone
from diary.models import DiaryEntry
from datetime import datetime


class DiaryPDFExporter:
    """Export diary entries to PDF"""
    
    def __init__(self, user):
        self.user = user
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='DiaryTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#FF69B4'),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        
        self.styles.add(ParagraphStyle(
            name='EntryDate',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=10,
        ))
        
        self.styles.add(ParagraphStyle(
            name='EntryContent',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=16,
            spaceAfter=20,
        ))
    
    def export_entries(self, start_date=None, end_date=None):
        """
        Export diary entries to PDF
        
        Args:
            start_date: Start date for export (optional)
            end_date: End date for export (optional)
        
        Returns:
            BytesIO buffer containing PDF
        """
        # Query entries
        entries = DiaryEntry.objects.filter(user=self.user)
        
        if start_date:
            entries = entries.filter(entry_date__gte=start_date)
        if end_date:
            entries = entries.filter(entry_date__lte=end_date)
        
        entries = entries.order_by('entry_date')
        
        # Create PDF
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        story = []
        
        # Title page
        story.append(Paragraph("My Diary", self.styles['DiaryTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        period_text = f"Exported on {timezone.now().strftime('%B %d, %Y')}"
        if start_date or end_date:
            period_text = f"Period: {start_date or 'Beginning'} to {end_date or 'Present'}"
        
        story.append(Paragraph(period_text, self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        story.append(PageBreak())
        
        # Add entries
        for entry in entries:
            # Date header
            date_str = entry.entry_date.strftime('%A, %B %d, %Y')
            story.append(Paragraph(date_str, self.styles['EntryDate']))
            
            # Mood indicator
            if entry.mood:
                mood_emoji = {1: '😔', 2: '😕', 3: '😐', 4: '🙂', 5: '😊'}
                mood_text = f"Mood: {mood_emoji.get(entry.mood, '')} {entry.mood}/5"
                if entry.mood_note:
                    mood_text += f" - {entry.mood_note}"
                story.append(Paragraph(mood_text, self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            # Content
            content = entry.content or entry.voice_transcript or entry.handwriting_ocr_text or "No content"
            # Clean HTML tags if present
            import re
            content = re.sub(r'<[^>]+>', '', content)
            
            story.append(Paragraph(content, self.styles['EntryContent']))
            story.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(story)
        
        # Reset buffer position
        self.buffer.seek(0)
        return self.buffer
    
    def export_single_entry(self, entry_id):
        """Export a single diary entry"""
        try:
            entry = DiaryEntry.objects.get(id=entry_id, user=self.user)
            return self.export_entries(
                start_date=entry.entry_date,
                end_date=entry.entry_date
            )
        except DiaryEntry.DoesNotExist:
            return None


def export_diary_pdf(user, start_date=None, end_date=None):
    """Main function to export diary to PDF"""
    exporter = DiaryPDFExporter(user)
    return exporter.export_entries(start_date, end_date)
