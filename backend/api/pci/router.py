from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.common.database import get_db
from api.common.models import ParentApproval, SystemSetting
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/pci", tags=["pci"])

class SettingUpdate(BaseModel):
    settings: Dict[str, str]

class ApprovalRequest(BaseModel):
    game_id: int
    tier: str
    duration_hours: int = 24

class ApprovalDecision(BaseModel):
    decision: str # APPROVE, DENY

AVAILABLE_MODELS = [
    {
        "id": "gemini-vertex",
        "name": "Google Gemini (Vertex AI)",
        "fields": [
            {"key": "GOOGLE_CLOUD_PROJECT", "label": "Project ID", "type": "text"},
            {"key": "GOOGLE_CLOUD_LOCATION", "label": "Location (e.g. us-central1)", "type": "text"},
            {"key": "GOOGLE_APPLICATION_CREDENTIALS_JSON", "label": "Service Account JSON", "type": "textarea"},
            {"key": "AI_MODEL_NAME", "label": "Model Name (e.g. gemini-1.5-pro)", "type": "text"}
        ]
    },
    {
        "id": "openai-chatgpt",
        "name": "OpenAI ChatGPT",
        "fields": [
            {"key": "OPENAI_API_KEY", "label": "API Key", "type": "text"},
            {"key": "OPENAI_MODEL_NAME", "label": "Model Name (e.g. gpt-4o)", "type": "text"}
        ]
    }
]

@router.get("/available-models")
async def get_available_models():
    return AVAILABLE_MODELS

@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}

@router.post("/settings")
async def update_settings(update_data: SettingUpdate, db: AsyncSession = Depends(get_db)):
    for key, value in update_data.settings.items():
        # Upsert logic
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            db.add(SystemSetting(key=key, value=value))
    await db.commit()
    return {"message": "Settings updated"}

@router.post("/approvals")
async def create_approval(request: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta, timezone
    expires_at = datetime.now(timezone.utc) + timedelta(hours=request.duration_hours)
    approval = ParentApproval(
        game_id=request.game_id, 
        tier=request.tier, 
        expires_at=expires_at,
        approved=False,
        used=False
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval

@router.post("/approvals/{approval_id}/decision")
async def approval_decision(approval_id: int, decision_data: ApprovalDecision, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ParentApproval).where(ParentApproval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    approval.approved = (decision_data.decision == "APPROVE")
    await db.commit()
    return {"message": f"Approval {decision_data.decision.lower()}ed"}


@router.get("/usage")
async def get_usage(db: AsyncSession = Depends(get_db)):
    # Simple usage view: list all approved AI sessions
    result = await db.execute(select(ParentApproval).where(ParentApproval.approved == True))
    usage = result.scalars().all()
    return {"usage": usage}
