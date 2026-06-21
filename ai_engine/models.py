from django.db import models
from events.models import Event

class AIAnalysis(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='analysis')
    event_category = models.CharField(max_length=100)
    risk_level = models.CharField(max_length=50)
    volunteers_required = models.CharField(max_length=255)
    security_required = models.CharField(max_length=255)
    
    # New structured fields
    risk_intelligence = models.JSONField(default=dict, blank=True)
    team_planning = models.JSONField(default=dict, blank=True)
    analytics = models.JSONField(default=dict, blank=True)
    
    raw_ai_response = models.TextField()

    def __str__(self):
        return f"Analysis for {self.event.event_name}"
