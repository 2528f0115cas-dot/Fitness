from ..config import get_settings


def generate_nutrition_tip_with_flash(goal: str) -> str:
    settings = get_settings()
    demo = {
        "weight loss": "Build meals around vegetables, a protein source, whole-food carbohydrates, and water; use sustainable portions rather than extreme restriction.",
        "muscle gain": "Include a protein-rich food at each meal and a balanced post-workout meal or snack with protein and carbohydrates.",
        "general wellness": "Aim for regular balanced meals, plenty of water, fruits and vegetables, and consistent sleep and recovery habits.",
        "flexibility": "Stay hydrated and include regular balanced meals; adequate protein and overall nutrition support recovery from mobility work.",
        "endurance": "Pair regular hydration with carbohydrate-rich foods around longer training sessions and include adequate protein for recovery.",
    }
    if not settings.ai_enabled or not settings.gemini_api_key:
        return demo.get(goal, demo["general wellness"])

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_flash_model,
        contents=f"Give one concise, practical nutrition or recovery tip for a fitness user whose goal is {goal}. Avoid medical claims and extreme dieting.",
        config=types.GenerateContentConfig(
            system_instruction="You are a concise wellness assistant. Return only the tip in plain text.",
            temperature=0.5,
            max_output_tokens=180,
        ),
    )
    return (response.text or demo.get(goal, demo["general wellness"])).strip()
