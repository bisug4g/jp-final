from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_interface, name='ai_chat'),
    path('send/', views.send_message, name='ai_send_message'),
    path('history/', views.chat_history, name='ai_chat_history'),
    path('clear/', views.clear_conversation, name='ai_clear_conversation'),
]
