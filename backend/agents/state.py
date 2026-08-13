from typing import Annotated, List, Optional, TypedDict
import operator


class ComplaintAgentState(TypedDict):
    raw_text: str
    complaint_id: str
    existing_complaints: List[dict]

    _full_analysis: Optional[dict]

    extracted_product_name: Optional[str]
    extracted_batch_number: Optional[str]
    extracted_customer_name: Optional[str]
    extracted_customer_email: Optional[str]
    extracted_customer_phone: Optional[str]
    extracted_customer_company: Optional[str]
    extracted_customer_country: Optional[str]
    extracted_manufacturing_date: Optional[str]
    extracted_expiry_date: Optional[str]
    extracted_quantity_affected: Optional[str]
    extracted_date_of_complaint: Optional[str]
    extracted_description: Optional[str]
    extracted_storage_conditions: Optional[str]
    extracted_actions_taken: Optional[str]
    extracted_coa_information: Optional[str]
    extracted_customer_requested_action: Optional[str]
    extraction_confidence: Optional[float]

    risk_level: Optional[str]
    complaint_category: Optional[str]
    classification_reasoning: Optional[str]
    regulatory_reference: Optional[str]

    is_complete: Optional[bool]
    missing_fields: List[str]

    root_cause_analysis: Optional[str]
    probable_causes: List[dict]

    capa_actions: Annotated[List[dict], operator.add]

    ai_summary: Optional[str]

    duplicate_score: Optional[float]
    similar_complaint_ids: List[str]

    errors: Annotated[List[str], operator.add]