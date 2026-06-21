from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .gemini_service import analyze_event, regenerate_marketing
from events.models import Event, EventModule, EventTimeline, BudgetPlan, BudgetSummary, MarketingContent, AuditLog
from .models import AIAnalysis
import logging
import json

logger = logging.getLogger(__name__)

from django.db import transaction

@login_required
def create_event_ai(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                event = Event.objects.create(
                    event_name=request.POST.get("event_name"),
                    event_type=request.POST.get("event_type"),
                    location=request.POST.get("location"),
                    event_date=request.POST.get("event_date"),
                    expected_crowd=request.POST.get("expected_crowd"),
                    budget=request.POST.get("budget") or 0,
                    prize_money=request.POST.get("prize_money") or 0,
                    created_by=request.user
                )
                AuditLog.objects.create(event=event, user=request.user, action="Event Created via AI")
                
                # Ensure event.event_date is a date object (it might be a string immediately after creation)
                if isinstance(event.event_date, str):
                    event.event_date = datetime.strptime(event.event_date, "%Y-%m-%d").date()

                event_data = {
                    "event_name": event.event_name,
                    "event_type": event.event_type,
                    "location": event.location,
                    "event_date": str(event.event_date),
                    "expected_crowd": event.expected_crowd,
                    "budget": float(event.budget),
                }
                
                logger.info(f"Requesting AI analysis for event {event.id}")
                analysis_result = analyze_event(event_data)

                if "error" in analysis_result:
                    raise Exception(analysis_result["error"])

                # 1. AI Analysis & Intelligence Hub
                exec_sum = analysis_result.get("executive_summary", {})
                team_plan = analysis_result.get("team_planning", {})
                AIAnalysis.objects.create(
                    event=event,
                    event_category=exec_sum.get("event_category", "Unknown"),
                    risk_level=exec_sum.get("risk_level", "Medium"),
                    volunteers_required=str(team_plan.get("counts", {}).get("volunteers", "0")),
                    security_required=str(team_plan.get("counts", {}).get("security", "0")),
                    risk_intelligence=analysis_result.get("risk_intelligence", []),
                    team_planning=team_plan,
                    analytics=analysis_result.get("analytics", {}),
                    raw_ai_response=json.dumps(analysis_result)
                )

                # 2. Dynamic Modules
                for mod in analysis_result.get("modules", []):
                    EventModule.objects.create(
                        event=event, 
                        module_name=mod.get("name"),
                        description=mod.get("description", ""),
                        form_schema=mod.get("fields", [])
                    )

                # 3. Roadmap (Milestones)
                for item in analysis_result.get("roadmap", []):
                    days = item.get("days_before_event", 0)
                    EventTimeline.objects.create(
                        event=event, title=item.get("title"), description=item.get("description"),
                        priority=item.get("priority", "Medium"), category=item.get("category"),
                        days_before_event=days, due_date=event.event_date - timedelta(days=days),
                        assigned_role=item.get("assigned_role", "Organizer")
                    )

                # 4. Kanban Tasks
                from events.models import EventTask
                for task in analysis_result.get("kanban_tasks", []):
                    EventTask.objects.create(
                        event=event, title=task.get("title"), description=task.get("description"),
                        priority=task.get("priority", "Medium"), status=task.get("status", "To Do"),
                        days_before=task.get("days_before", 0)
                    )

                # 5. Financial Planning
                total_est = 0
                for b_item in analysis_result.get("budget", []):
                    cost = b_item.get("estimated_cost") or 0
                    total_est += cost
                    BudgetPlan.objects.create(
                        event=event, category=b_item.get("category"),
                        estimated_cost=cost, description=b_item.get("description")
                    )

                BudgetSummary.objects.create(
                    event=event, total_estimated_cost=total_est,
                    remaining_budget=float(event.budget) - float(total_est), 
                    risk_level=exec_sum.get("risk_level", "Low"),
                    ai_recommendation=f"Successfully allocated {total_est} from total budget."
                )

                # 6. Marketing Content Studio
                marketing_data = analysis_result.get("marketing", {})
                marketing_mapping = {
                    "description": "Description",
                    "instagram": "Instagram",
                    "facebook": "Facebook",
                    "whatsapp": "WhatsApp",
                    "linkedin": "LinkedIn",
                    "email_campaign": "EmailCampaign",
                    "sponsor_pitch": "SponsorPitch",
                    "press_release": "PressRelease",
                    "volunteer_recruitment": "VolunteerRecruitment",
                    "hashtags": "Hashtags"
                }
                
                for ai_key, content in marketing_data.items():
                    if content and ai_key in marketing_mapping:
                        content_type = marketing_mapping[ai_key]
                        MarketingContent.objects.create(
                            event=event,
                            content_type=content_type,
                            title=f"{content_type} Content",
                            content=content
                        )
                
                messages.success(request, f"Operational Plan for '{event.event_name}' generated successfully!")
                return redirect('events:workspace', event_id=event.id)

        except Exception as e:
            logger.exception(f"Critical failure in AI Event Generation: {str(e)}")
            messages.error(request, f"Generation Failed: {str(e)}")
            return redirect('dashboard:home')

    return render(request, 'pro/create_event_ai.html')

@login_required
def regenerate_marketing_view(request, event_id, content_type):
    event = get_object_or_404(Event, id=event_id)
    if event.created_by and event.created_by != request.user:
        raise PermissionDenied("You do not have access to this event.")
        
    event_data = {"event_name": event.event_name, "event_type": event.event_type, "location": event.location, "event_date": str(event.event_date)}
    
    result = regenerate_marketing(event_data, content_type)
    if "error" not in result:
        marketing_item, created = MarketingContent.objects.get_or_create(event=event, content_type=content_type.capitalize())
        marketing_item.content = result['content']
        marketing_item.save()
        AuditLog.objects.create(event=event, user=request.user, action=f"Regenerated marketing content: {content_type}")
        messages.success(request, f"{content_type.capitalize()} content regenerated!")
    else:
        messages.error(request, f"Regeneration failed: {result['error']}")
    
    return redirect('events:workspace', event_id=event.id)

from django.http import JsonResponse
from .gemini_service import query_copilot

@login_required
def copilot_query_view(request, event_id):
    if request.method == "POST":
        event = get_object_or_404(Event, id=event_id)
        if event.created_by and event.created_by != request.user:
            return JsonResponse({"error": "Unauthorized"}, status=403)
            
        try:
            data = json.loads(request.body)
            user_query = data.get("query")
        except:
            user_query = request.POST.get("query")

        if not user_query:
            return JsonResponse({"error": "No query provided"}, status=400)

        # Gather context
        critical_tasks = event.tasks.filter(priority='Critical').exclude(status='Done')
        budget_summary = event.budget_summary if hasattr(event, 'budget_summary') else None
        
        event_context = {
            "name": event.event_name,
            "type": event.event_type,
            "location": event.location,
            "readiness": event.analysis.analytics.get('readiness_score', 0) if event.analysis else 20,
            "active_phase": "Planning", 
            "next_action": "Secure Venue", 
            "budget_summary": f"Total Estimated: {budget_summary.total_estimated_cost if budget_summary else 'N/A'}",
            "critical_issues": ", ".join([t.title for t in critical_tasks[:3]]) if critical_tasks.exists() else "None"
        }
        
        response_text = query_copilot(event_context, user_query)
        return JsonResponse({"response": response_text})
        
    return JsonResponse({"error": "Invalid request"}, status=405)

