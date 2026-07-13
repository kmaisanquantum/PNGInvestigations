from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth as auth_utils
from app.audit import log_action

router = APIRouter(prefix="/api/cases", tags=["cases"])

WRITE_ROLES = ("admin", "investigator")
REVIEW_ROLES = ("admin", "reviewer")


@router.get("", response_model=List[schemas.CaseOut])
def list_cases(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    query = db.query(models.Case)
    if status_filter:
        query = query.filter(models.Case.status == status_filter)
    return query.order_by(models.Case.created_at.desc()).all()


@router.post("", response_model=schemas.CaseOut)
def create_case(
    payload: schemas.CaseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles(*WRITE_ROLES)),
):
    if db.query(models.Case).filter(models.Case.case_number == payload.case_number).first():
        raise HTTPException(status_code=400, detail="Case number already exists")

    case = models.Case(
        case_number=payload.case_number,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        created_by=current_user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    log_action(db, current_user.id, "create_case", "case", case.id, payload.title)
    return case


@router.get("/{case_id}", response_model=schemas.CaseOut)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=schemas.CaseOut)
def update_case(
    case_id: str,
    payload: schemas.CaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles(*WRITE_ROLES, "reviewer")),
):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Status transitions to "closed" require reviewer/admin — a human review gate.
    if payload.status == "closed" and current_user.role.value not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Only a reviewer or admin can close a case")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    log_action(db, current_user.id, "update_case", "case", case.id, str(payload.model_dump(exclude_unset=True)))
    return case
