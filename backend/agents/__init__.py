"""
routers/analysis.py — FastAPI routes for triggering and retrieving AI analysis (MySQL version)

Endpoints:
  POST /analysis/analyze  — Triggers the LangGraph agent for a complaint
  GET  /analysis/{id}     — Get the analysis result for a complaint

MySQL fix: all ID comparisons use plain strings, no UUID conversion.
"""

import uuid
import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Complaint, AnalysisResult, CapaAction, ComplaintStatus, RiskLevel, ComplaintCategory
from schemas import AnalyzeRequest, AnalyzeResponse, AnalysisResultResponse
from agents.complaint_agent import run_complaint_analysis

router = APIRouter(prefix="/analysis", tags=["AI Analysis"])


# ── Helpers: safely map string → enum ────────────────────────────────────────

def map_risk_level(risk_str: str):
    mapping = {
        "critical": RiskLevel.CRITICAL,
        "major":    RiskLevel.MAJOR,
        "minor":    RiskLevel.MINOR,
        "unknown":  RiskLevel.UNKNOWN,
    }
    return mapping.get((risk_str or "").lower(), RiskLevel.UNKNOWN)


def map_category(category_str: str):
    mapping = {
        "product_quality": ComplaintCategory.PRODUCT_QUALITY,
        "adverse_event":   ComplaintCategory.ADVERSE_EVENT,
        "labeling":        ComplaintCategory.LABELING,
        "packaging":       ComplaintCategory.PACKAGING,
        "delivery":        ComplaintCategory.DELIVERY,
        "documentation":   ComplaintCategory.DOCUMENTATION,
        "other":           ComplaintCategory.OTHER,
    }
    return mapping.get((category_str or "").lower(), ComplaintCategory.OTHER)


# ── POST /analysis/analyze ────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_complaint(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Triggers the full LangGraph agent pipeline for a complaint.

    Full sequence:
    1. Load complaint from DB using complaint_id (plain string in MySQL)
    2. Build raw_text — use raw_input if available, else compose from fields
    3. Load last 100 complaints for duplicate detection context
    4. Call run_complaint_analysis() — this runs all 7 LangGraph nodes
       (takes 5-15 seconds — all the Groq API calls happen here)
    5. Save all results: analysis_results table + capa_actions table
    6. Update the complaint row with AI-extracted fields + risk level
    7. Return the full AnalyzeResponse to the frontend

    The frontend shows a loading spinner while this runs.
    """

    # ── Step 1: Load the complaint ────────────────────────────────────────
    # MySQL: complaint_id is already a string — query directly
    complaint = db.query(Complaint).filter(
        Complaint.id == str(request.complaint_id)
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # ── Step 2: Skip if already analyzed (unless force flag set) ──────────
    if complaint.ai_processed and not request.force_reanalyze:
        return AnalyzeResponse(
            complaint_id = str(complaint.id),
            success      = True,
            message      = "Already analyzed. Pass force_reanalyze=true to re-run.",
            analysis     = complaint.analysis,
            capa_actions = complaint.capa_actions or [],
        )

    # ── Step 3: Build the text to analyze ────────────────────────────────
    # Priority: raw_input (typed text / extracted from file) first,
    # then fall back to composing from structured fields if raw_input is empty
    raw_text = complaint.raw_input or ""

    if not raw_text and complaint.complaint_description:
        parts = []
        if complaint.customer_name:
            parts.append(f"Customer: {complaint.customer_name}")
        if complaint.product_name:
            parts.append(f"Product: {complaint.product_name}")
        if complaint.batch_number:
            parts.append(f"Batch Number: {complaint.batch_number}")
        if complaint.complaint_description:
            parts.append(f"Complaint: {complaint.complaint_description}")
        raw_text = "\n".join(parts)

    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail="No text to analyze. Please add raw_input or complaint_description first."
        )

    # ── Step 4: Load existing complaints for duplicate detection ──────────
    existing_complaints = (
        db.query(Complaint)
        .filter(Complaint.id != complaint.id)
        .order_by(Complaint.created_at.desc())
        .limit(100)
        .all()
    )

    existing_list = [
        {
            "id":                    str(c.id),
            "complaint_description": c.complaint_description,
            "raw_input":             (c.raw_input or "")[:200],
            "product_name":          c.product_name,
            "batch_number":          c.batch_number,
        }
        for c in existing_complaints
    ]

    # ── Step 5: Run the LangGraph agent ──────────────────────────────────
    # This is where all the AI work happens — 7 nodes, multiple Groq calls
    try:
        agent_result = run_complaint_analysis(
            raw_text            = raw_text,
            complaint_id        = str(complaint.id),
            existing_complaints = existing_list,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    # ── Step 6: Save analysis result to DB ───────────────────────────────
    # Delete old analysis first if re-running
    existing_analysis = db.query(AnalysisResult).filter(
        AnalysisResult.complaint_id == complaint.id
    ).first()
    if existing_analysis:
        db.delete(existing_analysis)
        db.flush()

    analysis = AnalysisResult(
        id           = str(uuid.uuid4()),
        complaint_id = str(complaint.id),

        # From extract node
        extracted_product_name  = agent_result.get("extracted_product_name"),
        extracted_batch_number  = agent_result.get("extracted_batch_number"),
        extracted_customer_name = agent_result.get("extracted_customer_name"),
        extracted_description   = agent_result.get("extracted_description"),
        extraction_confidence   = agent_result.get("extraction_confidence"),

        # From classify node
        classified_risk          = agent_result.get("risk_level"),
        classified_category      = agent_result.get("complaint_category"),
        classification_reasoning = agent_result.get("classification_reasoning"),

        # From root cause node
        root_cause_analysis = agent_result.get("root_cause_analysis"),
        probable_causes     = json.dumps(agent_result.get("probable_causes") or []),

        # From completeness node
        is_complete    = agent_result.get("is_complete"),
        missing_fields = json.dumps(agent_result.get("missing_fields") or []),

        # From summarize node
        ai_summary = agent_result.get("ai_summary"),

        # From duplicate detection node
        duplicate_score       = agent_result.get("duplicate_score"),
        similar_complaint_ids = json.dumps(agent_result.get("similar_complaint_ids") or []),

        analyzed_at = datetime.utcnow(),
    )
    db.add(analysis)

    # ── Step 7: Save CAPA actions ─────────────────────────────────────────
    # Delete old CAPA actions first if re-running
    db.query(CapaAction).filter(
        CapaAction.complaint_id == complaint.id
    ).delete()

    capa_db_objects = []
    for capa in agent_result.get("capa_actions", []):
        db_capa = CapaAction(
            id           = str(uuid.uuid4()),
            complaint_id = str(complaint.id),
            action_type  = capa.get("action_type", "corrective"),
            title        = capa.get("title", "")[:490],
            description  = capa.get("description", ""),
            priority     = capa.get("priority"),
            assigned_to  = capa.get("assigned_to"),
            due_date_suggestion = capa.get("due_date_suggestion"),
            status       = "open",
            created_at   = datetime.utcnow(),
        )
        db.add(db_capa)
        capa_db_objects.append(db_capa)

    # ── Step 8: Update the complaint with AI results ──────────────────────
    # Only fill empty fields — never overwrite what the user already typed
    if agent_result.get("extracted_product_name") and not complaint.product_name:
        complaint.product_name = agent_result["extracted_product_name"]
    if agent_result.get("extracted_batch_number") and not complaint.batch_number:
        complaint.batch_number = agent_result["extracted_batch_number"]
    if agent_result.get("extracted_customer_name") and not complaint.customer_name:
        complaint.customer_name = agent_result["extracted_customer_name"]
    if agent_result.get("extracted_description") and not complaint.complaint_description:
        complaint.complaint_description = agent_result["extracted_description"]

    # Always update risk + category from AI
    complaint.risk_level   = map_risk_level(agent_result.get("risk_level", ""))
    complaint.category     = map_category(agent_result.get("complaint_category", ""))
    complaint.ai_processed = True
    complaint.updated_at   = datetime.utcnow()

    # Flag as duplicate if score is high
    if (agent_result.get("duplicate_score") or 0) > 0.85:
        complaint.is_duplicate = True

    db.commit()
    db.refresh(complaint)
    db.refresh(analysis)

    return AnalyzeResponse(
        complaint_id = str(complaint.id),
        success      = True,
        message      = "Analysis completed successfully",
        analysis     = analysis,
        capa_actions = capa_db_objects,
    )


# ── GET /analysis/{complaint_id} ──────────────────────────────────────────────

@router.get("/{complaint_id}", response_model=AnalysisResultResponse)
def get_analysis(complaint_id: str, db: Session = Depends(get_db)):
    """
    Fetch the analysis result for a complaint.
    Returns 404 if analysis has not been run yet.
    """
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.complaint_id == complaint_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="No analysis found. Run POST /analysis/analyze first."
        )

    return analysis