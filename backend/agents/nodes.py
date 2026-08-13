import json
from typing import Any, Dict

from langchain_openai import ChatOpenAI

from core.config import settings
from agents.prompts import COMPLAINT_ANALYSIS_PROMPT
from agents.state import ComplaintAgentState


llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    api_key=settings.OPENAI_API_KEY,
    temperature=0,
)


def parse_json_response(content: str) -> Dict[str, Any]:
    content = content.strip()

    if content.startswith("```"):
        lines = content.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    return json.loads(content)


def extract_complaint_info(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    try:
        existing_complaints = json.dumps(
            state["existing_complaints"],
            default=str,
            ensure_ascii=False,
        )

        prompt = COMPLAINT_ANALYSIS_PROMPT.replace(
            "{existing_complaints}",
            existing_complaints,
        ).replace(
            "{raw_text}",
            state["raw_text"],
        )

        response = llm.invoke(prompt)
        analysis = parse_json_response(
            response.content
        )

        extraction = analysis.get(
            "extraction",
            {},
        )

        return {
            "_full_analysis": analysis,

            "extracted_product_name": extraction.get(
                "product_name"
            ),
            "extracted_batch_number": extraction.get(
                "batch_number"
            ),
            "extracted_customer_name": extraction.get(
                "customer_name"
            ),
            "extracted_customer_email": extraction.get(
                "customer_email"
            ),
            "extracted_customer_phone": extraction.get(
                "customer_phone"
            ),
            "extracted_customer_company": extraction.get(
                "customer_company"
            ),
            "extracted_customer_country": extraction.get(
                "customer_country"
            ),
            "extracted_manufacturing_date": extraction.get(
                "manufacturing_date"
            ),
            "extracted_expiry_date": extraction.get(
                "expiry_date"
            ),
            "extracted_quantity_affected": extraction.get(
                "quantity_affected"
            ),
            "extracted_date_of_complaint": extraction.get(
                "date_of_complaint"
            ),
            "extracted_description": extraction.get(
                "description"
            ),
            "extracted_storage_conditions": extraction.get(
                "storage_conditions"
            ),
            "extracted_actions_taken": extraction.get(
                "actions_taken"
            ),
            "extracted_coa_information": extraction.get(
                "coa_information"
            ),
            "extracted_customer_requested_action": extraction.get(
                "customer_requested_action"
            ),
            "extraction_confidence": extraction.get(
                "confidence"
            ),
        }

    except Exception as exc:
        return {
            "_full_analysis": None,
            "errors": [
                f"Complaint analysis failed: {str(exc)}"
            ],
        }


def classify_risk(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    analysis = state.get(
        "_full_analysis"
    ) or {}

    classification = analysis.get(
        "classification",
        {},
    )

    return {
        "risk_level": classification.get(
            "risk_level"
        ),
        "complaint_category": classification.get(
            "complaint_category"
        ),
        "classification_reasoning": classification.get(
            "classification_reasoning"
        ),
        "regulatory_reference": classification.get(
            "regulatory_reference"
        ),
    }


def check_completeness(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    analysis = state.get(
        "_full_analysis"
    ) or {}

    completeness = analysis.get(
        "completeness",
        {},
    )

    return {
        "is_complete": completeness.get(
            "is_complete"
        ),
        "missing_fields": completeness.get(
            "missing_fields",
            [],
        ),
    }


def analyze_root_cause(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    analysis = state.get(
        "_full_analysis"
    ) or {}

    root_cause = analysis.get(
        "root_cause",
        {},
    )

    return {
        "root_cause_analysis": root_cause.get(
            "root_cause_analysis"
        ),
        "probable_causes": root_cause.get(
            "probable_causes",
            [],
        ),
    }


def generate_capa(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    analysis = state.get(
        "_full_analysis"
    ) or {}

    return {
        "capa_actions": analysis.get(
            "capa_actions",
            [],
        ),
    }


def summarize_complaint(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    analysis = state.get(
        "_full_analysis"
    ) or {}

    return {
        "ai_summary": analysis.get(
            "summary"
        ),
    }


def detect_duplicates(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    analysis = state.get(
        "_full_analysis"
    ) or {}

    duplicate_detection = analysis.get(
        "duplicate_detection",
        {},
    )

    return {
        "duplicate_score": duplicate_detection.get(
            "duplicate_score",
            0.0,
        ),
        "similar_complaint_ids": duplicate_detection.get(
            "similar_complaint_ids",
            [],
        ),
    }