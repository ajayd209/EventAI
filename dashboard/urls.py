from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.my_dashboard, name='my_dashboard'),
    path('my-events/', views.my_events, name='my_events'),
]
