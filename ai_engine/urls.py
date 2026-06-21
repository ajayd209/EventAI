from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('', views.create_event_ai, name='create_event_ai'),
    path('copilot/<int:event_id>/', views.copilot_query_view, name='copilot_query'),
]
