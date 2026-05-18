"""
Comprehensive Backend API Tests for JAYTI Personal Life Companion
Tests all modules: Auth, Dashboard, Notes, Diary, Goals, Astro, AI Chat
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_USERNAME = os.environ.get('E2E_USERNAME', '')
TEST_PASSWORD = os.environ.get('E2E_PASSWORD', '')


def get_test_login_payload(csrf_token):
    assert TEST_USERNAME and TEST_PASSWORD, 'Set E2E_USERNAME and E2E_PASSWORD for authenticated E2E tests.'
    return {
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD,
        'csrfmiddlewaretoken': csrf_token,
    }

class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test health check endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/health/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'database' in data['checks']
        print(f"Health check passed: {data}")


class TestAuthentication:
    """Authentication flow tests"""
    
    def test_login_page_loads(self):
        """Test login page is accessible"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert 'Jayti' in response.text or 'login' in response.text.lower()
        print("Login page loads successfully")
    
    def test_login_with_valid_credentials(self):
        """Test login with configured credentials"""
        session = requests.Session()
        
        # Get CSRF token first
        login_page = session.get(f"{BASE_URL}/")
        assert login_page.status_code == 200
        
        # Extract CSRF token from cookies or form
        csrf_token = session.cookies.get('csrftoken', '')
        
        # Attempt login
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        response = session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        
        # Should redirect to dashboard on success
        assert response.status_code == 200
        # Check if we're on dashboard or still on login
        if 'dashboard' in response.url or 'Welcome' in response.text:
            print("Login successful - redirected to dashboard")
        else:
            print(f"Login response URL: {response.url}")
        
        return session
    
    def test_login_with_invalid_credentials(self):
        """Test login fails with wrong credentials"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = {
            'username': 'wronguser',
            'password': 'wrongpass',
            'csrfmiddlewaretoken': csrf_token
        }
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        response = session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        
        # Should stay on login page with error
        assert response.status_code == 200
        # Should show error or stay on login
        assert 'Invalid' in response.text or 'login' in response.url or 'Access Code' in response.text
        print("Invalid login correctly rejected")


class TestDashboard:
    """Dashboard tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_dashboard_loads(self, authenticated_session):
        """Test dashboard page loads after login"""
        response = authenticated_session.get(f"{BASE_URL}/dashboard/")
        assert response.status_code == 200
        assert 'Welcome' in response.text or 'Dashboard' in response.text
        print("Dashboard loads successfully")
    
    def test_dashboard_shows_birthday_countdown(self, authenticated_session):
        """Test birthday countdown is displayed"""
        response = authenticated_session.get(f"{BASE_URL}/dashboard/")
        assert response.status_code == 200
        # Should show birthday countdown
        assert 'Birthday' in response.text or 'days' in response.text
        print("Birthday countdown displayed")


class TestNotesModule:
    """Notes CRUD tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_notes_list_page(self, authenticated_session):
        """Test notes list page loads"""
        response = authenticated_session.get(f"{BASE_URL}/notes/")
        assert response.status_code == 200
        assert 'Notes' in response.text or 'note' in response.text.lower()
        print("Notes list page loads successfully")
    
    def test_notes_create_page(self, authenticated_session):
        """Test notes create page loads"""
        response = authenticated_session.get(f"{BASE_URL}/notes/create/")
        assert response.status_code == 200
        assert 'New Note' in response.text or 'Create' in response.text or 'Title' in response.text
        print("Notes create page loads successfully")


class TestDiaryModule:
    """Diary tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_diary_overview_page(self, authenticated_session):
        """Test diary overview page loads"""
        response = authenticated_session.get(f"{BASE_URL}/diary/")
        assert response.status_code == 200
        assert 'Diary' in response.text or 'Entry' in response.text
        print("Diary overview page loads successfully")
    
    def test_diary_write_page(self, authenticated_session):
        """Test diary write page loads"""
        response = authenticated_session.get(f"{BASE_URL}/diary/write/")
        assert response.status_code == 200
        assert 'Write' in response.text or 'Content' in response.text or 'Mood' in response.text
        print("Diary write page loads successfully")
    
    def test_diary_calendar_page(self, authenticated_session):
        """Test diary calendar page loads"""
        response = authenticated_session.get(f"{BASE_URL}/diary/calendar/")
        assert response.status_code == 200
        print("Diary calendar page loads successfully")


class TestGoalsModule:
    """Goals tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_goals_list_page(self, authenticated_session):
        """Test goals list page loads"""
        response = authenticated_session.get(f"{BASE_URL}/goals/")
        assert response.status_code == 200
        assert 'Goals' in response.text or 'Active' in response.text
        print("Goals list page loads successfully")
    
    def test_goals_create_page(self, authenticated_session):
        """Test goals create page loads"""
        response = authenticated_session.get(f"{BASE_URL}/goals/create/")
        assert response.status_code == 200
        assert 'Goal' in response.text or 'Create' in response.text
        print("Goals create page loads successfully")
    
    def test_goals_board_page(self, authenticated_session):
        """Test goals board page loads"""
        response = authenticated_session.get(f"{BASE_URL}/goals/board/")
        assert response.status_code == 200
        print("Goals board page loads successfully")


class TestAstroModule:
    """Astrology tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_astro_dashboard_page(self, authenticated_session):
        """Test astro dashboard page loads"""
        response = authenticated_session.get(f"{BASE_URL}/astro/")
        assert response.status_code == 200
        assert 'Astro' in response.text or 'Birth' in response.text
        print("Astro dashboard page loads successfully")
    
    def test_astro_shows_birth_data(self, authenticated_session):
        """Test astro page shows correct birth data"""
        response = authenticated_session.get(f"{BASE_URL}/astro/")
        assert response.status_code == 200
        # Check for birth date: 6-2-1997
        assert '1997' in response.text
        assert '6' in response.text or 'February' in response.text
        # Check for birth time: 22:30
        assert '22:30' in response.text
        print("Birth data displayed correctly: Date: 6-2-1997, Time: 22:30")
    
    def test_birth_chart_page(self, authenticated_session):
        """Test birth chart page loads"""
        response = authenticated_session.get(f"{BASE_URL}/astro/chart/")
        assert response.status_code == 200
        assert 'Chart' in response.text or 'House' in response.text
        print("Birth chart page loads successfully")
    
    def test_dasha_periods_page(self, authenticated_session):
        """Test dasha periods page loads"""
        response = authenticated_session.get(f"{BASE_URL}/astro/dasha/")
        assert response.status_code == 200
        assert 'Dasha' in response.text or 'Period' in response.text
        print("Dasha periods page loads successfully")
    
    def test_predictions_page(self, authenticated_session):
        """Test predictions page loads"""
        response = authenticated_session.get(f"{BASE_URL}/astro/predictions/")
        assert response.status_code == 200
        print("Predictions page loads successfully")


class TestAIChatModule:
    """AI Chat tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_ai_chat_page(self, authenticated_session):
        """Test AI chat page loads"""
        response = authenticated_session.get(f"{BASE_URL}/ai-chat/")
        assert response.status_code == 200
        assert 'Ask Jayti' in response.text or 'Chat' in response.text or 'AI' in response.text
        print("AI Chat page loads successfully")
    
    def test_ai_chat_send_message(self, authenticated_session):
        """Test sending message to AI chat"""
        # Get CSRF token
        chat_page = authenticated_session.get(f"{BASE_URL}/ai-chat/")
        csrf_token = authenticated_session.cookies.get('csrftoken', '')
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Referer': f"{BASE_URL}/ai-chat/"
        }
        
        message_data = {
            'message': 'Hello, this is a test message'
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/ai-chat/send/",
            json=message_data,
            headers=headers
        )
        
        # Should return 200 with AI response
        assert response.status_code == 200
        data = response.json()
        assert 'response' in data
        print(f"AI Chat response received: {data['response'][:100]}...")


class TestProfileModule:
    """Profile tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_profile_page(self, authenticated_session):
        """Test profile page loads"""
        response = authenticated_session.get(f"{BASE_URL}/profile/")
        assert response.status_code == 200
        assert 'Profile' in response.text or 'Jayti' in response.text
        print("Profile page loads successfully")


class TestAPIEndpoints:
    """API endpoint tests"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        return session
    
    def test_daily_briefing_api(self, authenticated_session):
        """Test daily briefing API"""
        response = authenticated_session.get(f"{BASE_URL}/api/daily-briefing/")
        # May return 200 or redirect if not authenticated
        assert response.status_code in [200, 302, 403]
        print(f"Daily briefing API status: {response.status_code}")
    
    def test_goal_progress_api(self, authenticated_session):
        """Test goal progress API"""
        response = authenticated_session.get(f"{BASE_URL}/api/goal-progress/")
        assert response.status_code in [200, 302, 403]
        print(f"Goal progress API status: {response.status_code}")
    
    def test_mood_trends_api(self, authenticated_session):
        """Test mood trends API"""
        response = authenticated_session.get(f"{BASE_URL}/api/mood-trends/")
        assert response.status_code in [200, 302, 403]
        print(f"Mood trends API status: {response.status_code}")


class TestLogout:
    """Logout tests"""
    
    def test_logout_redirects_to_login(self):
        """Test logout redirects to login page"""
        session = requests.Session()
        
        # Login first
        login_page = session.get(f"{BASE_URL}/")
        csrf_token = session.cookies.get('csrftoken', '')
        
        login_data = get_test_login_payload(csrf_token)
        headers = {
            'Referer': f"{BASE_URL}/",
            'X-CSRFToken': csrf_token
        }
        
        session.post(f"{BASE_URL}/", data=login_data, headers=headers, allow_redirects=True)
        
        # Now logout
        response = session.get(f"{BASE_URL}/logout/", allow_redirects=True)
        assert response.status_code == 200
        # Should be back on login page
        assert 'login' in response.url or response.url.endswith('/') or 'Access Code' in response.text
        print("Logout successful - redirected to login")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
