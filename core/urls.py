from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, api_views, api_briefing
from diary import api_mood
from notes import pdf_export

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-change/', views.password_change_view, name='password_change'),
    
    # Main pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Birthday API
    path('api/birthday-seen/', views.birthday_seen, name='birthday_seen'),
    
    # Enhanced API endpoints
    path('api/daily-briefing/', api_briefing.daily_briefing, name='api_daily_briefing'),
    path('api/weekly-summary/', api_briefing.weekly_summary, name='api_weekly_summary'),
    path('api/mood-trends/', api_mood.mood_trends, name='api_mood_trends'),
    path('api/goal-progress/', api_views.api_goal_progress, name='api_goal_progress'),
    path('api/daily-astro/', api_views.api_daily_astro, name='api_daily_astro'),
    path('api/diary-search/', api_views.api_diary_search, name='api_diary_search'),
    path('api/export-diary-pdf/', api_views.api_export_diary_pdf, name='api_export_diary_pdf'),
    path('api/export-notes-pdf/', pdf_export.export_notes_pdf, name='api_export_notes_pdf'),
    path('api/push-subscribe/', api_views.api_push_subscribe, name='api_push_subscribe'),
    path('api/push-unsubscribe/', api_views.api_push_unsubscribe, name='api_push_unsubscribe'),
    path('api/notification-settings/', api_views.api_notification_settings, name='api_notification_settings'),
    
    # Activity Tracker API
    path('api/activity-calendar/', api_views.api_activity_calendar, name='api_activity_calendar'),
    path('api/activity-stats/', api_views.api_activity_stats, name='api_activity_stats'),

    # Health check for Railway deployment
    path('health/', views.health_check, name='health_check'),
    
    # Session tracking dashboard
    path('sessions/', views.session_dashboard, name='session_dashboard'),
    path('sessions/terminate/<int:session_id>/', views.terminate_session, name='terminate_session'),
]
