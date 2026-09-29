from typing import Literal
from pydantic import BaseModel, Field, field_validator

Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility", "endurance"]
Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    user_id: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=25, le=400)
    goal: Goal
    intensity: Intensity


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=64)
    feedback: str = Field(min_length=3, max_length=1000)


class Exercise(BaseModel):
    name: str
    sets_reps: str
    rest: str


class DayPlan(BaseModel):
    day: str
    focus: str
    warmup: str
    exercises: list[Exercise]
    cooldown: str


class WorkoutPlan(BaseModel):
    days: list[DayPlan] = Field(min_length=7, max_length=7)


class PlanResponse(BaseModel):
    user_id: str
    name: str
    age: int
    weight: float
    goal: str
    intensity: str
    workout_plan: str
    nutrition_tip: str
    updated: bool = False


class HealthResponse(BaseModel):
    status: str
    ai_enabled: bool
