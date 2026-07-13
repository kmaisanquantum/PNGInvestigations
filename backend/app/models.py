import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey, Enum, BigInteger, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    admin = "admin"
    investigator = "investigator"
    reviewer = "reviewer"
    viewer = "viewer"


class CaseStatus(str, enum.Enum):
    open = "open"
    evidence_collection = "evidence_collection"
    under_review = "under_review"
    closed = "closed"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cases_created = relationship("Case", back_populates="created_by_user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_number = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CaseStatus), nullable=False, default=CaseStatus.open)
    category = Column(String, nullable=True)  # procurement_fraud, corruption, coi, etc.
    created_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_user = relationship("User", back_populates="cases_created")
    evidence_items = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    case_id = Column(UUID(as_uuid=False), ForeignKey("cases.id"), nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    sha256_hash = Column(String, nullable=False)
    uploaded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    hash_sealed = Column(Boolean, default=True)  # immutable once True
    notes = Column(Text, nullable=True)

    case = relationship("Case", back_populates="evidence_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    actor_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    detail = Column(Text, nullable=True)
    prev_hash = Column(String, nullable=True)
    entry_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
