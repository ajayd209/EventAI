import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

def generate_event_plan(prompt_text):
    """
    Generates a structured event plan based on user prompt.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY missing.")
        return {"error": "AI service is currently unavailable due to missing API Key."}

    client = genai.Client(api_key=api_key)

    system_prompt = f"""
    You are an expert AI Event Generator. Based on the user's event description, create a detailed, comprehensive event plan.
    
    User Description:
    {prompt_text}
    
    You MUST return ONLY a valid JSON object matching the following structure exactly. Do not use Markdown formatting.
    {{
        "event_name": "Name of the event",
        "overview": "A brief engaging summary of the event",
        "location": "Event location",
        "attendees": 150,
        "duration": "e.g., One Day Event, 2 Days, etc.",
        "budget": 80000,
        "schedule": [
            {{"time": "08:00 AM", "activity": "Registration & Welcome"}}
        ],
        "resources": [
            {{"item": "Volunteers", "quantity": "15"}},
            {{"item": "Sports Equipment", "quantity": "Yes"}}
        ],
        "budget_breakdown": [
            {{"category": "Venue & Permits", "amount": 15000}}
        ],
        "tasks": [
            {{"task": "Book venue", "completed": false}}
        ],
        "risks": [
            "Keep a backup plan in case of rain.",
            "Ensure proper hydration & first aid support."
        ],
        "recommendations": "This event has great potential for community engagement and healthy participation!"
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
            ),
        )
        content = response.text.strip()
        logger.info(f"Raw response length: {len(content)}")
        
        # Clean markdown code fences
        clean_content = content
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        elif clean_content.startswith("```"):
            clean_content = clean_content[3:]
            
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
            
        clean_content = clean_content.strip()
        
        try:
            result = json.loads(clean_content)
            logger.info("JSON parsing successful.")
            return result
        except json.JSONDecodeError as je:
            logger.error(f"JSON parsing failed. Raw response: {content}")
            return {"error": "Failed to parse AI response into valid JSON."}
            
    except Exception as e:
        logger.exception(f"AI Generation failed: {str(e)}")
        return {"error": "Failed to generate event plan."}
