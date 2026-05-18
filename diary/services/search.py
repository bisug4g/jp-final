"""
Diary Search Service
"""
from django.db.models import Q
from diary.models import DiaryEntry


class DiarySearchService:
    """Search diary entries"""
    
    def __init__(self, user):
        self.user = user
    
    def search(self, query, filters=None):
        """
        Search diary entries
        
        Args:
            query: Search text
            filters: Dict with optional filters (mood, date_from, date_to)
        """
        if not query and not filters:
            return DiaryEntry.objects.filter(user=self.user).order_by('-entry_date')
        
        entries = DiaryEntry.objects.filter(user=self.user)
        
        # Text search
        if query:
            entries = entries.filter(
                Q(content__icontains=query) |
                Q(voice_transcript__icontains=query) |
                Q(handwriting_ocr_text__icontains=query) |
                Q(mood_note__icontains=query)
            )
        
        # Apply filters
        if filters:
            if filters.get('mood'):
                entries = entries.filter(mood=filters['mood'])
            
            if filters.get('date_from'):
                entries = entries.filter(entry_date__gte=filters['date_from'])
            
            if filters.get('date_to'):
                entries = entries.filter(entry_date__lte=filters['date_to'])
            
            if filters.get('input_method'):
                entries = entries.filter(input_method=filters['input_method'])
        
        return entries.order_by('-entry_date')
    
    def get_search_suggestions(self, query):
        """Get search suggestions based on partial query"""
        if len(query) < 2:
            return []
        
        # Find common words in diary entries
        entries = DiaryEntry.objects.filter(
            user=self.user,
            content__icontains=query
        )[:5]
        
        suggestions = []
        for entry in entries:
            # Extract words containing the query
            words = entry.content.split()
            matching_words = [w.strip('.,!?') for w in words if query.lower() in w.lower()]
            suggestions.extend(matching_words[:3])
        
        # Return unique suggestions
        return list(set(suggestions))[:10]


def search_diary(user, query, filters=None):
    """Main function to search diary"""
    service = DiarySearchService(user)
    return service.search(query, filters)
