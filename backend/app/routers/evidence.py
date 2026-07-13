import hashlib
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app import models, schemas, auth as auth_utils
from app.audit import log_action

router = APIRouter(prefix="/api/cases/{case_id}/evidence", tags=["evidence"])

WRITE_ROLES = ("admin", "investigator")


@router.get("", response_model=List[schemas.EvidenceOut])
def list_evidence(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    if not db.query(models.Case).filter(models.Case.id == case_id).first():
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(models.Evidence).filter(models.Evidence.case_id == case_id).order_by(
        models.Evidence.uploaded_at.desc()
    ).all()


@router.post("", response_model=schemas.EvidenceOut)
def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    notes: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles(*WRITE_ROLES)),
):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case_dir = os.path.join(settings.evidence_storage_path, case_id)
    os.makedirs(case_dir, exist_ok=True)

    stored_name = f"{uuid.uuid4()}_{file.filename}"
    dest_path = os.path.join(case_dir, stored_name)

    sha256 = hashlib.sha256()
    size = 0
    with open(dest_path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            sha256.update(chunk)
            size += len(chunk)
            out.write(chunk)

    evidence = models.Evidence(
        case_id=case_id,
        filename=file.filename,
        storage_path=dest_path,
        content_type=file.content_type,
        size_bytes=size,
        sha256_hash=sha256.hexdigest(),
        uploaded_by=current_user.id,
        notes=notes,
        hash_sealed=True,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    log_action(
        db, current_user.id, "upload_evidence", "evidence", evidence.id,
        f"case={case_id} filename={file.filename} sha256={evidence.sha256_hash}",
    )
    return evidence


@router.get("/{evidence_id}/download")
def download_evidence(
    case_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    evidence = db.query(models.Evidence).filter(
        models.Evidence.id == evidence_id, models.Evidence.case_id == case_id
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Integrity check on every access — tamper detection.
    sha256 = hashlib.sha256()
    with open(evidence.storage_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            sha256.update(chunk)
    if sha256.hexdigest() != evidence.sha256_hash:
        log_action(db, current_user.id, "integrity_check_failed", "evidence", evidence.id, "hash mismatch")
        raise HTTPException(status_code=409, detail="Integrity check failed: file hash mismatch")

    log_action(db, current_user.id, "download_evidence", "evidence", evidence.id, "")
    return FileResponse(evidence.storage_path, filename=evidence.filename, media_type=evidence.content_type)
