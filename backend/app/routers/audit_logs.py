from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app import models, auth as auth_utils

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


class AuditLogOut(BaseModel):
    id: str
    actor_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    detail: Optional[str]
    entry_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin", "reviewer")),
):
    return db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(limit).all()
