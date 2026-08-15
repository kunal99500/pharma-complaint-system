from typing import List, Optional

from langgraph.graph import END, StateGraph

from agents.nodes import (
    classify_and_analyze,
    detect_duplicates,
    extract_complaint_info,
    generate_capa_and_summary,
)
from agents.state import ComplaintAgentState


def build_complaint_agent():
    graph = StateGraph(ComplaintAgentState)

    graph.add_node("extract", extract_complaint_info)
    graph.add_node("classify", classify_and_analyze)
    graph.add_node("generate_capa", generate_capa_and_summary)
    graph.add_node("detect_duplicates", detect_duplicates)

    graph.set_entry_point("extract")

    # classify uses extracted fields — must run after extract
    graph.add_edge("extract", "classify")

    # generate_capa uses classification — must run after classify
    graph.add_edge("classify", "generate_capa")

    # detect_duplicates only needs extracted fields — runs in parallel
    # with classify but LangGraph sequential graph runs it last
    # (parallel execution would require Send API — keeping it simple here)
    graph.add_edge("generate_capa", "detect_duplicates")

    graph.add_edge("detect_duplicates", END)

    return graph.compile()


def run_complaint_analysis(
    raw_text: str,
    complaint_id: str,
    existing_complaints: Optional[List[dict]] = None,
) -> ComplaintAgentState:
    """
    Run the full complaint analysis pipeline synchronously.
    Used directly by the background task runner.
    Returns the final state regardless of partial failures —
    the router reads success flags to decide what to save.
    """
    graph = build_complaint_agent()

    initial_state: ComplaintAgentState = {
        # Input
        "raw_text": raw_text,
        "complaint_id": complaint_id,
        "existing_complaints": existing_complaints or [],

        # Success flags — all False until each node succeeds
        "extraction_success": False,
        "classification_success": False,
        "capa_success": False,

        # Extraction fields
        "extracted_product_name": None,
        "extracted_batch_number": None,
        "extracted_customer_name": None,
        "extracted_customer_email": None,
        "extracted_customer_phone": None,
        "extracted_customer_company": None,
        "extracted_customer_country": None,
        "extracted_manufacturing_date": None,
        "extracted_expiry_date": None,
        "extracted_quantity_affected": None,
        "extracted_date_of_complaint": None,
        "extracted_description": None,
        "extracted_storage_conditions": None,
        "extracted_actions_taken": None,
        "extracted_coa_information": None,
        "extracted_customer_requested_action": None,
        "extraction_confidence": None,

        # Classification + root cause
        "risk_level": None,
        "complaint_category": None,
        "classification_reasoning": None,
        "regulatory_reference": None,
        "is_complete": None,
        "missing_fields": [],
        "root_cause_analysis": None,
        "probable_causes": [],

        # CAPA + summary
        "capa_actions": [],
        "ai_summary": None,

        # Duplicate detection
        "duplicate_score": None,
        "similar_complaint_ids": [],

        # Errors
        "errors": [],
    }

    return graph.invoke(initial_state)