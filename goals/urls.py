from django.urls import path
from . import views

urlpatterns = [
    path('', views.goal_list, name='goal_list'),
    path('create/', views.goal_create, name='goal_create'),
    path('<uuid:pk>/', views.goal_detail, name='goal_detail'),
    path('<uuid:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('<uuid:pk>/delete/', views.goal_delete, name='goal_delete'),
    
    # Task management
    path('<uuid:goal_pk>/task/create/', views.task_create, name='task_create'),
    path('task/<uuid:pk>/update/', views.task_update, name='task_update'),
    path('task/<uuid:pk>/delete/', views.task_delete, name='task_delete'),
    
    # Board view
    path('board/', views.goal_board, name='goal_board'),
    
    # AI Task regeneration
    path('<uuid:pk>/regenerate-tasks/', views.regenerate_ai_tasks, name='regenerate_ai_tasks'),
]
