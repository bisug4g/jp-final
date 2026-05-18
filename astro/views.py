from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BirthChart, PlanetPosition, HouseDetail, Prediction
from datetime import datetime, timedelta
import math

# Try to import swisseph - make astrology optional if library fails
try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    swe = None
    SWISSEPH_AVAILABLE = False

# Jayti's birth data
JAYTI_BIRTH_DATA = {
    'year': 1997,
    'month': 2,
    'day': 6,
    'hour': 22,
    'minute': 30,
    'latitude': 28.61,
    'longitude': 77.21,
    'timezone': 'Asia/Kolkata',
    'location': 'Delhi, India',
}

# Vedic Astrology Constants
if SWISSEPH_AVAILABLE:
    PLANETS = {
        swe.SUN: ('sun', 'Sun', '☉'),
        swe.MOON: ('moon', 'Moon', '☽'),
        swe.MARS: ('mars', 'Mars', '♂'),
        swe.MERCURY: ('mercury', 'Mercury', '☿'),
        swe.JUPITER: ('jupiter', 'Jupiter', '♃'),
        swe.VENUS: ('venus', 'Venus', '♀'),
        swe.SATURN: ('saturn', 'Saturn', '♄'),
        swe.TRUE_NODE: ('rahu', 'Rahu', '☊'),
    }
else:
    PLANETS = {}

# Calculate Ketu position (opposite to Rahu)
def get_ketu_position(rahu_degree):
    """Ketu is always 180 degrees opposite to Rahu"""
    ketu_degree = (rahu_degree + 180) % 360
    return ketu_degree

RASHIS = [
    ('aries', 'Aries (Mesha)', 0, '♈'),
    ('taurus', 'Taurus (Vrishabha)', 30, '♉'),
    ('gemini', 'Gemini (Mithuna)', 60, '♊'),
    ('cancer', 'Cancer (Karka)', 90, '♋'),
    ('leo', 'Leo (Simha)', 120, '♌'),
    ('virgo', 'Virgo (Kanya)', 150, '♍'),
    ('libra', 'Libra (Tula)', 180, '♎'),
    ('scorpio', 'Scorpio (Vrishchika)', 210, '♏'),
    ('sagittarius', 'Sagittarius (Dhanu)', 240, '♐'),
    ('capricorn', 'Capricorn (Makara)', 270, '♑'),
    ('aquarius', 'Aquarius (Kumbha)', 300, '♒'),
    ('pisces', 'Pisces (Meena)', 330, '♓'),
]

NAKSHATRAS = [
    ('Ashwini', 0, 'Ketu'),
    ('Bharani', 13.33, 'Venus'),
    ('Krittika', 26.66, 'Sun'),
    ('Rohini', 40, 'Moon'),
    ('Mrigashira', 53.33, 'Mars'),
    ('Ardra', 66.66, 'Rahu'),
    ('Punarvasu', 80, 'Jupiter'),
    ('Pushya', 93.33, 'Saturn'),
    ('Ashlesha', 106.66, 'Mercury'),
    ('Magha', 120, 'Ketu'),
    ('Purva Phalguni', 133.33, 'Venus'),
    ('Uttara Phalguni', 146.66, 'Sun'),
    ('Hasta', 160, 'Moon'),
    ('Chitra', 173.33, 'Mars'),
    ('Swati', 186.66, 'Rahu'),
    ('Vishakha', 200, 'Jupiter'),
    ('Anuradha', 213.33, 'Saturn'),
    ('Jyeshtha', 226.66, 'Mercury'),
    ('Mula', 240, 'Ketu'),
    ('Purva Ashadha', 253.33, 'Venus'),
    ('Uttara Ashadha', 266.66, 'Sun'),
    ('Shravana', 280, 'Moon'),
    ('Dhanishta', 293.33, 'Mars'),
    ('Shatabhisha', 306.66, 'Rahu'),
    ('Purva Bhadrapada', 320, 'Jupiter'),
    ('Uttara Bhadrapada', 333.33, 'Saturn'),
    ('Revati', 346.66, 'Mercury'),
]

# Vimshottari Dasha Constants
DASHA_PERIODS = {
    'Ketu': 7,
    'Venus': 20,
    'Sun': 6,
    'Moon': 10,
    'Mars': 7,
    'Rahu': 18,
    'Jupiter': 16,
    'Saturn': 19,
    'Mercury': 17,
}

DASHA_SEQUENCE = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']

RASHI_INFO = {
    'aries': {'element': 'Fire', 'quality': 'Cardinal', 'symbol': '♈', 'lord': 'mars'},
    'taurus': {'element': 'Earth', 'quality': 'Fixed', 'symbol': '♉', 'lord': 'venus'},
    'gemini': {'element': 'Air', 'quality': 'Mutable', 'symbol': '♊', 'lord': 'mercury'},
    'cancer': {'element': 'Water', 'quality': 'Cardinal', 'symbol': '♋', 'lord': 'moon'},
    'leo': {'element': 'Fire', 'quality': 'Fixed', 'symbol': '♌', 'lord': 'sun'},
    'virgo': {'element': 'Earth', 'quality': 'Mutable', 'symbol': '♍', 'lord': 'mercury'},
    'libra': {'element': 'Air', 'quality': 'Cardinal', 'symbol': '♎', 'lord': 'venus'},
    'scorpio': {'element': 'Water', 'quality': 'Fixed', 'symbol': '♏', 'lord': 'mars'},
    'sagittarius': {'element': 'Fire', 'quality': 'Mutable', 'symbol': '♐', 'lord': 'jupiter'},
    'capricorn': {'element': 'Earth', 'quality': 'Cardinal', 'symbol': '♑', 'lord': 'saturn'},
    'aquarius': {'element': 'Air', 'quality': 'Fixed', 'symbol': '♒', 'lord': 'saturn'},
    'pisces': {'element': 'Water', 'quality': 'Mutable', 'symbol': '♓', 'lord': 'jupiter'},
}

PLANET_INFO = {
    'sun': {'symbol': '☉', 'represents': 'Soul, Authority, Career', 'element': 'Fire'},
    'moon': {'symbol': '☽', 'represents': 'Mind, Emotions, Mother', 'element': 'Water'},
    'mars': {'symbol': '♂', 'represents': 'Energy, Courage, Action', 'element': 'Fire'},
    'mercury': {'symbol': '☿', 'represents': 'Intellect, Communication', 'element': 'Earth'},
    'jupiter': {'symbol': '♃', 'represents': 'Wisdom, Prosperity, Growth', 'element': 'Ether'},
    'venus': {'symbol': '♀', 'represents': 'Love, Beauty, Relationships', 'element': 'Water'},
    'saturn': {'symbol': '♄', 'represents': 'Discipline, Responsibility, Patience', 'element': 'Air'},
    'rahu': {'symbol': '☊', 'represents': 'Ambition, Illusion, Foreign', 'element': 'Air'},
    'ketu': {'symbol': '☋', 'represents': 'Spirituality, Detachment', 'element': 'Fire'},
}


def calculate_julian_day(year, month, day, hour, minute, timezone_offset=5.5):
    """Calculate Julian Day Number for given date/time"""
    if not SWISSEPH_AVAILABLE:
        return 0
    decimal_hour = hour + minute / 60.0 - timezone_offset
    return swe.julday(year, month, day, decimal_hour)


def get_rashi_from_degree(degree):
    """Get rashi name from degree (0-360)"""
    degree = degree % 360
    for rashi_name, rashi_full, start_deg, symbol in RASHIS:
        if start_deg <= degree < start_deg + 30:
            return rashi_name, degree - start_deg
    return 'aries', degree


def get_nakshatra_from_degree(degree):
    """Get nakshatra name, pada, and lord from degree (0-360)"""
    degree = degree % 360
    for i, (name, start, lord) in enumerate(NAKSHATRAS):
        end = NAKSHATRAS[(i + 1) % 27][1] if i < 26 else 360
        if start <= degree < end or (i == 26 and degree >= start):
            nakshatra_degree = degree - start
            pada = int(nakshatra_degree / 3.33) + 1
            return name, min(pada, 4), lord
    return NAKSHATRAS[0][0], 1, NAKSHATRAS[0][2]


def calculate_houses(julian_day, latitude, longitude):
    """Calculate house cusps using Vedic Whole Sign Houses (Rashi-based)
    
    In Whole Sign Houses, each house is exactly 30° (one sign).
    House 1 starts at 0° of the Ascendant's sign.
    This is the traditional Vedic astrology method.
    """
    if not SWISSEPH_AVAILABLE:
        return [0] * 12
    
    # Get Ascendant (Lagna) - first house cusp in tropical
    houses = swe.houses_ex(julian_day, latitude, longitude, b'W')  # Whole sign
    ascendant_tropical = houses[0][0]  # Ascendant degree
    
    # Apply Ayanamsa to get Vedic position
    ayanamsa = swe.get_ayanamsa_ut(julian_day)
    ascendant_vedic = (ascendant_tropical - ayanamsa) % 360
    
    # Find the start of the Ascendant's sign (0° of that sign)
    # Each sign is 30°, so sign_start = floor(degree / 30) * 30
    ascendant_sign_start = (ascendant_vedic // 30) * 30
    
    # Create 12 house cusps - each house is exactly 30° (one sign)
    # House 1 starts at 0° of Ascendant's sign
    vedic_cusps = []
    for house_num in range(12):
        cusp = (ascendant_sign_start + (house_num * 30)) % 360
        vedic_cusps.append(cusp)
    
    return vedic_cusps


def calculate_planet_positions(julian_day):
    """Calculate all planet positions"""
    positions = {}
    
    if not SWISSEPH_AVAILABLE:
        return positions
    
    for planet_id, (name, full_name, symbol) in PLANETS.items():
        result = swe.calc_ut(julian_day, planet_id)
        degree = result[0][0]  # Longitude in degrees
        
        # Calculate Ayanamsa (Lahiri)
        ayanamsa = swe.get_ayanamsa_ut(julian_day)
        vedic_degree = (degree - ayanamsa) % 360
        
        rashi, degree_in_rashi = get_rashi_from_degree(vedic_degree)
        nakshatra, pada, nakshatra_lord = get_nakshatra_from_degree(vedic_degree)
        
        positions[name] = {
            'degree': round(vedic_degree, 2),
            'degree_in_rashi': round(degree_in_rashi, 2),
            'rashi': rashi,
            'nakshatra': nakshatra,
            'pada': pada,
            'symbol': symbol,
        }
    
    # Calculate Ketu
    if 'rahu' in positions:
        rahu_degree = positions['rahu']['degree']
        ketu_degree = get_ketu_position(rahu_degree)
        rashi, degree_in_rashi = get_rashi_from_degree(ketu_degree)
        nakshatra, pada, nakshatra_lord = get_nakshatra_from_degree(ketu_degree)
        
        positions['ketu'] = {
            'degree': round(ketu_degree, 2),
            'degree_in_rashi': round(degree_in_rashi, 2),
            'rashi': rashi,
            'nakshatra': nakshatra,
            'pada': pada,
            'symbol': '☋',
        }
    
    return positions


def assign_planets_to_houses(planet_positions, house_cusps):
    """Assign planets to houses using Vedic Whole Sign Houses (Rashi-based)
    
    In Whole Sign Houses:
    - Each house is exactly 30° (one sign)
    - House 1 = Ascendant's sign (all 30° of that sign)
    - A planet's house is determined by which sign it's in, not exact degree
    
    Example: If Ascendant is Virgo (150°-180°):
    - House 1 = Virgo (150°-180°)
    - House 2 = Libra (180°-210°)
    - Mars at 161.22° (Virgo) → House 1
    """
    if not SWISSEPH_AVAILABLE:
        return {}
    
    planet_houses = {}
    
    for planet_name, data in planet_positions.items():
        planet_degree = data['degree']
        
        # Find which sign the planet is in (0-11)
        # Each sign is 30°, so sign = floor(degree / 30)
        planet_sign = int(planet_degree // 30)
        
        # Find which sign is House 1
        # House 1 cusp is the start of the Ascendant's sign
        house_1_sign = int(house_cusps[0] // 30)
        
        # Calculate house number
        # House = (planet_sign - house_1_sign) mod 12 + 1
        house_num = ((planet_sign - house_1_sign) % 12) + 1
        planet_houses[planet_name] = house_num
    
    return planet_houses


def calculate_house_scores(planet_positions, planet_houses):
    """Calculate strength scores for each house"""
    scores = {}
    
    for house_num in range(1, 13):
        score = 15  # Base score
        
        for planet_name, house in planet_houses.items():
            if house == house_num:
                planet_degree = planet_positions[planet_name]['degree_in_rashi']
                
                # Planets in own sign or exalted get bonus
                rashi = planet_positions[planet_name]['rashi']
                planet_key = planet_name.lower()
                
                # Add base points for having a planet
                score += 5
                
                # Check for directional strength (dig bala)
                if planet_name in ['jupiter', 'mercury'] and house_num == 1:
                    score += 3
                elif planet_name == 'sun' and house_num == 10:
                    score += 3
                elif planet_name == 'moon' and house_num == 4:
                    score += 3
                elif planet_name == 'mars' and house_num == 10:
                    score += 3
                elif planet_name == 'saturn' and house_num == 7:
                    score += 3
                elif planet_name == 'venus' and house_num == 4:
                    score += 3
        
        scores[house_num] = min(score, 36)  # Cap at 36
    
    return scores


# ==================== VIMSHOTTARI DASHA CALCULATIONS ====================

def calculate_dasha_balance(birth_jd, moon_degree):
    """
    Calculate the Dasha balance at birth based on Moon's position.
    Returns which mahadasha lord is running at birth and how much is remaining.
    """
    # Find which nakshatra the Moon is in
    nakshatra_index = int(moon_degree / 13.3333) % 27
    nakshatra_name, start_deg, dasha_lord = NAKSHATRAS[nakshatra_index]
    
    # Calculate how much of the nakshatra has passed
    nakshatra_progress = (moon_degree - start_deg) / 13.3333
    
    # Total years for this dasha lord
    total_years = DASHA_PERIODS[dasha_lord]
    
    # Years already passed = progress * total years
    years_passed = nakshatra_progress * total_years
    
    # Years remaining
    years_remaining = total_years - years_passed
    
    return {
        'starting_lord': dasha_lord,
        'years_remaining': years_remaining,
        'years_passed': years_passed,
        'total_years': total_years,
        'nakshatra': nakshatra_name,
    }


def generate_vimshottari_dasha(birth_jd, moon_degree, birth_date):
    """
    Generate complete Vimshottari Dasha sequence from birth.
    Returns list of mahadashas with start/end dates.
    """
    dasha_balance = calculate_dasha_balance(birth_jd, moon_degree)
    
    # Find starting position in DASHA_SEQUENCE
    start_index = DASHA_SEQUENCE.index(dasha_balance['starting_lord'])
    
    dasha_periods = []
    current_date = birth_date
    
    # First mahadasha (partial)
    first_lord = dasha_balance['starting_lord']
    first_duration = dasha_balance['years_remaining']
    first_end = current_date + timedelta(days=int(first_duration * 365.25))
    
    dasha_periods.append({
        'lord': first_lord,
        'start_date': current_date,
        'end_date': first_end,
        'duration_years': first_duration,
        'is_running': False,  # Will be set later
    })
    
    current_date = first_end
    
    # Continue with full dashas
    next_index = (start_index + 1) % 9
    
    # Generate next 9 periods (full cycle from next lord)
    for _ in range(9):
        lord = DASHA_SEQUENCE[next_index]
        duration = DASHA_PERIODS[lord]
        end_date = current_date + timedelta(days=int(duration * 365.25))
        
        dasha_periods.append({
            'lord': lord,
            'start_date': current_date,
            'end_date': end_date,
            'duration_years': duration,
            'is_running': False,
        })
        
        current_date = end_date
        next_index = (next_index + 1) % 9
    
    return dasha_periods


def get_current_mahadasha(dasha_periods, current_date=None):
    """Find which mahadasha is currently running"""
    if current_date is None:
        current_date = datetime.now().date()
    
    for period in dasha_periods:
        if period['start_date'] <= current_date < period['end_date']:
            period['is_running'] = True
            return period
    
    return None


def get_dasha_interpretation(lord):
    """Get interpretation for a dasha lord"""
    interpretations = {
        'Sun': {
            'theme': 'Authority, Recognition, Career Growth',
            'focus': 'Professional advancement, leadership opportunities, government connections',
            'advice': 'Take charge of your career. Seek recognition for your work. Focus on long-term goals.',
            'challenges': 'Ego conflicts, health issues related to heart/eyes',
        },
        'Moon': {
            'theme': 'Emotions, Home, Public Connection',
            'focus': 'Emotional well-being, family matters, public image, creative pursuits',
            'advice': 'Nurture your emotional needs. Strengthen family bonds. Trust your intuition.',
            'challenges': 'Mood fluctuations, over-sensitivity, mother-related concerns',
        },
        'Mars': {
            'theme': 'Energy, Courage, Action',
            'focus': 'Initiating projects, physical vitality, competition, property matters',
            'advice': 'Channel your energy constructively. Take bold action. Stand up for yourself.',
            'challenges': 'Impatience, conflicts, accidents, inflammation',
        },
        'Rahu': {
            'theme': 'Ambition, Foreign Connections, Material Gains',
            'focus': 'Unconventional paths, technology, foreign affairs, sudden opportunities',
            'advice': 'Embrace change and innovation. Think outside the box. Manage desires wisely.',
            'challenges': 'Illusions, obsessions, foreign-related stress, health mysteries',
        },
        'Jupiter': {
            'theme': 'Wisdom, Expansion, Prosperity',
            'focus': 'Higher learning, spirituality, children, wealth growth, guidance',
            'advice': 'Seek knowledge and wisdom. Expand your horizons. Trust in abundance.',
            'challenges': 'Over-optimism, weight gain, excesses, philosophical conflicts',
        },
        'Saturn': {
            'theme': 'Discipline, Responsibility, Structure',
            'focus': 'Hard work, responsibility, long-term planning, maturity, service',
            'advice': 'Embrace discipline and patience. Do the hard work. Build lasting foundations.',
            'challenges': 'Delays, restrictions, health issues, heavy responsibilities',
        },
        'Mercury': {
            'theme': 'Communication, Intellect, Commerce',
            'focus': 'Learning, writing, business, communication skills, adaptability',
            'advice': 'Sharpen your communication. Pursue learning. Stay flexible and curious.',
            'challenges': 'Nervousness, overthinking, communication misunderstandings',
        },
        'Ketu': {
            'theme': 'Spirituality, Detachment, Past Lessons',
            'focus': 'Letting go, spiritual growth, introspection, liberation from attachments',
            'advice': 'Practice detachment from outcomes. Focus on spiritual growth. Release the past.',
            'challenges': 'Confusion, losses, isolation, sudden separations',
        },
        'Venus': {
            'theme': 'Love, Beauty, Pleasure, Relationships',
            'focus': 'Romantic relationships, creativity, luxury, artistic pursuits, comfort',
            'advice': 'Cultivate beauty and harmony in life. Nurture relationships. Enjoy pleasures mindfully.',
            'challenges': 'Over-indulgence, relationship issues, financial excesses',
        },
    }
    
    return interpretations.get(lord, {
        'theme': 'Personal Growth and Transformation',
        'focus': 'Self-discovery and life lessons',
        'advice': 'Stay mindful and present',
        'challenges': 'Unexpected changes',
    })


def calculate_antardasha(mahadasha_lord, mahadasha_start, mahadasha_end):
    """
    Calculate Antardasha (sub-periods) within a Mahadasha.
    Each mahadasha is divided into 9 antardashas in the same sequence.
    """
    antardashas = []
    mahadasha_duration = (mahadasha_end - mahadasha_start).days
    
    # Find starting position
    start_index = DASHA_SEQUENCE.index(mahadasha_lord)
    
    current_date = mahadasha_start
    
    for i in range(9):
        lord_index = (start_index + i) % 9
        lord = DASHA_SEQUENCE[lord_index]
        
        # Duration is proportional
        # Formula: (Antardasha Lord Years / 120) * Mahadasha Duration
        antardasha_years = DASHA_PERIODS[lord]
        duration_days = int((antardasha_years / 120) * mahadasha_duration)
        
        end_date = current_date + timedelta(days=duration_days)
        
        antardashas.append({
            'lord': lord,
            'start_date': current_date,
            'end_date': end_date,
            'duration_days': duration_days,
        })
        
        current_date = end_date
    
    return antardashas


# ==================== MAIN VIEWS ====================

def calculate_birth_chart():
    """Calculate complete birth chart for Jayti"""
    jd = calculate_julian_day(
        JAYTI_BIRTH_DATA['year'],
        JAYTI_BIRTH_DATA['month'],
        JAYTI_BIRTH_DATA['day'],
        JAYTI_BIRTH_DATA['hour'],
        JAYTI_BIRTH_DATA['minute']
    )
    
    # Calculate positions
    planet_positions = calculate_planet_positions(jd)
    
    # Calculate houses
    house_cusps = calculate_houses(jd, JAYTI_BIRTH_DATA['latitude'], JAYTI_BIRTH_DATA['longitude'])
    
    # Assign planets to houses
    planet_houses = assign_planets_to_houses(planet_positions, house_cusps)
    
    # Update planet positions with house info
    for planet_name, house in planet_houses.items():
        if planet_name in planet_positions:
            planet_positions[planet_name]['house'] = house
    
    # Determine ascendant (1st house cusp)
    ayanamsa = swe.get_ayanamsa_ut(jd) if SWISSEPH_AVAILABLE else 0
    ascendant_degree = (house_cusps[0] - ayanamsa) % 360
    ascendant_rashi, _ = get_rashi_from_degree(ascendant_degree)
    
    # Calculate house scores
    house_scores = calculate_house_scores(planet_positions, planet_houses)
    
    # Build house details
    houses = {}
    for i in range(12):
        house_num = i + 1
        cusp_degree = (house_cusps[i] - ayanamsa) % 360 if SWISSEPH_AVAILABLE else 0
        rashi, _ = get_rashi_from_degree(cusp_degree)
        
        planets_in_house = [
            name for name, h in planet_houses.items() if h == house_num
        ]
        
        houses[house_num] = {
            'rashi': rashi,
            'lord': RASHI_INFO[rashi]['lord'],
            'planets': planets_in_house,
            'score': house_scores.get(house_num, 15),
        }
    
    # Calculate Dasha
    birth_date = datetime(JAYTI_BIRTH_DATA['year'], JAYTI_BIRTH_DATA['month'], JAYTI_BIRTH_DATA['day']).date()
    moon_degree = planet_positions.get('moon', {}).get('degree', 0)
    dasha_periods = generate_vimshottari_dasha(jd, moon_degree, birth_date)
    current_dasha = get_current_mahadasha(dasha_periods)
    
    return {
        'ascendant': ascendant_rashi,
        'houses': houses,
        'planets': planet_positions,
        'dasha_periods': dasha_periods,
        'current_dasha': current_dasha,
    }


@login_required
def astro_dashboard(request):
    """Astrology dashboard overview"""
    if not SWISSEPH_AVAILABLE:
        messages.warning(request, 'Astrology features are temporarily unavailable. Please try again later.')
        return render(request, 'astro/astro_dashboard.html', {
            'birth_data': JAYTI_BIRTH_DATA,
            'swisseph_unavailable': True,
        })
    chart_data = calculate_birth_chart()
    
    context = {
        'birth_data': JAYTI_BIRTH_DATA,
        'ascendant': chart_data['ascendant'],
        'rashi_info': RASHI_INFO[chart_data['ascendant']],
        'current_dasha': chart_data['current_dasha'],
    }
    return render(request, 'astro/astro_dashboard.html', context)


@login_required
def birth_chart(request):
    """Display birth chart with visual representation"""
    chart_data = calculate_birth_chart()
    
    # Prepare chart data for display
    chart_display = []
    for house_num in range(1, 13):
        data = chart_data['houses'][house_num]
        
        planets_in_house = []
        for planet_name in data['planets']:
            if planet_name in chart_data['planets']:
                pdata = chart_data['planets'][planet_name]
                planets_in_house.append({
                    'name': planet_name,
                    'info': PLANET_INFO.get(planet_name, {}),
                    'degree': pdata.get('degree_in_rashi', 0),
                    'nakshatra': pdata.get('nakshatra', ''),
                    'symbol': pdata.get('symbol', ''),
                })
        
        chart_display.append({
            'number': house_num,
            'rashi': data['rashi'],
            'rashi_info': RASHI_INFO.get(data['rashi'], {}),
            'lord': data['lord'],
            'planets': planets_in_house,
            'score': data['score'],
        })
    
    # Prepare planet data for visual chart
    planets_for_chart = []
    for planet_name, pdata in chart_data['planets'].items():
        planets_for_chart.append({
            'name': planet_name,
            'symbol': pdata.get('symbol', ''),
            'house': pdata.get('house', 1),
            'rashi': pdata.get('rashi', 'aries'),
            'degree': pdata.get('degree_in_rashi', 0),
            'nakshatra': pdata.get('nakshatra', ''),
        })
    
    context = {
        'chart': chart_display,
        'ascendant': chart_data['ascendant'],
        'birth_data': JAYTI_BIRTH_DATA,
        'planets': planets_for_chart,
        'rashi_info': RASHI_INFO,
    }
    return render(request, 'astro/birth_chart.html', context)


@login_required
def house_details(request):
    """Detailed house analysis"""
    chart_data = calculate_birth_chart()
    
    house_meanings = {
        1: 'Self, Personality, Physical Appearance, Overall Well-being',
        2: 'Wealth, Family, Speech, Food, Face',
        3: 'Siblings, Courage, Communication, Short Travels, Skills',
        4: 'Home, Mother, Happiness, Vehicles, Education',
        5: 'Children, Creativity, Education, Speculation, Past Merit',
        6: 'Health, Enemies, Service, Debts, Competition',
        7: 'Marriage, Partnerships, Business, Foreign Lands',
        8: 'Transformation, Inheritance, Mysteries, Longevity, Sudden Events',
        9: 'Fortune, Higher Learning, Spirituality, Father, Long Travels',
        10: 'Career, Status, Father, Authority, Public Image',
        11: 'Gains, Friends, Aspirations, Elder Siblings, Fulfillment',
        12: 'Expenses, Liberation, Foreign Lands, Losses, Spirituality',
    }
    
    houses_detail = []
    
    for house_num in range(1, 13):
        data = chart_data['houses'][house_num]
        
        planets_in_house = []
        for planet_name in data['planets']:
            if planet_name in chart_data['planets']:
                pdata = chart_data['planets'][planet_name]
                planets_in_house.append({
                    'name': planet_name,
                    'info': PLANET_INFO.get(planet_name, {}),
                    'degree': pdata.get('degree_in_rashi', 0),
                    'nakshatra': pdata.get('nakshatra', ''),
                    'pada': pdata.get('pada', 1),
                    'symbol': pdata.get('symbol', ''),
                })
        
        strength = 'Strong' if data['score'] >= 25 else 'Moderate' if data['score'] >= 18 else 'Gentle'
        
        houses_detail.append({
            'number': house_num,
            'meaning': house_meanings[house_num],
            'rashi': data['rashi'],
            'rashi_info': RASHI_INFO.get(data['rashi'], {}),
            'lord': data['lord'],
            'lord_info': PLANET_INFO.get(data['lord'], {}),
            'planets': planets_in_house,
            'score': data['score'],
            'strength': strength,
        })
    
    context = {
        'houses': houses_detail,
    }
    return render(request, 'astro/house_details.html', context)


@login_required
def dasha_periods(request):
    """Display Vimshottari Dasha periods"""
    chart_data = calculate_birth_chart()
    
    dasha_periods = chart_data['dasha_periods']
    current_dasha = chart_data['current_dasha']
    
    # Get interpretation for current dasha
    current_interpretation = None
    if current_dasha:
        current_interpretation = get_dasha_interpretation(current_dasha['lord'])
        
        # Calculate antardashas for current mahadasha
        antardashas = calculate_antardasha(
            current_dasha['lord'],
            current_dasha['start_date'],
            current_dasha['end_date']
        )
        
        # Find current antardasha
        today = datetime.now().date()
        current_antardasha = None
        for ad in antardashas:
            if ad['start_date'] <= today < ad['end_date']:
                current_antardasha = ad
                break
    else:
        antardashas = []
        current_antardasha = None
    
    # Prepare dasha display with interpretations
    dasha_display = []
    for period in dasha_periods:
        interpretation = get_dasha_interpretation(period['lord'])
        dasha_display.append({
            **period,
            'interpretation': interpretation,
            'is_past': period['end_date'] < datetime.now().date(),
            'is_future': period['start_date'] > datetime.now().date(),
        })
    
    context = {
        'dasha_periods': dasha_display,
        'current_dasha': current_dasha,
        'current_interpretation': current_interpretation,
        'antardashas': antardashas,
        'current_antardasha': current_antardasha,
    }
    return render(request, 'astro/dasha_periods.html', context)


@login_required
def predictions(request):
    """90-day forward predictions based on current transits and dasha"""
    today = datetime.now().date()
    
    # Calculate current chart
    chart_data = calculate_birth_chart()
    
    # Get current dasha for personalized predictions
    current_dasha = chart_data['current_dasha']
    dasha_influence = ""
    if current_dasha:
        dasha_interp = get_dasha_interpretation(current_dasha['lord'])
        dasha_influence = f"During this {current_dasha['lord']} Mahadasha, {dasha_interp['theme'].lower()} influences your path."
    
    # Generate predictions based on current transits and dasha
    predictions_data = generate_predictions(today, chart_data, dasha_influence)
    
    context = {
        'predictions': predictions_data,
        'today': today,
        'current_dasha': current_dasha,
    }
    return render(request, 'astro/predictions.html', context)


def generate_predictions(today, chart_data, dasha_influence=""):
    """Generate 90-day predictions based on planetary transits and dasha"""
    predictions = []
    
    # Get current planetary positions
    jd_today = calculate_julian_day(today.year, today.month, today.day, 12, 0)
    current_positions = calculate_planet_positions(jd_today)
    
    # Assign houses to current positions
    house_cusps_today = calculate_houses(jd_today, JAYTI_BIRTH_DATA['latitude'], JAYTI_BIRTH_DATA['longitude'])
    planet_houses_today = assign_planets_to_houses(current_positions, house_cusps_today)
    for planet_name, house in planet_houses_today.items():
        if planet_name in current_positions:
            current_positions[planet_name]['house'] = house
    
    # Get natal positions for comparison
    natal_positions = chart_data['planets']
    
    # Career prediction (10th house focus)
    career_score = 0
    career_factors = []
    
    # Check Jupiter's transit
    if 'jupiter' in current_positions and 'jupiter' in natal_positions:
        jupiter_current = current_positions['jupiter'].get('house', 1)
        jupiter_natal = natal_positions['jupiter'].get('house', 1)
        
        if jupiter_current == 10 or jupiter_natal == 10:
            career_score += 20
            career_factors.append("Jupiter's favorable influence on career house")
    
    # Check Saturn's transit
    if 'saturn' in current_positions:
        saturn_house = current_positions['saturn'].get('house', 1)
        if saturn_house == 10:
            career_score += 10
            career_factors.append("Saturn bringing discipline to career matters")
    
    career_intensity = 'favorable' if career_score >= 20 else 'neutral' if career_score >= 10 else 'challenging'
    
    predictions.append({
        'period': 'Next 30 Days',
        'focus': 'Career',
        'intensity': career_intensity,
        'description': generate_career_description(career_score, career_factors, dasha_influence),
        'recommendation': generate_career_recommendation(career_intensity),
        'dates': f"{today.strftime('%d %b')} - {(today + timedelta(days=30)).strftime('%d %b')}",
    })
    
    # Relationship prediction (7th house focus)
    relationship_score = 0
    rel_factors = []
    
    if 'venus' in current_positions:
        venus_house = current_positions['venus'].get('house', 1)
        if venus_house in [7, 5, 11]:
            relationship_score += 15
            rel_factors.append("Venus supporting relationship harmony")
    
    rel_intensity = 'favorable' if relationship_score >= 15 else 'neutral'
    
    predictions.append({
        'period': 'Days 30-60',
        'focus': 'Relationships',
        'intensity': rel_intensity,
        'description': generate_relationship_description(relationship_score, dasha_influence),
        'recommendation': 'Practice active listening. Express appreciation for loved ones. Be patient with family matters.',
        'dates': f"{(today + timedelta(days=30)).strftime('%d %b')} - {(today + timedelta(days=60)).strftime('%d %b')}",
    })
    
    # Health prediction (1st and 6th house focus)
    health_score = 0
    
    if 'saturn' in current_positions:
        saturn_house = current_positions['saturn'].get('house', 1)
        if saturn_house in [1, 6]:
            health_score -= 10
    
    if 'sun' in current_positions:
        sun_house = current_positions['sun'].get('house', 1)
        if sun_house == 1:
            health_score += 10
    
    health_intensity = 'favorable' if health_score > 0 else 'challenging' if health_score < 0 else 'neutral'
    
    predictions.append({
        'period': 'Days 60-90',
        'focus': 'Health',
        'intensity': health_intensity,
        'description': generate_health_description(health_intensity, dasha_influence),
        'recommendation': 'Establish consistent sleep and exercise routines. Prioritize mental health through meditation or journaling.',
        'dates': f"{(today + timedelta(days=60)).strftime('%d %b')} - {(today + timedelta(days=90)).strftime('%d %b')}",
    })
    
    return predictions


def generate_career_description(score, factors, dasha_influence=""):
    """Generate career prediction description"""
    base_desc = ""
    if score >= 20:
        base_desc = "Jupiter aspects your 10th house, bringing opportunities for professional growth. This is a favorable time for initiating new projects and seeking recognition."
    elif score >= 10:
        base_desc = "Steady progress in career matters. Focus on building foundations and demonstrating reliability."
    else:
        base_desc = "A period for introspection regarding career direction. Avoid major decisions and focus on skill development."
    
    if dasha_influence:
        base_desc = f"{dasha_influence} {base_desc}"
    
    return base_desc


def generate_career_recommendation(intensity):
    """Generate career recommendation"""
    if intensity == 'favorable':
        return "Take initiative on career goals. Network actively and present your ideas with confidence."
    elif intensity == 'neutral':
        return "Maintain steady effort. Focus on completing existing projects before starting new ones."
    else:
        return "Focus on skill development and learning. Avoid major career changes during this period."


def generate_relationship_description(score, dasha_influence=""):
    """Generate relationship prediction description"""
    if score >= 15:
        return "Venus transits bring focus on partnerships. A time for deepening existing connections and healing past misunderstandings."
    else:
        return "Stable period for relationships. Focus on communication and understanding."


def generate_health_description(intensity, dasha_influence=""):
    """Generate health prediction description"""
    if intensity == 'challenging':
        return "Saturn influence suggests the need for discipline in health routines. Minor stress-related issues may arise."
    elif intensity == 'favorable':
        return "Positive energy supporting vitality and well-being. Good time to start health initiatives."
    else:
        return "Maintain regular health routines. Pay attention to balance between work and rest."


@login_required
def planet_detail(request, planet):
    """Detailed information about a planet"""
    chart_data = calculate_birth_chart()
    
    if planet not in chart_data['planets']:
        messages.error(request, 'Planet not found.')
        return redirect('birth_chart')
    
    pdata = chart_data['planets'][planet]
    house = pdata.get('house', 1)
    rashi = pdata.get('rashi', 'aries')
    
    # Generate interpretation based on house position
    house_interpretations = {
        1: "In the 1st house, this planet significantly influences your personality and physical appearance.",
        2: "In the 2nd house, this planet affects your wealth, speech, and family matters.",
        3: "In the 3rd house, this planet influences your courage, siblings, and communication skills.",
        4: "In the 4th house, this planet affects your home, happiness, and relationship with mother.",
        5: "In the 5th house, this planet influences your creativity, children, and speculative gains.",
        6: "In the 6th house, this planet affects your health, competition, and ability to overcome obstacles.",
        7: "In the 7th house, this planet significantly influences your partnerships and marriage.",
        8: "In the 8th house, this planet affects transformation, inheritance, and longevity.",
        9: "In the 9th house, this planet influences your fortune, higher learning, and spirituality.",
        10: "In the 10th house, this planet strongly influences your career and public status.",
        11: "In the 11th house, this planet affects your gains, aspirations, and elder siblings.",
        12: "In the 12th house, this planet influences expenses, foreign connections, and liberation.",
    }
    
    context = {
        'planet': planet,
        'info': PLANET_INFO.get(planet, {}),
        'data': pdata,
        'house': house,
        'rashi': rashi,
        'rashi_info': RASHI_INFO.get(rashi, {}),
        'interpretation': house_interpretations.get(house, ""),
    }
    return render(request, 'astro/planet_detail.html', context)
