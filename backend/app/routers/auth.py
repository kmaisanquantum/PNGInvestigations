from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth as auth_utils
from app.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/bootstrap-admin", response_model=schemas.UserOut)
def bootstrap_admin(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Creates the first admin user. Only works if no users exist yet."""
    existing = db.query(models.User).count()
    if existing > 0:
        raise HTTPException(status_code=403, detail="Admin already bootstrapped. Use /register with an admin token.")

    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=auth_utils.hash_password(payload.password),
        role=models.UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, user.id, "bootstrap_admin", "user", user.id, f"created first admin {user.email}")
    return user


@router.post("/register", response_model=schemas.UserOut)
def register(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role = payload.role if payload.role in [r.value for r in models.UserRole] else "viewer"
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=auth_utils.hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "create_user", "user", user.id, f"role={role}")
    return user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")

    token = auth_utils.create_access_token(subject=user.id, extra={"role": user.role.value})
    log_action(db, user.id, "login", "user", user.id, "")
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth_utils.get_current_user)):
    return current_user
