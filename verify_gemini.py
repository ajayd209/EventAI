import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"DEBUG: Key starts with: {api_key[:5]}...")

if "your-gemini-api-key" in api_key:
    print("RESULT: KEY_IS_PLACEHOLDER")
else:
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents="Return JSON with key status='ok'",
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
            ),
        )
        print(f"RESULT: SUCCESS")
        print(f"RAW_RESPONSE: {response.text}")
    except Exception as e:
        print(f"RESULT: FAILED")
        print(f"ERROR: {str(e)}")
