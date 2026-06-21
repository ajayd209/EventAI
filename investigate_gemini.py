import os
import sys
import traceback

sys.path.append('d:/Study/Full Stack Development/My Projects/EventAI')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()

from event_planner.services.event_generator import generate_event_plan
from django.conf import settings

# 1. Print loaded API key (masked)
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("API_KEY_LOADED: None")
else:
    if len(api_key) <= 8:
        masked = "****"
    else:
        masked = f"{api_key[:4]}{'*' * (len(api_key)-8)}{api_key[-4:]}"
    print(f"API_KEY_LOADED: {masked}")

# 2. Trigger generation and print traceback
print("\n--- TRIGGERING GENERATION ---")
try:
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=api_key)
    
    print("MODEL_USED: gemini-1.5-flash")
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents="Hello",
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
        ),
    )
    print("GENERATION_SUCCESS: True")
    print(f"RESPONSE: {response.text}")
except Exception as e:
    print("GENERATION_SUCCESS: False")
    print("\n--- EXCEPTION TRACEBACK ---")
    traceback.print_exc()
    
    print("\n--- EXCEPTION DETAILS ---")
    print(f"EXCEPTION_TYPE: {type(e).__name__}")
    print(f"ERROR_MESSAGE: {str(e)}")
