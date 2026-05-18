from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list, name='note_list'),
    path('create/', views.note_create, name='note_create'),
    path('<uuid:pk>/', views.note_detail, name='note_detail'),
    path('<uuid:pk>/edit/', views.note_edit, name='note_edit'),
    path('<uuid:pk>/delete/', views.note_delete, name='note_delete'),
    # Folder management
    path('folder/create/', views.folder_create, name='folder_create'),
    path('folder/<int:pk>/delete/', views.folder_delete, name='folder_delete'),
]
