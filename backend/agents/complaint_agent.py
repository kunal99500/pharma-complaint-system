from typing import List, Optional

from langgraph.graph import END, StateGraph

from agents.nodes import (
    analyze_root_cause,
    check_completeness,
    classify_risk,
    detect_duplicates,
    extract_complaint_info,
    generate_capa,
    summarize_complaint,
)
from agents.state import ComplaintAgentState


def build_complaint_agent():
    graph = StateGraph(
        ComplaintAgentState
    )

    graph.add_node(
        "extract",
        extract_complaint_info,
    )

    graph.add_node(
        "classify",
        classify_risk,
    )

    graph.add_node(
        "check_completeness",
        check_completeness,
    )

    graph.add_node(
        "analyze_root_cause",
        analyze_root_cause,
    )

    graph.add_node(
        "generate_capa",
        generate_capa,
    )

    graph.add_node(
        "summarize",
        summarize_complaint,
    )

    graph.add_node(
        "detect_duplicates",
        detect_duplicates,
    )

    graph.set_entry_point(
        "extract"
    )

    graph.add_edge(
        "extract",
        "classify",
    )

    graph.add_edge(
        "classify",
        "check_completeness",
    )

    graph.add_edge(
        "check_completeness",
        "analyze_root_cause",
    )

    graph.add_edge(
        "analyze_root_cause",
        "generate_capa",
    )

    graph.add_edge(
        "generate_capa",
        "summarize",
    )

    graph.add_edge(
        "summarize",
        "detect_duplicates",
    )

    graph.add_edge(
        "detect_duplicates",
        END,
    )

    return graph.compile()


def run_complaint_analysis(
    raw_text: str,
    complaint_id: str,
    existing_complaints: Optional[
        List[dict]
    ] = None,
) -> ComplaintAgentState:
    graph = build_complaint_agent()

    initial_state: ComplaintAgentState = {
        "raw_text": raw_text,
        "complaint_id": complaint_id,
        "existing_complaints": (
            existing_complaints or []
        ),

        "_full_analysis": None,

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

        "risk_level": None,
        "complaint_category": None,
        "classification_reasoning": None,
        "regulatory_reference": None,

        "is_complete": None,
        "missing_fields": [],

        "root_cause_analysis": None,
        "probable_causes": [],

        "capa_actions": [],

        "ai_summary": None,

        "duplicate_score": None,
        "similar_complaint_ids": [],

        "errors": [],
    }

    return graph.invoke(
        initial_state
    )