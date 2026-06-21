from django.urls import path
from . import views
from ai_engine.views import regenerate_marketing_view

app_name = 'events'

urlpatterns = [
    path('workspace/<int:event_id>/', views.workspace, name='workspace'),
    path('<int:event_id>/module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('<int:event_id>/module/slug/<slug:module_slug>/', views.module_detail_slug, name='module_detail_slug'),
    path('task/update/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('milestone/update/<int:milestone_id>/', views.update_milestone_status, name='update_milestone_status'),
    path('<int:event_id>/marketing/regenerate/<str:content_type>/', regenerate_marketing_view, name='regenerate_marketing'),
    path('<int:event_id>/audit/', views.audit_logs, name='audit_logs'),
]
