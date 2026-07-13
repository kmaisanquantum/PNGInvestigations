import hashlib
from sqlalchemy.orm import Session

from app import models


def _compute_hash(prev_hash: str, actor_id: str, action: str, resource_type: str, resource_id: str, detail: str) -> str:
    payload = f"{prev_hash}|{actor_id}|{action}|{resource_type}|{resource_id}|{detail}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def log_action(db: Session, actor_id: str, action: str, resource_type: str, resource_id: str, detail: str = ""):
    last = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).first()
    prev_hash = last.entry_hash if last else "genesis"
    entry_hash = _compute_hash(prev_hash, actor_id or "system", action, resource_type, resource_id or "", detail)

    entry = models.AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    db.commit()
    return entry
