from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import Plan, User
from .schemas import FeedbackRequest, HealthResponse, PlanResponse, UserInput
from .services.gemini_flash_generator import generate_nutrition_tip_with_flash
from .services.gemini_generator import generate_workout_gemini
from .services.updated_plan import update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _plan_response(user: User, plan: Plan, updated: bool = False) -> PlanResponse:
    return PlanResponse(
        user_id=user.user_id, name=user.name, age=user.age, weight=user.weight,
        goal=user.goal, intensity=user.intensity,
        workout_plan=plan.updated_plan if updated and plan.updated_plan else plan.original_plan,
        nutrition_tip=plan.updated_nutrition_tip if updated and plan.updated_nutrition_tip else plan.nutrition_tip,
        updated=updated,
    )


def _admin_required(token: str | None) -> None:
    if token != get_settings().admin_token:
        raise HTTPException(status_code=401, detail="Valid X-Admin-Token required")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(
    request: Request,
    user_id: str = Form(...), name: str = Form(...), age: int = Form(...),
    weight: float = Form(...), goal: str = Form(...), intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user_input = UserInput(user_id=user_id.strip(), name=name.strip(), age=age, weight=weight, goal=goal, intensity=intensity)
    except Exception as exc:
        return templates.TemplateResponse(request=request, name="index.html", context={"error": str(exc)}, status_code=422)
    user = db.scalar(select(User).where(User.user_id == user_input.user_id))
    if user is None:
        user = User(**user_input.model_dump())
        db.add(user)
        db.flush()
    else:
        for key, value in user_input.model_dump().items():
            setattr(user, key, value)
    workout = generate_workout_gemini(user_input)
    tip = generate_nutrition_tip_with_flash(user_input.goal)
    if user.plan:
        user.plan.original_plan = workout
        user.plan.nutrition_tip = tip
        user.plan.updated_plan = None
        user.plan.feedback = None
        user.plan.updated_nutrition_tip = None
        user.plan.updated_at = None
        plan = user.plan
    else:
        plan = Plan(user_id=user.id, original_plan=workout, nutrition_tip=tip)
        db.add(plan)
    db.commit()
    return templates.TemplateResponse(request=request, name="result.html", context={"user": user, "plan": plan, "updated": False})


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(
    request: Request, user_id: str = Form(...), feedback: str = Form(...), db: Session = Depends(get_db)
):
    try:
        req = FeedbackRequest(user_id=user_id.strip(), feedback=feedback.strip())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    user = db.scalar(select(User).where(User.user_id == req.user_id))
    if not user or not user.plan:
        raise HTTPException(status_code=404, detail="User or plan not found")
    updated = update_workout_plan(user.plan.original_plan, req.feedback)
    tip = generate_nutrition_tip_with_flash(user.goal)
    user.plan.updated_plan = updated
    user.plan.feedback = req.feedback
    user.plan.updated_nutrition_tip = tip
    user.plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    return templates.TemplateResponse(request=request, name="result.html", context={"user": user, "plan": user.plan, "updated": True})


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return templates.TemplateResponse(request=request, name="all_users.html", context={"users": users})


@router.post("/admin/delete/{user_id}")
def delete_user_form(user_id: str, token: str = Form(...), db: Session = Depends(get_db)):
    _admin_required(token)
    user = db.scalar(select(User).where(User.user_id == user_id))
    if user:
        db.delete(user); db.commit()
    return RedirectResponse(url="/view-all-users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/api/health", response_model=HealthResponse)
def health():
    settings = get_settings()
    return {"status": "ok", "ai_enabled": bool(settings.ai_enabled and settings.gemini_api_key)}


@router.post("/api/generate-workout", response_model=PlanResponse, status_code=201)
def api_generate(payload: UserInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if user is None:
        user = User(**payload.model_dump()); db.add(user); db.flush()
    else:
        for key, value in payload.model_dump().items(): setattr(user, key, value)
    workout = generate_workout_gemini(payload)
    tip = generate_nutrition_tip_with_flash(payload.goal)
    if user.plan:
        user.plan.original_plan, user.plan.nutrition_tip = workout, tip
        user.plan.updated_plan = user.plan.feedback = user.plan.updated_nutrition_tip = user.plan.updated_at = None
        plan = user.plan
    else:
        plan = Plan(user_id=user.id, original_plan=workout, nutrition_tip=tip); db.add(plan)
    db.commit()
    return _plan_response(user, plan)


@router.post("/api/submit-feedback", response_model=PlanResponse)
def api_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if not user or not user.plan:
        raise HTTPException(status_code=404, detail="User or plan not found")
    user.plan.updated_plan = update_workout_plan(user.plan.original_plan, payload.feedback)
    user.plan.feedback = payload.feedback
    user.plan.updated_nutrition_tip = generate_nutrition_tip_with_flash(user.goal)
    user.plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    return _plan_response(user, user.plan, updated=True)


@router.get("/api/users")
def api_users(x_admin_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    _admin_required(x_admin_token)
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [_plan_response(u, u.plan, updated=bool(u.plan and u.plan.updated_plan)).model_dump() for u in users if u.plan]


@router.get("/api/users/{user_id}", response_model=PlanResponse)
def api_user(user_id: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user or not user.plan:
        raise HTTPException(status_code=404, detail="User or plan not found")
    return _plan_response(user, user.plan, updated=bool(user.plan.updated_plan))


@router.delete("/api/users/{user_id}", status_code=204)
def api_delete_user(user_id: str, x_admin_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    _admin_required(x_admin_token)
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user); db.commit()
