import json
from django.shortcuts import render
from django.http import JsonResponse
from .models import AIEventPlan
from .services.event_generator import generate_event_plan

def planner_home(request, pk=None):
    drafts = AIEventPlan.objects.filter(status='DRAFT').order_by('-updated_at')[:5]
    
    current_draft = None
    if pk:
        current_draft = get_object_or_404(AIEventPlan, pk=pk, status='DRAFT')

    if request.method == "POST":
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        prompt_text = request.POST.get("prompt")
        draft_id = request.POST.get("draft_id")
        
        if is_ajax and not prompt_text:
            try:
                data = json.loads(request.body)
                prompt_text = data.get("prompt")
                draft_id = data.get("draft_id") or draft_id
            except:
                pass
                
        if not prompt_text:
            if is_ajax:
                return JsonResponse({"error": "Prompt is required."}, status=400)
            return render(request, 'event_planner/home.html', {"error": "Prompt is required.", "recent_drafts": drafts})

        plan_data = generate_event_plan(prompt_text)
        
        if "error" in plan_data:
            if is_ajax:
                return JsonResponse({"error": plan_data["error"]}, status=500)
            return render(request, 'event_planner/home.html', {"error": plan_data["error"], "prompt": prompt_text, "recent_drafts": drafts})

        if draft_id:
            plan = get_object_or_404(AIEventPlan, pk=draft_id)
            plan.prompt = prompt_text
            plan.event_name = plan_data.get("event_name", "Untitled Event")
            plan.generated_plan_json = plan_data
            plan.status = 'DRAFT'
            plan.save()
        else:
            plan = AIEventPlan.objects.create(
                prompt=prompt_text,
                event_name=plan_data.get("event_name", "Untitled Event"),
                generated_plan_json=plan_data,
                status='DRAFT'
            )

        if is_ajax:
            return JsonResponse({"plan": plan_data, "id": str(plan.id)})
            
        return render(request, 'event_planner/home.html', {"plan": plan_data, "prompt": prompt_text, "current_draft": plan, "recent_drafts": drafts})

    return render(request, 'event_planner/home.html', {
        "current_draft": current_draft, 
        "recent_drafts": drafts,
        "plan": current_draft.generated_plan_json if current_draft else None,
        "prompt": current_draft.prompt if current_draft else ""
    })

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

def plan_history(request):
    plans_list = AIEventPlan.objects.filter(status='PUBLISHED')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        plans_list = plans_list.filter(event_name__icontains=search_query)
        
    # Sort
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'budget_asc':
        # Need to sort by JSON field budget - requires raw SQL or specific ORM in Django 3.2+
        # Using raw order_by on json field
        plans_list = plans_list.order_by('generated_plan_json__budget')
    elif sort_by == 'budget_desc':
        plans_list = plans_list.order_by('-generated_plan_json__budget')
    elif sort_by == 'attendees_asc':
        plans_list = plans_list.order_by('generated_plan_json__attendees')
    elif sort_by == 'attendees_desc':
        plans_list = plans_list.order_by('-generated_plan_json__attendees')
    else: # newest
        plans_list = plans_list.order_by('-created_at')

    paginator = Paginator(plans_list, 10) # Show 10 plans per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'event_planner/history.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by
    })

def plan_detail(request, pk):
    plan = get_object_or_404(AIEventPlan, pk=pk)
    
    # We pass the plan object to the template. 
    # Since generated_plan_json is a JSONField, it behaves like a dict.
    return render(request, 'event_planner/detail.html', {'plan': plan, 'json_data': plan.generated_plan_json})

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_POST
def delete_draft(request, pk):
    plan = get_object_or_404(AIEventPlan, pk=pk, status='DRAFT')
    plan.delete()
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
def publish_draft(request, pk):
    plan = get_object_or_404(AIEventPlan, pk=pk, status='DRAFT')
    plan.status = 'PUBLISHED'
    plan.save()
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
def auto_save_draft(request):
    try:
        data = json.loads(request.body)
        draft_id = data.get('draft_id')
        prompt_text = data.get('prompt', '')
        
        if draft_id:
            plan = get_object_or_404(AIEventPlan, pk=draft_id, status='DRAFT')
            plan.prompt = prompt_text
            plan.save()
            return JsonResponse({'success': True, 'id': str(plan.id)})
        else:
            if prompt_text.strip():
                plan = AIEventPlan.objects.create(prompt=prompt_text, status='DRAFT')
                return JsonResponse({'success': True, 'id': str(plan.id)})
    except Exception as e:
        pass
    return JsonResponse({'success': False}, status=400)

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_POST
def toggle_task(request, pk):
    plan = get_object_or_404(AIEventPlan, pk=pk)
    try:
        data = json.loads(request.body)
        task_index = data.get('task_index')
        completed = data.get('completed')
        
        if task_index is not None and completed is not None:
            # Update the JSON data
            plan_json = plan.generated_plan_json
            if 'tasks' in plan_json and 0 <= task_index < len(plan_json['tasks']):
                plan_json['tasks'][task_index]['completed'] = completed
                plan.generated_plan_json = plan_json
                plan.save()
                return JsonResponse({'success': True})
    except Exception as e:
        pass
    
    return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

