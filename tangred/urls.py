from django.urls import path

from . import views


urlpatterns = [
    path("", views.tangred_home, name="tangred_home"),
    path("sessions/create/", views.create_session_view, name="tangred_create_session"),
    path("sessions/<uuid:pk>/", views.session_detail, name="tangred_session_detail"),
    path("sessions/<uuid:pk>/run/", views.run_session_view, name="tangred_run_session"),
    path("photos/<int:pk>/", views.session_photo_view, name="tangred_session_photo"),
    path("studio/", views.studio_home, name="tan_studio_home"),
    path("studio/projects/create/", views.create_project_view, name="tan_studio_create_project"),
    path("studio/projects/<uuid:pk>/", views.project_detail, name="tan_studio_project_detail"),
    path("studio/projects/<uuid:pk>/generate/", views.generate_screen_view, name="tan_studio_generate_screen"),
    path("studio/screens/<uuid:pk>/", views.screen_detail, name="tan_studio_screen_detail"),
    path("studio/screens/<uuid:pk>/refresh/", views.refresh_screen_view, name="tan_studio_refresh_screen"),
]
