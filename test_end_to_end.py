import os
import sys
import json
from unittest.mock import patch

sys.path.append('d:/Study/Full Stack Development/My Projects/EventAI')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()

from event_planner.services.event_generator import generate_event_plan
from event_planner.models import AIEventPlan

class MockResponse:
    def __init__(self):
        self.text = '```json\n{"event_name": "AI NY Meetup", "overview": "A brief summary", "location": "New York", "attendees": 100, "duration": "1 Day", "budget": 10000, "schedule": [{"time": "09:00 AM", "activity": "Networking"}], "resources": [], "budget_breakdown": [], "tasks": [{"task": "Book venue", "completed": false}], "risks": [], "recommendations": "Have fun!"}\n```'

def mock_generate(*args, **kwargs):
    return MockResponse()

def run_test():
    print("Testing End-to-End JSON Parsing...")
    
    # 1. Prompt
    prompt_text = "AI developers meetup in New York for 100 people. Focus on networking. Budget: $10,000."
    
    # 2. Gemini + JSON Parse
    with patch('google.genai.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.models.generate_content = mock_generate
        
        result = generate_event_plan(prompt_text)
        print('JSON Parsing Result:', result)
        
    if "error" in result:
        print("Test Failed:", result["error"])
        return
        
    # 3. Database Save
    plan = AIEventPlan.objects.create(
        prompt=prompt_text,
        event_name=result.get('event_name'),
        generated_plan_json=result
    )
    print(f'DB Count: {AIEventPlan.objects.count()}')
    print(f'Latest Event Saved: {plan.event_name}')
    
run_test()
