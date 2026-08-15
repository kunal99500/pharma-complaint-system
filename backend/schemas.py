from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RiskLevelEnum(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    UNKNOWN = "unknown"


class ComplaintStatusEnum(str, Enum):
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    CAPA_OPEN = "capa_open"
    CLOSED = "closed"
    REJECTED = "rejected"


class ComplaintCategoryEnum(str, Enum):
    PRODUCT_QUALITY = "product_quality"
    ADVERSE_EVENT = "adverse_event"
    LABELING = "labeling"
    PACKAGING = "packaging"
    DELIVERY = "delivery"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class CapaActionResponse(BaseModel):
    id: str
    action_type: str
    title: str
    description: str
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date_suggestion: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class ProbableCauseResponse(BaseModel):
    cause: str
    category: Optional[str] = None
    likelihood: Optional[str] = None
    investigation_step: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    id: str
    complaint_id: str

    extraction_confidence: Optional[float] = None

    classified_risk: Optional[str] = None
    classified_category: Optional[str] = None
    classification_reasoning: Optional[str] = None
    regulatory_reference: Optional[str] = None

    root_cause_analysis: Optional[str] = None
    probable_causes: List[ProbableCauseResponse] = Field(
        default_factory=list
    )

    is_complete: Optional[bool] = None
    missing_fields: List[str] = Field(
        default_factory=list
    )

    ai_summary: Optional[str] = None

    duplicate_score: Optional[float] = None
    similar_complaint_ids: List[str] = Field(
        default_factory=list
    )

    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintCreate(BaseModel):
    source_type: str = Field(default="manual")
    raw_input: Optional[str] = None

    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_company: Optional[str] = None
    customer_country: Optional[str] = None

    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None

    complaint_description: Optional[str] = None
    date_of_complaint: Optional[str] = None
    category: Optional[ComplaintCategoryEnum] = None

    storage_conditions: Optional[str] = None
    actions_taken: Optional[str] = None
    coa_information: Optional[str] = None
    customer_requested_action: Optional[str] = None


class ComplaintUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_company: Optional[str] = None
    customer_country: Optional[str] = None

    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None

    complaint_description: Optional[str] = None
    date_of_complaint: Optional[str] = None
    category: Optional[ComplaintCategoryEnum] = None
    status: Optional[ComplaintStatusEnum] = None
    risk_level: Optional[RiskLevelEnum] = None

    storage_conditions: Optional[str] = None
    actions_taken: Optional[str] = None
    coa_information: Optional[str] = None
    customer_requested_action: Optional[str] = None


class AttachmentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: Optional[int] = None
    storage_path: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintResponse(BaseModel):
    id: str
    complaint_number: str
    source_type: str
    raw_input: Optional[str] = None

    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_company: Optional[str] = None
    customer_country: Optional[str] = None

    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None

    complaint_description: Optional[str] = None
    date_of_complaint: Optional[str] = None

    category: Optional[ComplaintCategoryEnum] = None
    status: ComplaintStatusEnum
    risk_level: RiskLevelEnum

    storage_conditions: Optional[str] = None
    actions_taken: Optional[str] = None
    coa_information: Optional[str] = None
    customer_requested_action: Optional[str] = None

    is_duplicate: bool
    ai_processed: bool
    analysis_status: Optional[str] = None 

    analysis: Optional[AnalysisResultResponse] = None
    capa_actions: List[CapaActionResponse] = Field(
        default_factory=list
    )
    attachments: List[AttachmentResponse] = Field(
        default_factory=list
    )

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintListItem(BaseModel):
    id: str
    complaint_number: str
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[ComplaintCategoryEnum] = None
    status: ComplaintStatusEnum
    risk_level: RiskLevelEnum
    ai_processed: bool
    analysis_status: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyzeRequest(BaseModel):
    complaint_id: str
    force_reanalyze: bool = Field(default=False)


class AnalyzeResponse(BaseModel):
    complaint_id: str
    success: bool
    message: str
    analysis_status: str = Field(default="pending")
    analysis: Optional[AnalysisResultResponse] = None
    capa_actions: List[CapaActionResponse] = Field(
        default_factory=list
    )