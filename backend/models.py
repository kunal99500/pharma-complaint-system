import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class RiskLevel(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    UNKNOWN = "unknown"


class ComplaintStatus(str, enum.Enum):
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    CAPA_OPEN = "capa_open"
    CLOSED = "closed"
    REJECTED = "rejected"


class ComplaintCategory(str, enum.Enum):
    PRODUCT_QUALITY = "product_quality"
    ADVERSE_EVENT = "adverse_event"
    LABELING = "labeling"
    PACKAGING = "packaging"
    DELIVERY = "delivery"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    complaint_number = Column(
        String(50),
        unique=True,
        nullable=False,
    )
    source_type = Column(
        String(50),
        nullable=False,
        default="manual",
    )
    raw_input = Column(Text, nullable=True)

    customer_name = Column(String(200), nullable=True)
    customer_email = Column(String(200), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_company = Column(String(200), nullable=True)
    customer_country = Column(String(100), nullable=True)

    product_name = Column(String(200), nullable=True)
    batch_number = Column(String(100), nullable=True)
    manufacturing_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)
    quantity_affected = Column(String(200), nullable=True)

    complaint_description = Column(Text, nullable=True)
    date_of_complaint = Column(String(50), nullable=True)

    category = Column(
        Enum(ComplaintCategory),
        nullable=True,
        default=ComplaintCategory.OTHER,
    )
    status = Column(
        Enum(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.RECEIVED,
    )
    risk_level = Column(
        Enum(RiskLevel),
        nullable=False,
        default=RiskLevel.UNKNOWN,
    )

    storage_conditions = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    coa_information = Column(Text, nullable=True)
    customer_requested_action = Column(Text, nullable=True)

    is_duplicate = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    duplicate_of_id = Column(
        String(36),
        ForeignKey("complaints.id"),
        nullable=True,
    )

    duplicate_of = relationship(
        "Complaint",
        remote_side=[id],
        foreign_keys=[duplicate_of_id],
    )

    ai_processed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    analysis = relationship(
        "AnalysisResult",
        back_populates="complaint",
        uselist=False,
        cascade="all, delete-orphan",
    )

    attachments = relationship(
        "Attachment",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )

    capa_actions = relationship(
        "CapaAction",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    complaint_id = Column(
        String(36),
        ForeignKey("complaints.id"),
        nullable=False,
        unique=True,
    )

    extraction_confidence = Column(
        Float,
        nullable=True,
    )

    classified_risk = Column(
        String(50),
        nullable=True,
    )
    classified_category = Column(
        String(100),
        nullable=True,
    )
    classification_reasoning = Column(
        Text,
        nullable=True,
    )
    regulatory_reference = Column(
        Text,
        nullable=True,
    )

    root_cause_analysis = Column(
        Text,
        nullable=True,
    )
    probable_causes = Column(
        JSON,
        nullable=True,
    )

    is_complete = Column(
        Boolean,
        nullable=True,
    )
    missing_fields = Column(
        JSON,
        nullable=True,
    )

    ai_summary = Column(
        Text,
        nullable=True,
    )

    duplicate_score = Column(
        Float,
        nullable=True,
    )
    similar_complaint_ids = Column(
        JSON,
        nullable=True,
    )

    analyzed_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    complaint = relationship(
        "Complaint",
        back_populates="analysis",
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    complaint_id = Column(
        String(36),
        ForeignKey("complaints.id"),
        nullable=False,
    )

    filename = Column(
        String(500),
        nullable=False,
    )
    file_type = Column(
        String(50),
        nullable=False,
    )
    file_size = Column(
        Integer,
        nullable=True,
    )
    storage_path = Column(
        String(1000),
        nullable=True,
    )
    extracted_text = Column(
        Text,
        nullable=True,
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    complaint = relationship(
        "Complaint",
        back_populates="attachments",
    )


class CapaAction(Base):
    __tablename__ = "capa_actions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    complaint_id = Column(
        String(36),
        ForeignKey("complaints.id"),
        nullable=False,
    )

    action_type = Column(
        String(50),
        nullable=False,
    )
    title = Column(
        String(500),
        nullable=False,
    )
    description = Column(
        Text,
        nullable=False,
    )
    priority = Column(
        String(20),
        nullable=True,
    )
    assigned_to = Column(
        String(200),
        nullable=True,
    )
    due_date_suggestion = Column(
        String(100),
        nullable=True,
    )
    status = Column(
        String(50),
        nullable=False,
        default="open",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    complaint = relationship(
        "Complaint",
        back_populates="capa_actions",
    )