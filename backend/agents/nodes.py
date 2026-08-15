import json
import time
from typing import Any, Dict

from langchain_openai import ChatOpenAI

from core.config import settings
from agents.prompts import (
    CLASSIFICATION_PROMPT,
    CAPA_PROMPT,
    DUPLICATE_DETECTION_PROMPT,
    EXTRACTION_PROMPT,
)
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


def call_llm_with_retry(
    prompt: str,
    node_name: str,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Call the LLM with exponential backoff retry.
    Raises on final failure so the node can handle it cleanly.
    """
    last_error = None

    for attempt in range(max_attempts):
        try:
            response = llm.invoke(prompt)
            return parse_json_response(response.content)

        except json.JSONDecodeError as exc:
            last_error = f"{node_name}: invalid JSON on attempt {attempt + 1}: {str(exc)}"

        except Exception as exc:
            last_error = f"{node_name}: LLM call failed on attempt {attempt + 1}: {str(exc)}"

        if attempt < max_attempts - 1:
            wait = 2 ** attempt
            time.sleep(wait)

    raise RuntimeError(last_error)


def extract_complaint_info(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    """
    Node 1: Extract all structured fields from raw complaint text.
    Makes one focused LLM call. No classification or analysis.
    """
    try:
        prompt = EXTRACTION_PROMPT.replace(
            "{raw_text}",
            state["raw_text"],
        )

        extraction = call_llm_with_retry(
            prompt,
            node_name="extract",
        )

        return {
            "extracted_customer_name": extraction.get("customer_name"),
            "extracted_customer_email": extraction.get("customer_email"),
            "extracted_customer_phone": extraction.get("customer_phone"),
            "extracted_customer_company": extraction.get("customer_company"),
            "extracted_customer_country": extraction.get("customer_country"),
            "extracted_product_name": extraction.get("product_name"),
            "extracted_batch_number": extraction.get("batch_number"),
            "extracted_manufacturing_date": extraction.get("manufacturing_date"),
            "extracted_expiry_date": extraction.get("expiry_date"),
            "extracted_quantity_affected": extraction.get("quantity_affected"),
            "extracted_date_of_complaint": extraction.get("date_of_complaint"),
            "extracted_description": extraction.get("description"),
            "extracted_storage_conditions": extraction.get("storage_conditions"),
            "extracted_actions_taken": extraction.get("actions_taken"),
            "extracted_coa_information": extraction.get("coa_information"),
            "extracted_customer_requested_action": extraction.get("customer_requested_action"),
            "extraction_confidence": extraction.get("confidence"),
            "extraction_success": True,
        }

    except Exception as exc:
        return {
            "extraction_success": False,
            "errors": [str(exc)],
        }


def classify_and_analyze(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    """
    Node 2: Classify risk, category, check completeness, analyze root cause.
    Uses extracted fields from Node 1 as grounded input — not raw text.
    Skips gracefully if extraction failed.
    """
    if not state.get("extraction_success", False):
        return {
            "classification_success": False,
            "errors": ["Skipping classification — extraction failed"],
        }

    extracted_data = {
        "customer_name": state.get("extracted_customer_name"),
        "customer_email": state.get("extracted_customer_email"),
        "customer_company": state.get("extracted_customer_company"),
        "customer_country": state.get("extracted_customer_country"),
        "product_name": state.get("extracted_product_name"),
        "batch_number": state.get("extracted_batch_number"),
        "manufacturing_date": state.get("extracted_manufacturing_date"),
        "expiry_date": state.get("extracted_expiry_date"),
        "quantity_affected": state.get("extracted_quantity_affected"),
        "date_of_complaint": state.get("extracted_date_of_complaint"),
        "description": state.get("extracted_description"),
        "storage_conditions": state.get("extracted_storage_conditions"),
        "actions_taken": state.get("extracted_actions_taken"),
        "coa_information": state.get("extracted_coa_information"),
        "customer_requested_action": state.get("extracted_customer_requested_action"),
    }

    try:
        prompt = CLASSIFICATION_PROMPT.replace(
            "{extracted_data}",
            json.dumps(extracted_data, ensure_ascii=False, indent=2),
        )

        classification = call_llm_with_retry(
            prompt,
            node_name="classify",
        )

        return {
            "risk_level": classification.get("risk_level"),
            "complaint_category": classification.get("complaint_category"),
            "classification_reasoning": classification.get("classification_reasoning"),
            "regulatory_reference": classification.get("regulatory_reference"),
            "is_complete": classification.get("is_complete"),
            "missing_fields": classification.get("missing_fields", []),
            "root_cause_analysis": classification.get("root_cause_analysis"),
            "probable_causes": classification.get("probable_causes", []),
            "classification_success": True,
        }

    except Exception as exc:
        return {
            "classification_success": False,
            "errors": [str(exc)],
        }


def generate_capa_and_summary(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    """
    Node 3: Generate CAPA actions and professional summary.
    Uses classification + root cause from Node 2 as grounded input.
    Skips gracefully if classification failed.
    """
    if not state.get("classification_success", False):
        return {
            "capa_success": False,
            "errors": ["Skipping CAPA — classification failed"],
        }

    classification_data = {
        "product_name": state.get("extracted_product_name"),
        "batch_number": state.get("extracted_batch_number"),
        "description": state.get("extracted_description"),
        "risk_level": state.get("risk_level"),
        "complaint_category": state.get("complaint_category"),
        "classification_reasoning": state.get("classification_reasoning"),
        "root_cause_analysis": state.get("root_cause_analysis"),
        "probable_causes": state.get("probable_causes", []),
        "is_complete": state.get("is_complete"),
        "missing_fields": state.get("missing_fields", []),
    }

    try:
        prompt = CAPA_PROMPT.replace(
            "{classification_data}",
            json.dumps(classification_data, ensure_ascii=False, indent=2),
        )

        result = call_llm_with_retry(
            prompt,
            node_name="generate_capa",
        )

        return {
            "capa_actions": result.get("capa_actions", []),
            "ai_summary": result.get("ai_summary"),
            "capa_success": True,
        }

    except Exception as exc:
        return {
            "capa_success": False,
            "errors": [str(exc)],
        }


def detect_duplicates(
    state: ComplaintAgentState,
) -> Dict[str, Any]:
    """
    Node 4: Compare current complaint against existing complaints.
    Runs independently — does not depend on classification success.
    Skips gracefully if extraction failed since we need extracted fields to compare.
    """
    if not state.get("extraction_success", False):
        return {
            "duplicate_score": 0.0,
            "similar_complaint_ids": [],
        }

    existing = state.get("existing_complaints", [])

    if not existing:
        return {
            "duplicate_score": 0.0,
            "similar_complaint_ids": [],
        }

    extracted_data = {
        "product_name": state.get("extracted_product_name"),
        "batch_number": state.get("extracted_batch_number"),
        "customer_company": state.get("extracted_customer_company"),
        "description": state.get("extracted_description"),
        "complaint_category": state.get("complaint_category"),
    }

    try:
        prompt = DUPLICATE_DETECTION_PROMPT.replace(
            "{extracted_data}",
            json.dumps(extracted_data, ensure_ascii=False, indent=2),
        ).replace(
            "{existing_complaints}",
            json.dumps(existing, ensure_ascii=False, indent=2),
        )

        result = call_llm_with_retry(
            prompt,
            node_name="detect_duplicates",
        )

        return {
            "duplicate_score": result.get("duplicate_score", 0.0),
            "similar_complaint_ids": result.get("similar_complaint_ids", []),
        }

    except Exception as exc:
        return {
            "duplicate_score": 0.0,
            "similar_complaint_ids": [],
            "errors": [str(exc)],
        }