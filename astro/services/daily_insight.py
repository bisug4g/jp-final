"""
Daily Astrological Insight Service
"""
from django.utils import timezone
from astro.models import BirthChart, PlanetPosition
import swisseph as swe
from datetime import datetime


class DailyAstroService:
    """Generate daily astrological insights"""
    
    HOUSE_MEANINGS = {
        1: "self and personality",
        2: "wealth and resources",
        3: "communication and siblings",
        4: "home and mother",
        5: "creativity and children",
        6: "health and service",
        7: "partnerships and marriage",
        8: "transformation and mysteries",
        9: "wisdom and fortune",
        10: "career and status",
        11: "gains and friendships",
        12: "spirituality and liberation",
    }
    
    PLANET_KEYWORDS = {
        'sun': 'vitality and confidence',
        'moon': 'emotions and intuition',
        'mars': 'action and courage',
        'mercury': 'communication and intellect',
        'jupiter': 'growth and wisdom',
        'venus': 'love and creativity',
        'saturn': 'discipline and responsibility',
    }
    
    def __init__(self, user):
        self.user = user
        self.today = timezone.now()
    
    def get_daily_insight(self):
        """Get today's astrological insight"""
        try:
            birth_chart = BirthChart.objects.get(user=self.user)
        except BirthChart.DoesNotExist:
            return {
                'has_chart': False,
                'message': 'Complete your birth chart to see daily insights.'
            }
        
        # Get current planetary transits
        transit_insights = self._get_transit_insights(birth_chart)
        
        if transit_insights:
            return {
                'has_chart': True,
                'insight': transit_insights['message'],
                'planet': transit_insights['planet'],
                'house': transit_insights['house'],
            }
        
        # Fallback to natal chart insight
        return self._get_natal_insight(birth_chart)
    
    def _get_transit_insights(self, birth_chart):
        """Get insights from current planetary transits"""
        try:
            # Calculate current planetary positions
            jd = swe.julday(self.today.year, self.today.month, self.today.day, 12.0)
            
            # Check Moon transit (changes daily)
            moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
            moon_house = self._get_house_from_degree(moon_pos, birth_chart)
            
            house_meaning = self.HOUSE_MEANINGS.get(moon_house, "your life")
            
            messages = [
                f"The Moon transits your {self._ordinal(moon_house)} house today, highlighting {house_meaning}. A good day for emotional awareness.",
                f"Today's Moon in your {self._ordinal(moon_house)} house brings focus to {house_meaning}. Trust your intuition.",
                f"With the Moon in your {self._ordinal(moon_house)} house, pay attention to {house_meaning}. Your feelings guide you.",
            ]
            
            import random
            return {
                'planet': 'Moon',
                'house': moon_house,
                'message': random.choice(messages),
            }
            
        except Exception as e:
            print(f"Transit calculation error: {e}")
            return None
    
    def _get_natal_insight(self, birth_chart):
        """Get insight from natal chart"""
        # Get strongest planet in chart
        planets = PlanetPosition.objects.filter(birth_chart=birth_chart)
        
        if not planets:
            return {
                'has_chart': True,
                'insight': 'Your birth chart holds wisdom. Explore the Astro section for detailed insights.',
            }
        
        # Simple: pick a planet and its house
        import random
        planet = random.choice(planets)
        
        planet_keyword = self.PLANET_KEYWORDS.get(planet.planet, 'energy')
        house_meaning = self.HOUSE_MEANINGS.get(planet.house, 'your life')
        
        return {
            'has_chart': True,
            'insight': f"Your natal {planet.planet.title()} in the {self._ordinal(planet.house)} house influences {house_meaning}. Embrace your {planet_keyword} today.",
            'planet': planet.planet.title(),
            'house': planet.house,
        }
    
    def _get_house_from_degree(self, degree, birth_chart):
        """Calculate which house a degree falls into"""
        # Simplified: divide 360 degrees into 12 houses
        house = int(degree / 30) + 1
        return house if house <= 12 else 1
    
    def _ordinal(self, n):
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"


def get_daily_astro_insight(user):
    """Main function to get daily astro insight"""
    service = DailyAstroService(user)
    return service.get_daily_insight()
