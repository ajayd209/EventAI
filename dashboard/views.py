from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from events.models import Event, EventTimeline
from django.db.models import Sum, Q

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard:my_dashboard')
    return render(request, 'home.html')

@login_required
def my_dashboard(request):
    events = Event.objects.filter(created_by=request.user)
    upcoming_events = events.filter(event_date__gte=timezone.now().date()).count()
    completed_events = events.filter(event_date__lt=timezone.now().date()).count()
    total_budget = events.aggregate(Sum('budget'))['budget__sum'] or 0
    pending_tasks = EventTimeline.objects.filter(event__in=events, status='Pending').count()
    
    return render(request, 'dashboard/my_dashboard.html', {
        'total_events': events.count(),
        'upcoming_events': upcoming_events,
        'completed_events': completed_events,
        'total_budget': total_budget,
        'pending_tasks': pending_tasks,
        'recent_events': events.order_by('-created_at')[:5]
    })

@login_required
def my_events(request):
    events = Event.objects.filter(created_by=request.user).order_by('-created_at')
    query = request.GET.get('q', '').strip()
    
    if query:
        events = events.filter(
            Q(event_name__icontains=query) |
            Q(event_type__icontains=query) |
            Q(location__icontains=query)
        )
    
    return render(request, 'dashboard/my_events.html', {'events': events})
