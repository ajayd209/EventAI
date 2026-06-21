from django.urls import path
from . import views

app_name = 'event_planner'

urlpatterns = [
    path('', views.planner_home, name='planner_home'),
    path('history/', views.plan_history, name='plan_history'),
    path('history/<uuid:pk>/', views.plan_detail, name='plan_detail'),
    path('history/<uuid:pk>/toggle_task/', views.toggle_task, name='toggle_task'),
    path('draft/<uuid:pk>/', views.planner_home, name='load_draft'),
    path('delete_draft/<uuid:pk>/', views.delete_draft, name='delete_draft'),
    path('publish_draft/<uuid:pk>/', views.publish_draft, name='publish_draft'),
    path('auto_save_draft/', views.auto_save_draft, name='auto_save_draft'),
]
