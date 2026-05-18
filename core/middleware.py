"""
Custom middleware for user session tracking.
"""
import re
from django.utils.deprecation import MiddlewareMixin
from .models import UserSession


class UserSessionTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user sessions with IP and device information.
    Captures login data and updates activity timestamps.
    """
    
    # Skip tracking for these paths
    SKIP_PATHS = ['/static/', '/media/', '/favicon.ico', '/health', '/admin/jsi18n/', '/api/']
    
    def process_request(self, request):
        # Skip tracking for static/media/API
        path = request.path
        for skip_path in self.SKIP_PATHS:
            if path.startswith(skip_path):
                return None
        
        # Only track authenticated users
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Get or create session tracking record
        session_key = request.session.session_key
        if not session_key:
            return None
        
        try:
            from django.utils import timezone as tz
            user_session, created = UserSession.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'user': request.user,
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    'device_type': self.detect_device_type(request),
                    'browser': self.detect_browser(request),
                    'browser_version': self.detect_browser_version(request),
                    'os': self.detect_os(request),
                    'os_version': self.detect_os_version(request),
                }
            )
            
            if not created:
                # Throttle: only update last_activity once per 5 minutes
                if not hasattr(user_session, 'last_activity') or \
                   user_session.last_activity is None or \
                   (tz.now() - user_session.last_activity).total_seconds() > 300:
                    user_session.save()
                
        except Exception:
            # Silently fail to not break the application
            pass
        
        return None
    
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            x_real_ip = request.META.get('HTTP_X_REAL_IP')
            if x_real_ip:
                ip = x_real_ip
            else:
                ip = request.META.get('REMOTE_ADDR')
        
        # Validate IP address
        if ip and len(ip) <= 45:  # IPv6 max length
            return ip
        return None
    
    def detect_device_type(self, request):
        """Detect if device is mobile, tablet, or desktop"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Check for tablets first
        tablets = ['ipad', 'android(?!.*mobile)', 'tablet', 'kindle', 'silk']
        for tablet in tablets:
            if re.search(tablet, user_agent):
                return 'tablet'
        
        # Check for mobile devices
        mobiles = ['mobile', 'android', 'iphone', 'ipod', 'windows phone', 
                   'blackberry', 'webos', 'iemobile', 'opera mini']
        for mobile in mobiles:
            if mobile in user_agent:
                return 'mobile'
        
        # Check for bots
        bots = ['bot', 'crawler', 'spider', 'scrape', 'archiver', 'slurp']
        for bot in bots:
            if bot in user_agent:
                return 'bot'
        
        return 'desktop'
    
    def detect_browser(self, request):
        """Detect browser name from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        browsers = [
            ('edge', 'Edge'),
            ('edg/', 'Edge'),
            ('chrome', 'Chrome'),
            ('safari', 'Safari'),
            ('firefox', 'Firefox'),
            ('opera', 'Opera'),
            ('opr/', 'Opera'),
            ('trident', 'Internet Explorer'),
            ('msie', 'Internet Explorer'),
        ]
        
        for pattern, name in browsers:
            if pattern in user_agent:
                return name
        
        return 'Unknown'
    
    def detect_browser_version(self, request):
        """Extract browser version from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        browser = self.detect_browser(request).lower()
        
        patterns = {
            'chrome': r'Chrome/(\d+\.\d+)',
            'safari': r'Version/(\d+\.\d+)',
            'firefox': r'Firefox/(\d+\.\d+)',
            'edge': r'(?:Edge|Edg)/(\d+\.\d+)',
            'opera': r'(?:Opera|OPR)/(\d+\.\d+)',
        }
        
        for key, pattern in patterns.items():
            if key in browser or key in user_agent.lower():
                match = re.search(pattern, user_agent)
                if match:
                    return match.group(1)
        
        return ''
    
    def detect_os(self, request):
        """Detect operating system from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        os_patterns = [
            ('windows nt 10.0', 'Windows'),
            ('windows nt 6.3', 'Windows'),
            ('windows nt 6.2', 'Windows'),
            ('windows nt 6.1', 'Windows'),
            ('macintosh', 'macOS'),
            ('mac os', 'macOS'),
            ('iphone', 'iOS'),
            ('ipad', 'iOS'),
            ('android', 'Android'),
            ('linux', 'Linux'),
        ]
        
        for pattern, name in os_patterns:
            if pattern in user_agent:
                return name
        
        return 'Unknown'
    
    def detect_os_version(self, request):
        """Extract OS version from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        os_name = self.detect_os(request)
        
        patterns = {
            'Windows': r'Windows NT (\d+\.\d+)',
            'macOS': r'Mac OS X (\d+[._]\d+[._]?\d*)',
            'iOS': r'OS (\d+_\d+_?\d*)',
            'Android': r'Android (\d+\.\d+)',
        }
        
        if os_name in patterns:
            match = re.search(patterns[os_name], user_agent)
            if match:
                return match.group(1).replace('_', '.')
        
        return ''
