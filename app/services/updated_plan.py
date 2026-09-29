import json
from ..config import get_settings
from ..schemas import WorkoutPlan


def update_workout_plan(original_plan: str, feedback: str) -> str:
    settings = get_settings()
    if not settings.ai_enabled or not settings.gemini_api_key:
        try:
            data = json.loads(original_plan)
            data["feedback_applied"] = feedback
            return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            return original_plan + f"\n\nFeedback applied: {feedback}"

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"Original plan:\n{original_plan}\n\nUser feedback:\n{feedback}\n\nRevise the plan while preserving the 7-day structure and safety guidance."
    response = client.models.generate_content(
        model=settings.gemini_workout_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You revise fitness plans conservatively. Apply reasonable user feedback, keep exactly 7 days, and do not provide medical treatment. Return structured JSON.",
            response_mime_type="application/json",
            response_schema=WorkoutPlan,
            temperature=0.4,
        ),
    )
    parsed = response.parsed or WorkoutPlan.model_validate_json(response.text)
    return json.dumps(parsed.model_dump(), indent=2)
