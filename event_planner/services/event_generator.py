import os
import json
import logging
from google import genai
from google.genai import types
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_json(content):
    c = content.strip()
    if c.startswith("```json"):
        c = c[7:]
    elif c.startswith("```"):
        c = c[3:]
    if c.endswith("```"):
        c = c[:-3]
    return c.strip()


def parse_time_to_minutes(t_str):
    """Helper to convert '09:00 AM' or '09:00 AM - 10:00 AM' start times to minutes for overlap checking."""
    try:
        t = t_str.split("-")[0].strip()
        t = t.replace(":", " ")
        parts = t.split()
        if len(parts) >= 2:
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 2 and parts[1].isdigit() else 0
            is_pm = "PM" in t_str.upper()
            if is_pm and h != 12:
                h += 12
            if not is_pm and h == 12:
                h = 0
            return h * 60 + m
    except:
        pass
    return 0


def generate_event_plan(prompt_text):
    """
    Generates a structured event plan using MULTI-STAGE AI REASONING.
    Upgraded to EventAI Intelligence Engine V1.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY missing.")
        return {"error": "AI service is currently unavailable due to missing API Key."}

    client = genai.Client(api_key=api_key)

    # ---------------------------------------------------------
    # PHASE 1: FACT EXTRACTION ENGINE & EVENT CLASSIFICATION
    # ---------------------------------------------------------
    extraction_prompt = f"""
You are an expert Event Fact Extraction Engine.
Extract facts explicitly mentioned in the user's event request.
Classify the event into one of the following categories:
CRICKET_EVENT, FOOTBALL_EVENT, PRIZE_DISTRIBUTION, HACKATHON, CONFERENCE, SEMINAR, WORKSHOP, MEETUP, WEDDING, BIRTHDAY, CULTURAL_PROGRAM, COLLEGE_EVENT, COMMUNITY_EVENT, OTHER

INPUT:
{prompt_text}

OUTPUT MUST BE STRICT JSON matching this schema exactly:
{{
"event_category": "",
"event_type": "",
"event_name": "",
"location": "",
"date": "",
"start_time": "",
"end_time": "",
"attendees": 0,
"budget": 0,
"prize_money": 0,
"duration_hours": 0,
"missing_information": []
}}
"""
    try:
        ext_resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=extraction_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        facts = json.loads(clean_json(ext_resp.text))
        logger.info(f"Phase 1 Facts Extracted: {facts}")
    except Exception as e:
        logger.exception("Phase 1 Extraction failed")
        return {"error": "Failed to extract facts from prompt."}

    # ---------------------------------------------------------
    # PHASE 5: MISSING INFORMATION ENGINE
    # ---------------------------------------------------------
    critical_missing = []
    if not facts.get("date"):
        critical_missing.append("What is the event date?")
    if not facts.get("location"):
        critical_missing.append("What is the venue location?")

    if critical_missing:
        # Halt execution and return clarification request
        # The frontend expects 'error' key to display the alert
        return {
            "error": "Needs Clarification:\n" + "\n".join(critical_missing),
            "needs_clarification": True,
            "questions": critical_missing,
        }

    # ---------------------------------------------------------
    # PHASE 9: EVENT CONFIDENCE SCORE
    # ---------------------------------------------------------
    conf = 95
    if not facts.get("start_time"):
        conf -= 10
    if not facts.get("budget"):
        conf -= 15
    if not facts.get("attendees"):
        conf -= 10
    confidence_score = max(0, conf)

    # ---------------------------------------------------------
    # PHASE 2: ATTENDEE RESOURCE ENGINE (Python Logic)
    # ---------------------------------------------------------
    try:
        attendees = int(facts.get("attendees") or 0)
    except ValueError:
        attendees = 0

    if attendees <= 100:
        calc_vols = 4
        calc_sec = 1
    elif attendees <= 300:
        calc_vols = 8
        calc_sec = 2
    elif attendees <= 500:
        calc_vols = 12
        calc_sec = 3
    else:
        calc_vols = 20
        calc_sec = 5

    resource_baseline = f"Volunteers: {calc_vols}, Security: {calc_sec}"

    # ---------------------------------------------------------
    # PHASE 3: BUDGET INTELLIGENCE ENGINE (Python Logic)
    # ---------------------------------------------------------
    try:
        budget = float(facts.get("budget") or 0)
    except ValueError:
        budget = 0

    try:
        prize_money = float(facts.get("prize_money") or 0)
    except ValueError:
        prize_money = 0

    if budget < 0:
        return {"error": "Budget cannot be negative."}
    if attendees < 0:
        return {"error": "Attendees cannot be negative."}
    if budget > 0 and prize_money > budget:
        return {"error": "Prize money cannot exceed total event budget."}

    remaining_budget = budget - prize_money
    budget_baseline = f"Total Budget: {budget}. Prize Money: {prize_money}. Remaining: {remaining_budget}. Allocate remaining strictly among Venue, Food, Certificates, Sound, Contingency, etc."

    # ---------------------------------------------------------
    # PHASE 4: LOCATION INTELLIGENCE (Python Logic)
    # ---------------------------------------------------------
    loc = facts.get("location", "").lower()
    loc_intel = ""
    if "nashik" in loc:
        loc_intel = "Suggest Cricket grounds, Community halls, Parking considerations."
    elif "pune" in loc:
        loc_intel = "Suggest IT audience assumptions, Higher venue costs."
    elif "mumbai" in loc:
        loc_intel = "Suggest Traffic planning, Premium venue pricing."

    # ---------------------------------------------------------
    # PHASE 6: RISK INTELLIGENCE ENGINE (Python Logic)
    # ---------------------------------------------------------
    cat = facts.get("event_category", "").upper()
    baseline_risks = []
    if "CRICKET" in cat:
        baseline_risks = [
            "Rain affecting ground",
            "Trophy delivery delays",
            "Ground availability issues",
            "Guest arrival delays",
        ]
    elif "HACKATHON" in cat:
        baseline_risks = ["Internet outage", "Power issues", "Mentor shortage"]
    elif "CONFERENCE" in cat or "SEMINAR" in cat:
        baseline_risks = ["Speaker cancellation", "AV equipment failure"]
    elif "WEDDING" in cat:
        baseline_risks = ["Catering delays", "Weather impact", "Guest transport issues"]

    # ---------------------------------------------------------
    # PLANNING ENGINE CALL
    # ---------------------------------------------------------
    planning_prompt = f"""
You are a Professional Event Intelligence Engine.
Generate a structured event plan using ONLY the extracted facts and deterministic baselines provided below.

EXTRACTED FACTS:
{json.dumps(facts, indent=2)}

PYTHON BASELINES TO STRICTLY FOLLOW:
- Resources: Use exactly -> {resource_baseline}. You may add others and explain reasoning.
- Budget constraints: {budget_baseline}
- Location considerations: {loc_intel if loc_intel else 'Standard location planning.'}
- Baseline Risks to include: {', '.join(baseline_risks) if baseline_risks else 'Generate highly specific risks.'}

STRICT RULES:
1. EVENT PLANNER: Never change date, attendees, budget, prize money, location, or duration. Mark any assumed resources clearly (e.g., "Assumed Resource: Projector").
2. RESOURCE REASONING: Every resource must have reasoning included in its item name. Format -> "Item Name (Reason: why it's needed)".
3. SCHEDULE GENERATOR: Schedule must fit exactly inside the provided times. No overlapping tasks.
4. BUDGET ENGINE: Budget must always balance perfectly. SUM(budget_breakdown) MUST exactly equal the total budget ({budget}). Verify mathematically before outputting.
5. RISK ENGINE: Include the baseline risks provided and expand if necessary. No generic risks.
6. RECOMMENDATION ENGINE: Recommendations must be actionable and highly specific to the event context. No generic advice.
7. OUTPUT FORMAT: Return STRICT JSON ONLY matching the following schema.

EXPECTED JSON SCHEMA:
{{
    "event_name": "Name of the event",
    "overview": "A brief engaging summary of the event",
    "location": "Event location",
    "attendees": 150,
    "duration": "e.g., One Day Event, 2 Days, etc.",
    "budget": 80000,
    "schedule": [
        {{"time": "08:00 AM - 09:00 AM", "activity": "Registration & Welcome"}}
    ],
    "resources": [
        {{"item": "Volunteers (Reason: 2 Registration, 2 Stage)", "quantity": "4"}},
        {{"item": "Security (Reason: entry management)", "quantity": "1"}}
    ],
    "budget_breakdown": [
        {{"category": "Venue & Permits", "amount": 15000}}
    ],
    "tasks": [
        {{"task": "Book venue", "completed": false}}
    ],
    "risks": [
        "Specific risk 1"
    ],
    "recommendations": "Actionable, specific recommendation."
}}
"""
    try:
        plan_resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=planning_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        plan_content = clean_json(plan_resp.text)
        result = json.loads(plan_content)

        # ---------------------------------------------------------
        # PHASE 7: VALIDATION ENGINE V2
        # ---------------------------------------------------------
        # Validate Schedule Overlap (Basic check that times strictly advance)
        if "schedule" in result:
            prev_time = -1
            for item in result["schedule"]:
                t = parse_time_to_minutes(item.get("time", ""))
                if t > 0:
                    if t <= prev_time:
                        logger.warning(
                            f"Schedule overlap detected: {item.get('time')} comes after a later time."
                        )
                        # Could reject it completely, but let's just log and adjust quality score
                    prev_time = t

        # ---------------------------------------------------------
        # PHASE 8: PLAN QUALITY SCORING
        # ---------------------------------------------------------
        quality_score = 100

        # Budget balancing fallback
        if "budget_breakdown" in result and budget > 0:
            try:
                calc_total = sum(
                    float(
                        str(item.get("amount", 0))
                        .replace(",", "")
                        .replace("₹", "")
                        .replace("$", "")
                    )
                    for item in result["budget_breakdown"]
                )
                diff = budget - calc_total
                if abs(diff) > 0.01:
                    quality_score -= 15  # Penalty for LLM failing math
                    logger.warning(
                        f"Budget mismatch resolved programmatically: Expected {budget}, Calculated {calc_total}"
                    )
                    if diff > 0:
                        result["budget_breakdown"].append(
                            {
                                "category": "Contingency / Adjustments",
                                "amount": round(diff, 2),
                            }
                        )
                    else:
                        # Over budget -> reduce the largest category
                        if len(result["budget_breakdown"]) > 0:
                            largest_cat = max(
                                result["budget_breakdown"],
                                key=lambda x: float(
                                    str(x.get("amount", 0))
                                    .replace(",", "")
                                    .replace("₹", "")
                                    .replace("$", "")
                                ),
                            )
                            current_amt = float(
                                str(largest_cat["amount"])
                                .replace(",", "")
                                .replace("₹", "")
                                .replace("$", "")
                            )
                            new_amt = current_amt + diff
                            largest_cat["amount"] = round(
                                new_amt if new_amt > 0 else 0, 2
                            )
            except Exception as e:
                logger.error(f"Budget check fallback error: {e}")
                quality_score -= 20

        # Inject scores back into the result for frontend or DB
        result["plan_quality_score"] = f"{quality_score}/100"
        result["confidence_score"] = f"{confidence_score}%"

        logger.info(
            f"Phase 2-10 JSON generation and validation successful. Quality: {quality_score}, Confidence: {confidence_score}"
        )
        return result
    except Exception as e:
        logger.exception("AI Planning failed")
        return {"error": "Failed to generate comprehensive event plan."}
