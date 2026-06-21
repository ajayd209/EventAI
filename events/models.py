from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Event(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    event_name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    event_date = models.DateField()
    expected_crowd = models.PositiveIntegerField()
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prize_money = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_name
    
    @property
    def days_remaining(self):
        delta = self.event_date - timezone.now().date()
        return max(0, delta.days)

class AuditLog(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} on {self.event.event_name}"

class EventModule(models.Model):
    STATUS_CHOICES = [('Not Started', 'Not Started'), ('In Progress', 'In Progress'), ('Completed', 'Completed')]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='modules')
    module_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Not Started')
    form_schema = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.module_name)
        super().save(*args, **kwargs)

class ModuleEntry(models.Model):
    module = models.ForeignKey(EventModule, on_delete=models.CASCADE, related_name='entries')
    data_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class EventTimeline(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed')]
    PRIORITY_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='timeline')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    completion_percentage = models.IntegerField(default=0)
    category = models.CharField(max_length=100, blank=True, null=True)
    days_before_event = models.IntegerField()
    due_date = models.DateField()
    assigned_role = models.CharField(max_length=100, default='Organizer')
    related_module = models.ForeignKey(EventModule, on_delete=models.SET_NULL, null=True, blank=True, related_name='timeline_items')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class BudgetPlan(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='budget_items')
    category = models.CharField(max_length=100)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)

class BudgetSummary(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='budget_summary')
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_budget = models.DecimalField(max_digits=12, decimal_places=2)
    risk_level = models.CharField(max_length=50)
    ai_recommendation = models.TextField()

class MarketingContent(models.Model):
    CONTENT_TYPES = [
        ('Description', 'Description'),
        ('Instagram', 'Instagram'),
        ('Facebook', 'Facebook'),
        ('WhatsApp', 'WhatsApp'),
        ('LinkedIn', 'LinkedIn'),
        ('EmailCampaign', 'EmailCampaign'),
        ('SponsorPitch', 'SponsorPitch'),
        ('PressRelease', 'PressRelease'),
        ('VolunteerRecruitment', 'VolunteerRecruitment'),
        ('Hashtags', 'Hashtags'),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='marketing_contents')
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.content_type} for {self.event.event_name}"

class EventTask(models.Model):
    STATUS_CHOICES = [
        ('To Do', 'To Do'),
        ('In Progress', 'In Progress'),
        ('Done', 'Done'),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='To Do')
    days_before = models.IntegerField()
