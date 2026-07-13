from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Optional[str] = "viewer"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Cases ---
class CaseCreate(BaseModel):
    case_number: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None


class CaseOut(BaseModel):
    id: str
    case_number: str
    title: str
    description: Optional[str]
    status: str
    category: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Evidence ---
class EvidenceOut(BaseModel):
    id: str
    case_id: str
    filename: str
    content_type: Optional[str]
    size_bytes: Optional[int]
    sha256_hash: str
    uploaded_by: str
    uploaded_at: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True
