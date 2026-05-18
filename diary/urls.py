from django.urls import path
from . import views

urlpatterns = [
    path('', views.diary_overview, name='diary_overview'),
    path('write/', views.diary_write, name='diary_write'),
    path('write/<str:date>/', views.diary_write, name='diary_write_date'),
    path('entry/<uuid:pk>/', views.diary_entry_detail, name='diary_entry_detail'),
    path('calendar/', views.diary_calendar, name='diary_calendar'),
    path('summary/', views.diary_summary, name='diary_summary'),
]
