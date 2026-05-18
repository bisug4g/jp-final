from django.db import models
from django.contrib.auth.models import User
import uuid


class BirthChart(models.Model):
    """Cached birth chart calculations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='birth_chart')
    
    # Birth data
    birth_date = models.DateField()
    birth_time = models.TimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    timezone = models.CharField(max_length=50)
    
    # Chart data (JSON)
    chart_data = models.JSONField()
    calculated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Birth Chart for {self.user.username}"


class PlanetPosition(models.Model):
    """Individual planet positions in houses"""
    PLANETS = [
        ('sun', 'Sun'),
        ('moon', 'Moon'),
        ('mars', 'Mars'),
        ('mercury', 'Mercury'),
        ('jupiter', 'Jupiter'),
        ('venus', 'Venus'),
        ('saturn', 'Saturn'),
        ('rahu', 'Rahu'),
        ('ketu', 'Ketu'),
    ]
    
    RASHIS = [
        ('aries', 'Aries (Mesha)'),
        ('taurus', 'Taurus (Vrishabha)'),
        ('gemini', 'Gemini (Mithuna)'),
        ('cancer', 'Cancer (Karka)'),
        ('leo', 'Leo (Simha)'),
        ('virgo', 'Virgo (Kanya)'),
        ('libra', 'Libra (Tula)'),
        ('scorpio', 'Scorpio (Vrishchika)'),
        ('sagittarius', 'Sagittarius (Dhanu)'),
        ('capricorn', 'Capricorn (Makara)'),
        ('aquarius', 'Aquarius (Kumbha)'),
        ('pisces', 'Pisces (Meena)'),
    ]
    
    birth_chart = models.ForeignKey(BirthChart, on_delete=models.CASCADE, related_name='planets')
    planet = models.CharField(max_length=10, choices=PLANETS)
    house = models.IntegerField()
    rashi = models.CharField(max_length=20, choices=RASHIS)
    degree = models.FloatField()
    nakshatra = models.CharField(max_length=50, blank=True)
    pada = models.IntegerField(null=True, blank=True)
    retrograde = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['house', 'planet']
    
    def __str__(self):
        return f"{self.planet} in House {self.house}"


class HouseDetail(models.Model):
    """Detailed house information"""
    birth_chart = models.ForeignKey(BirthChart, on_delete=models.CASCADE, related_name='houses')
    house_number = models.IntegerField()
    rashi = models.CharField(max_length=20, choices=PlanetPosition.RASHIS)
    lord = models.CharField(max_length=20, choices=PlanetPosition.PLANETS)
    strength_score = models.IntegerField(default=0)  # 0-36 or 0-100
    
    class Meta:
        ordering = ['house_number']
    
    def __str__(self):
        return f"House {self.house_number}"


class Prediction(models.Model):
    """90-day forward predictions"""
    PERIOD_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    FOCUS_AREAS = [
        ('career', 'Career'),
        ('relationships', 'Relationships'),
        ('health', 'Health'),
        ('finance', 'Finance'),
        ('general', 'General'),
    ]
    
    birth_chart = models.ForeignKey(BirthChart, on_delete=models.CASCADE, related_name='predictions')
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    focus_area = models.CharField(max_length=20, choices=FOCUS_AREAS)
    
    description = models.TextField()
    recommendation = models.TextField()
    intensity = models.CharField(max_length=20, choices=[
        ('favorable', 'Favorable'),
        ('neutral', 'Neutral'),
        ('challenging', 'Challenging'),
    ])
    
    class Meta:
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.period_type} prediction for {self.focus_area}"
