from django.urls import path
from . import views

urlpatterns = [
    path('', views.astro_dashboard, name='astro_dashboard'),
    path('chart/', views.birth_chart, name='birth_chart'),
    path('houses/', views.house_details, name='house_details'),
    path('dasha/', views.dasha_periods, name='dasha_periods'),
    path('predictions/', views.predictions, name='predictions'),
    path('planet/<str:planet>/', views.planet_detail, name='planet_detail'),
]
