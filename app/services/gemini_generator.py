import json
from ..config import get_settings
from ..schemas import DayPlan, Exercise, UserInput, WorkoutPlan


SYSTEM = """You are FitBuddy, a careful wellness planning assistant. Create practical, beginner-friendly fitness plans.
Do not diagnose or treat medical conditions. Avoid dangerous exercise prescriptions. Respect the requested intensity.
Return exactly 7 days. Include warm-up, exercises with sets/reps or duration, rest, and cooldown for every day.
Include at least one recovery/rest-oriented day in the week. Keep advice concise and actionable."""


def _client():
    settings = get_settings()
    if not settings.ai_enabled or not settings.gemini_api_key:
        return None
    from google import genai
    return genai.Client(api_key=settings.gemini_api_key)


def _demo_plan(user: UserInput) -> WorkoutPlan:
    base = [
        ("Day 1", "Full body strength"), ("Day 2", "Cardio + core"),
        ("Day 3", "Upper body strength"), ("Day 4", "Active recovery"),
        ("Day 5", "Lower body strength"), ("Day 6", "Cardio + mobility"),
        ("Day 7", "Rest and recovery"),
    ]
    exercises = {
        "strength": [("Squat", "3 x 10", "60–90 sec"), ("Push-up", "3 x 8–12", "60 sec"), ("Row", "3 x 10", "60 sec")],
        "cardio": [("Brisk walk", "20 min", "as needed"), ("Marching", "10 min", "30 sec")],
        "core": [("Plank", "3 x 20–40 sec", "45 sec"), ("Dead bug", "3 x 8/side", "45 sec")],
        "mobility": [("Hip mobility", "8 min", "as needed"), ("Shoulder mobility", "8 min", "as needed")],
    }
    days = []
    for day, focus in base:
        key = "strength" if "strength" in focus.lower() or "body" in focus.lower() else "cardio" if "cardio" in focus.lower() else "core" if "core" in focus.lower() else "mobility"
        if focus.startswith("Rest"):
            ex = [Exercise(name="Easy walking or gentle stretching", sets_reps="10–20 min optional", rest="Comfortable pace")]
        elif focus == "Active recovery":
            ex = [Exercise(name="Easy walk", sets_reps="15–25 min", rest="As needed"), Exercise(name="Gentle stretching", sets_reps="8–10 min", rest="As needed")]
        else:
            ex = [Exercise(name=a, sets_reps=b, rest=c) for a, b, c in exercises[key]]
        days.append(DayPlan(day=day, focus=focus, warmup="5–10 min easy movement and joint mobility.", exercises=ex, cooldown="5–10 min easy movement and gentle stretching."))
    return WorkoutPlan(days=days)


def generate_workout_gemini(user: UserInput) -> str:
    client = _client()
    if client is None:
        plan = _demo_plan(user)
        return json.dumps(plan.model_dump(), indent=2)

    prompt = f"Create a 7-day workout plan for: name={user.name}, age={user.age}, weight={user.weight} kg, goal={user.goal}, intensity={user.intensity}."
    from google.genai import types
    response = client.models.generate_content(
        model=get_settings().gemini_workout_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            response_mime_type="application/json",
            response_schema=WorkoutPlan,
            temperature=0.4,
        ),
    )
    parsed = response.parsed or WorkoutPlan.model_validate_json(response.text)
    return json.dumps(parsed.model_dump(), indent=2)
