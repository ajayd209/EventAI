from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from .models import Event, EventModule, ModuleEntry, EventTimeline, BudgetPlan, BudgetSummary, MarketingContent, AuditLog, EventTask

def check_event_access(user, event):
    if event.created_by and event.created_by != user:
        raise PermissionDenied("You do not have access to this event.")

@login_required
def workspace(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    check_event_access(request.user, event)
    
    # 1. Roadmap (High-level milestones)
    roadmap = event.timeline.all().order_by('due_date')
    
    # 2. Kanban Tasks (Granular operations)
    tasks = event.tasks.all()
    lane_todo = tasks.filter(status='To Do')
    lane_inprogress = tasks.filter(status='In Progress')
    lane_done = tasks.filter(status='Done')
    
    # 3. Financials
    budget_items = event.budget_items.all()
    try:
        budget_summary = event.budget_summary
    except BudgetSummary.DoesNotExist:
        budget_summary = None
    
    # 4. Marketing
    marketing_items = event.marketing_contents.all()
    
    # Activity & Modules
    recent_logs = event.audit_logs.all().order_by('-timestamp')[:15]
    modules = event.modules.all()
    
    # Progress Stats (Calculated from granular Kanban tasks)
    total_tasks = tasks.count()
    completed_tasks = lane_done.count()
    pending_tasks = lane_todo.count()
    progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    # Ensure all modules have slugs (one-time migration for existing data)
    for m in modules:
        if not m.slug:
            m.save() 

    # --- ROADMAP V4 ENGINE (AI Guidance System) ---
    # Define category-specific phase templates with Guidance Data
    CATEGORY_PHASE_TEMPLATES = {
        'Sports Event': [
            {
                "id": 1, "name": "Tournament Setup", "categories": ["Management", "Planning", "Legal", "Strategy"],
                "purpose": "Lay the foundational rules and structure for the tournament.",
                "why": "Clear rules prevent disputes and ensure fair competition.",
                "steps": ["Define match formats", "Set registration fees", "Establish prize pools", "Draft rulebook"],
                "effort": "3-5 days", "next": "Registration"
            },
            {
                "id": 2, "name": "Registration", "categories": ["Registration", "Team", "Staffing"],
                "purpose": "Onboard participants and collect necessary documentation.",
                "why": "Finalizing participant lists is critical for scheduling and logistics.",
                "steps": ["Open online portals", "Verify ID documents", "Collect payments", "Close registration"],
                "effort": "1-2 weeks", "next": "Ground Preparation"
            },
            {
                "id": 3, "name": "Ground Preparation", "categories": ["Logistics", "Venue", "Technical", "Equipment"],
                "purpose": "Ready the physical arena for matches.",
                "why": "Player safety and professional standards depend on high-quality pitch prep.",
                "steps": ["Mark boundaries", "Set up goalposts/nets", "Check floodlights", "Arrange seating"],
                "effort": "2-4 days", "next": "Match Management"
            },
            {
                "id": 4, "name": "Match Management", "categories": ["Operations", "Safety", "Security"],
                "purpose": "Oversee the day-to-day operations of tournament matches.",
                "why": "Seamless match flow keeps the schedule on track and fans engaged.",
                "steps": ["Brief referees", "Coordinate ball boys", "Manage scoreboard", "Handle incidents"],
                "effort": "Duration of event", "next": "Event Execution"
            },
            {
                "id": 5, "name": "Event Execution", "categories": ["Execution", "On-site"],
                "purpose": "The grand finale or the main match day operations.",
                "why": "This is where the user experience and event success are finalized.",
                "steps": ["Manage entry gates", "Execute opening ceremony", "Coordinate media", "Oversee VIPs"],
                "effort": "1-2 days", "next": "Prize Distribution"
            },
            {
                "id": 6, "name": "Prize Distribution", "categories": ["Finance", "Final", "Feedback"],
                "purpose": "Reward excellence and wrap up financial obligations.",
                "why": "Proper closure ensures a positive legacy and accurate accounts.",
                "steps": ["Verify winners", "Present trophies", "Settle vendor bills", "Publish results"],
                "effort": "1 day", "next": "None (Event Complete)"
            }
        ],
        'Tech Conference': [
            {
                "id": 1, "name": "Planning & Strategy", "categories": ["Management", "Planning", "Legal", "Strategy"],
                "purpose": "Define themes, goals, and core team structure.",
                "why": "A strong strategy attracts the right sponsors and attendees.",
                "steps": ["Select core theme", "Determine ticket pricing", "Set key KPIs", "Draft event budget"],
                "effort": "1 week", "next": "Venue & Logistics"
            },
            {
                "id": 2, "name": "Venue & Logistics", "categories": ["Logistics", "Venue", "Technical", "Equipment", "Catering"],
                "purpose": "Secure the physical space and technical infrastructure.",
                "why": "Conference quality is judged by venue accessibility and tech reliability.",
                "steps": ["Sign venue contract", "Test Wi-Fi capacity", "Review AV setup", "Finalize catering menu"],
                "effort": "2 weeks", "next": "Speaker Management"
            },
            {
                "id": 3, "name": "Speaker Management", "categories": ["Speakers", "Team", "Roles"],
                "purpose": "Curate and manage high-value technical content.",
                "why": "Speakers are the primary draw for tech audiences.",
                "steps": ["Call for proposals", "Review submissions", "Send speaker invites", "Collect slide decks"],
                "effort": "3-4 weeks", "next": "Marketing"
            },
            {
                "id": 4, "name": "Marketing", "categories": ["Marketing", "Promotion", "Sponsorship", "PR"],
                "purpose": "Drive ticket sales and brand awareness.",
                "why": "Visibility ensures a full house and ROI for sponsors.",
                "steps": ["Launch website", "Start social campaigns", "Send email blasts", "Issue press release"],
                "effort": "Ongoing", "next": "Operations"
            },
            {
                "id": 5, "name": "Operations", "categories": ["Operations", "Safety", "Security"],
                "purpose": "Manage on-site flow, registration, and safety.",
                "why": "Smooth operations allow attendees to focus on learning.",
                "steps": ["Set up badge printing", "Brief volunteers", "Install signage", "Review safety plan"],
                "effort": "3 days", "next": "Event Day Execution"
            },
            {
                "id": 6, "name": "Event Day Execution", "categories": ["Execution", "Final", "On-site"],
                "purpose": "Real-time management of the conference live dates.",
                "why": "Live execution is the ultimate test of months of planning.",
                "steps": ["Keynote management", "Monitor track timing", "Manage networking hub", "Handle live QA"],
                "effort": "1-3 days", "next": "None (Event Complete)"
            }
        ],
        'Festival': [
            {
                "id": 1, "name": "Mandal Planning", "categories": ["Management", "Planning", "Legal", "Strategy"],
                "purpose": "Define the vision and core committee for the festival.",
                "why": "Community festivals need strong leadership to manage local logistics.",
                "steps": ["Appoint treasurer", "Select idol/theme", "Set collection targets", "Draft event map"],
                "effort": "1 week", "next": "Permissions"
            },
            {
                "id": 2, "name": "Permissions", "categories": ["Legal", "Logistics"],
                "purpose": "Acquire all legal and local government clearances.",
                "why": "Legal compliance is mandatory to avoid shutdowns or fines.",
                "steps": ["Police NOC", "Fire Dept clearance", "Municipality permit", "Noise level permit"],
                "effort": "10-15 days", "next": "Decoration Setup"
            },
            {
                "id": 3, "name": "Decoration Setup", "categories": ["Technical", "Venue", "Decoration"],
                "purpose": "Build the festival's visual and physical environment.",
                "why": "Visual appeal creates the spiritual/celebratory atmosphere.",
                "steps": ["Build pandal/stage", "Install lighting", "Set up sound system", "Place idol/centerpiece"],
                "effort": "5 days", "next": "Volunteer Management"
            },
            {
                "id": 4, "name": "Volunteer Management", "categories": ["Volunteer", "Team", "Staffing"],
                "purpose": "Organize local manpower for smooth operations.",
                "why": "Volunteer energy is the lifeblood of non-profit festivals.",
                "steps": ["Assign gate duties", "Brief prasad team", "Distribute ID cards", "Set up WhatsApp hub"],
                "effort": "3 days", "next": "Daily Operations"
            },
            {
                "id": 5, "name": "Daily Operations", "categories": ["Operations", "Safety", "Catering"],
                "purpose": "Manage daily rituals, crowds, and food distribution.",
                "why": "Consistency ensures every visitor has a safe and holy experience.",
                "steps": ["Monitor Aarti times", "Manage crowd queues", "Supervise prasad kitchen", "Sanitation checks"],
                "effort": "10 days", "next": "Visarjan Planning"
            },
            {
                "id": 6, "name": "Visarjan Planning", "categories": ["Final", "Execution", "Risk"],
                "purpose": "Plan the final immersion/closing procession.",
                "why": "Processions are high-risk; planning ensures safety and order.",
                "steps": ["Rent truck/transport", "Book music/bands", "Brief security guards", "Define route"],
                "effort": "2 days", "next": "None (Event Complete)"
            }
        ]
    }

    # Default template if category not matched
    DEFAULT_TEMPLATE = [
        {"id": 1, "name": "Initial Planning", "categories": ["Management", "Planning", "Legal"], "purpose": "Establish goals.", "why": "Foundation.", "steps": ["Step 1"], "effort": "1 week", "next": "Next"},
        {"id": 2, "name": "Setup & Logistics", "categories": ["Logistics", "Venue", "Technical"], "purpose": "Secure site.", "why": "Presence.", "steps": ["Step 1"], "effort": "1 week", "next": "Next"},
        {"id": 3, "name": "Team & Volunteers", "categories": ["Team", "Volunteer"], "purpose": "Build team.", "why": "Manpower.", "steps": ["Step 1"], "effort": "1 week", "next": "Next"},
        {"id": 4, "name": "Publicity", "categories": ["Marketing", "Promotion", "Sponsorship"], "purpose": "Get audience.", "why": "ROI.", "steps": ["Step 1"], "effort": "1 week", "next": "Next"},
        {"id": 5, "name": "Execution & Operations", "categories": ["Operations", "Safety"], "purpose": "Run event.", "why": "Success.", "steps": ["Step 1"], "effort": "1 week", "next": "Next"},
        {"id": 6, "name": "Closing Phase", "categories": ["Final", "Execution", "Feedback"], "purpose": "Closure.", "why": "Record.", "steps": ["Step 1"], "effort": "1 week", "next": "End"}
    ]

    # Detect category from AI Analysis or Event Type
    ai_category = event.analysis.event_category if hasattr(event, 'analysis') and event.analysis else None
    display_category = ai_category or event.event_type or 'General Event'
    
    # Select Phase Definition
    phase_definitions = CATEGORY_PHASE_TEMPLATES.get(display_category, 
                         CATEGORY_PHASE_TEMPLATES.get(event.event_type, DEFAULT_TEMPLATE))
    
    execution_roadmap = []
    current_active_phase_id = None
    total_phases_completed = 0
    
    # Pre-fetch modules to link to milestones if needed
    module_list = list(modules)
    
    for phase in phase_definitions:
        # Mapping EventTimeline to Phases
        phase_milestones = roadmap.filter(category__in=phase['categories'])
        
        m_total = phase_milestones.count()
        m_done = phase_milestones.filter(status='Completed').count()
        
        # Logic for locking: A phase is locked if the previous phase is not 100%
        is_phase_locked = total_phases_completed < phase['id'] - 1
        
        completion = int((m_done / m_total) * 100) if m_total > 0 else (100 if not is_phase_locked and m_total == 0 else 0)
        
        status = "Upcoming"
        if completion == 100:
            status = "Completed"
            total_phases_completed += 1
        elif not is_phase_locked and current_active_phase_id is None:
            status = "In Progress"
            current_active_phase_id = phase['id']
        elif completion > 0:
            status = "In Progress"

        # Determine phase priority and risk
        phase_priority = "Medium"
        if phase_milestones.filter(priority='Critical').exists():
            phase_priority = "Critical"
            
        phase_risk = "Low"
        if phase_milestones.filter(status='Delayed').exists():
            phase_risk = "High"

        # Prepare milestones with guidance data
        processed_milestones = []
        milestones_list = list(phase_milestones)
        for i, m in enumerate(milestones_list):
            # Auto-link logic (existing)
            if not m.related_module:
                 search_terms = {
                    "Planning": ["planning", "strategy", "management"],
                    "Logistics": ["logistics", "transport", "technical"],
                    "Marketing": ["marketing", "promotion", "publicity", "studio"],
                    "Safety": ["safety", "security", "risk"],
                    "Registration": ["registration", "tickets"]
                }
                 for module_type, terms in search_terms.items():
                    if any(term in (m.title or "").lower() for term in terms):
                        target_module = next((mod for mod in module_list if any(term in mod.module_name.lower() for term in terms)), None)
                        if target_module:
                            m.related_module = target_module
                            m.save()
                            break

            # AUTOMATIC COMPLETION LOGIC (Phase 5 Smart Automation)
            if m.status != 'Completed':
                # Trigger 1: Module Entry Sync
                if m.related_module and m.related_module.entries.count() > 0:
                    m.status = 'Completed'
                # Trigger 2: Marketing Content Generation
                elif "Marketing" in (m.title or "") and marketing_items.count() >= 3:
                    m.status = 'Completed'
                # Trigger 3: Budget Planning Data
                elif "Budget" in (m.title or "") and budget_items.count() > 0:
                    m.status = 'Completed'
                # Trigger 4: Registration Module Activity
                elif "Registration" in (m.title or ""):
                    reg_mod = modules.filter(module_name__icontains="Registration").first()
                    if reg_mod and reg_mod.entries.count() > 0:
                        m.status = 'Completed'
                # Trigger 5: Volunteer/Staff Module Activity
                elif "Volunteer" in (m.title or "") or "Staff" in (m.title or ""):
                    vol_mod = modules.filter(module_name__icontains="Volunteer").first()
                    if vol_mod and vol_mod.entries.count() > 0:
                        m.status = 'Completed'
                
                if m.status == 'Completed':
                    m.completion_percentage = 100
                    m.completed_at = timezone.now()
                    m.save()
            
            # Interactive Checklist Logic
            # We generate checklists based on title keywords if no explicit data
            checklist = []
            checklist_items = ["Initial review", "Documentation check", "Team briefing", "Final verification"]
            if "Setup" in m.title: checklist_items = ["Physical layout", "Equipment test", "Safety walk", "Power backup"]
            elif "Marketing" in m.title: checklist_items = ["Posters design", "Social media schedule", "Email blast", "Ad spend review"]
            
            # Map items to status
            for item in checklist_items:
                checklist.append({"task": item, "is_done": m.status == 'Completed'})

            processed_milestones.append({
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "status": m.status,
                "priority": m.priority,
                "is_locked": is_phase_locked or (i > 0 and milestones_list[i-1].status != 'Completed'),
                "completed_at": m.completed_at,
                "module_slug": m.related_module.slug if m.related_module else None,
                "assigned_role": m.assigned_role,
                "due_date": m.due_date,
                "checklist": checklist,
                "purpose": f"Finalize {m.title} to progress in {phase['name']}.", 
                "why": "Essential component of the event's critical path.",
                "effort": "1-3 hours",
            })
            
        execution_roadmap.append({
            "id": phase['id'],
            "name": phase['name'],
            "status": status,
            "is_locked": is_phase_locked,
            "completion": completion,
            "milestones": processed_milestones,
            "m_total": m_total,
            "m_done": m_done,
            "priority": phase_priority,
            "risk": phase_risk,
            "purpose": phase.get("purpose"),
            "why": phase.get("why"),
            "steps": phase.get("steps", []),
            "effort_est": phase.get("effort"),
            "next_phase": phase.get("next"),
            "owner": phase_milestones.first().assigned_role if phase_milestones.exists() else "Ops Lead"
        })

    # Resolve Active Phase Object
    if current_active_phase_id is None:
        current_active_phase_id = 1
        
    active_phase = next(
        (p for p in execution_roadmap if p["id"] == current_active_phase_id),
        execution_roadmap[0] if execution_roadmap else {"name": "General Planning", "id": 1}
    )

    # --- PHASE 2: EXPLAINABLE READINESS SCORE ---
    # Define critical operational pillars
    readiness_pillars = [
        {"id": "planning", "name": "Initial Planning", "target_phase": 1, "status": "Missing"},
        {"id": "venue", "name": "Venue Confirmation", "target_phase": 2, "status": "Missing"},
        {"id": "team", "name": "Staffing & Team", "target_phase": 3, "status": "Missing"},
        {"id": "marketing", "name": "Marketing Launch", "target_phase": 4, "status": "Missing"},
        {"id": "ops", "name": "Operations Setup", "target_phase": 5, "status": "Missing"},
    ]
    
    completed_pillars = []
    missing_pillars_list = []
    next_readiness_milestone = None
    
    for pillar in readiness_pillars:
        phase_done = any(p['id'] == pillar['target_phase'] and p['status'] == 'Completed' for p in execution_roadmap)
        if phase_done:
            pillar['status'] = 'Completed'
            completed_pillars.append(pillar['name'])
        else:
            missing_pillars_list.append(pillar['name'])
            if not next_readiness_milestone:
                next_readiness_milestone = pillar['name']

    # Recalculate progress based on roadmap completion (more accurate for readiness)
    roadmap_progress = int((total_phases_completed / len(phase_definitions)) * 100) if phase_definitions else 0
    # Blend with task progress for granular feel
    readiness_score = int((roadmap_progress * 0.7) + (progress * 0.3))
    
    # Path to next level
    path_to_increase = f"Complete {next_readiness_milestone}" if next_readiness_milestone else "Maintain operations"
    target_score = min(100, readiness_score + 20) if next_readiness_milestone else 100

    # --- PHASE 1 & 4: REFINED AI COMMAND CENTER ---
    # Identify "Next Best Action" with explicit Reasoning
    next_action_m = None
    reasoning = "Finalize current tasks to stay on schedule."
    
    for phase in execution_roadmap:
        for m in phase['milestones']:
            if m['status'] != 'Completed' and not m['is_locked']:
                next_action_m = m
                break
        if next_action_m: 
            # Derive reasoning based on milestone data
            if "Venue" in next_action_m['title'] or "Ground" in next_action_m['title']:
                reasoning = "Logistics and scheduling depend on a confirmed physical location."
            elif "Marketing" in next_action_m['title'] or "Registration" in next_action_m['title']:
                reasoning = "Attendee acquisition is critical for budget and scaling."
            elif "Team" in next_action_m['title'] or "Volunteer" in next_action_m['title']:
                reasoning = "Manpower is required to execute the operational blueprint."
            elif "Planning" in next_action_m['title']:
                reasoning = "Establishing a clear strategy prevents mid-event scope creep."
            break

    ai_guidance = {
        "current_focus": active_phase['name'],
        "next_action": next_action_m['title'] if next_action_m else "Event Ready!",
        "est_time": next_action_m['effort'] if next_action_m else "0 mins",
        "priority": next_action_m['priority'] if next_action_m else "Low",
        "reasoning": reasoning,
        "module_slug": next_action_m['module_slug'] if next_action_m else None
    }

    # Identify Next Critical Milestone
    next_milestone = roadmap.filter(status__in=['Pending', 'In Progress']).order_by('priority', 'due_date').first()
    blocked_tasks = tasks.filter(priority='Critical').exclude(status='Done').count()
    
    # AI Recommendations for Roadmap
    roadmap_recommendations = []
    if blocked_tasks > 0:
        roadmap_recommendations.append(f"Resolve {blocked_tasks} blocked critical tasks in Phase {current_active_phase_id}.")
    
    if event.analysis:
        if int(event.analysis.team_planning.get('counts', {}).get('volunteers', 0)) < 5:
            roadmap_recommendations.append("Volunteer count is below threshold for optimized operations.")
        
        if event.analysis.risk_level == "High":
             roadmap_recommendations.append("High risk detected. Review Operations phase immediately.")

    if marketing_items.count() < 3:
        roadmap_recommendations.append("Generate more marketing assets to accelerate Promotion phase.")

    return render(request, 'events/workspace.html', {
        'event': event,
        'modules': modules,
        'execution_roadmap': execution_roadmap,
        'active_phase': active_phase,
        'current_active_phase': current_active_phase_id,
        'ai_guidance': ai_guidance,
        'completed_pillars': completed_pillars,
        'missing_pillars_list': missing_pillars_list,
        'missing_pillars': missing_pillars_list,
        'path_to_increase': path_to_increase,
        'target_score': target_score,
        'readiness_score': readiness_score,
        'progress': progress,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'blocked_tasks': blocked_tasks,
        'next_milestone': next_milestone,
        'roadmap_recommendations': roadmap_recommendations,
        'lane_pending': lane_todo,
        'lane_progress': lane_inprogress,
        'lane_completed': lane_done,
        'tasks': tasks,
        'budget_items': budget_items,
        'budget_summary': budget_summary,
        'marketing_items': marketing_items,
        'recent_logs': recent_logs,
    })

@login_required
def module_detail(request, event_id, module_id):
    event = get_object_or_404(Event, id=event_id)
    check_event_access(request.user, event)
    
    module = get_object_or_404(EventModule, id=module_id, event=event)
    return _module_detail_render(request, event, module)

@login_required
def module_detail_slug(request, event_id, module_slug):
    event = get_object_or_404(Event, id=event_id)
    check_event_access(request.user, event)
    
    module = get_object_or_404(EventModule, slug=module_slug, event=event)
    return _module_detail_render(request, event, module)

def _module_detail_render(request, event, module):
    if request.method == "POST":
        form_data = {field['name']: request.POST.get(field['name']) for field in module.form_schema}
        ModuleEntry.objects.create(module=module, data_json=form_data)
        AuditLog.objects.create(event=event, user=request.user, action=f"Added entry to {module.module_name}")
        messages.success(request, "Entry recorded.")
        return redirect('events:module_detail', event_id=event.id, module_id=module.id)
    
    entries = module.entries.all().order_by('-created_at')
    return render(request, 'events/module_detail.html', {'event': event, 'module': module, 'entries': entries})

@login_required
def update_task_status(request, task_id):
    if request.method == "POST":
        # Check both Timeline and Task models for compatibility
        try:
            task = EventTask.objects.get(id=task_id)
            is_kanban = True
        except EventTask.DoesNotExist:
            task = get_object_or_404(EventTimeline, id=task_id)
            is_kanban = False

        check_event_access(request.user, task.event)
        
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except json.JSONDecodeError:
            new_status = request.POST.get('status')

        # Normalize status mapping between models
        status_map = {
            'To Do': 'To Do' if is_kanban else 'Pending',
            'Pending': 'To Do' if is_kanban else 'Pending',
            'In Progress': 'In Progress',
            'Completed': 'Done' if is_kanban else 'Completed',
            'Done': 'Done' if is_kanban else 'Completed'
        }
        
        target_status = status_map.get(new_status, new_status)
        task.status = target_status
        task.save()
        
        AuditLog.objects.create(event=task.event, user=request.user, action=f"Updated task '{task.title}' to {target_status}")
        
        event = task.event
        tasks = event.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='Done').count()
        pending_tasks = tasks.filter(status='To Do').count()
        
        progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        return JsonResponse({
            'status': 'success',
            'progress': progress,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'task_id': task.id,
            'new_status': task.status
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_milestone_status(request, milestone_id):
    if request.method == "POST":
        milestone = get_object_or_404(EventTimeline, id=milestone_id)
        check_event_access(request.user, milestone.event)
        
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except json.JSONDecodeError:
            new_status = request.POST.get('status')

        if new_status == 'Completed':
            milestone.status = 'Completed'
            milestone.completed_at = timezone.now()
        else:
            milestone.status = 'Pending'
            milestone.completed_at = None
        
        milestone.save()
        
        AuditLog.objects.create(
            event=milestone.event, 
            user=request.user, 
            action=f"Milestone '{milestone.title}' marked as {milestone.status}"
        )
        
        return JsonResponse({'status': 'success', 'new_status': milestone.status})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def audit_logs(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    check_event_access(request.user, event)
    
    logs_list = event.audit_logs.all().order_by('-timestamp')
    
    # Filtering logic
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'event':
        logs_list = logs_list.filter(action__icontains='Event')
    elif filter_type == 'task':
        logs_list = logs_list.filter(action__icontains='task')
    elif filter_type == 'marketing':
        logs_list = logs_list.filter(action__icontains='marketing')
    elif filter_type == 'module':
        logs_list = logs_list.filter(action__icontains='entry')
        
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(logs_list, 15)  # 15 logs per page
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)
        
    return render(request, 'events/audit_logs.html', {
        'event': event,
        'logs': logs,
        'current_filter': filter_type,
    })
