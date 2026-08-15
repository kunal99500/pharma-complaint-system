from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.complaint_agent import run_complaint_analysis
from database import get_db, SessionLocal
from models import (
    AnalysisResult,
    CapaAction,
    Complaint,
    ComplaintCategory,
    ComplaintStatus,
    RiskLevel,
)
from schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
)


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


def _save_analysis_result(
    complaint_id: str,
    result: dict,
    force_reanalyze: bool = False,
):
    """
    Persist analysis results to the database.
    Runs inside the background task — uses its own db session.
    Handles partial results gracefully using success flags.
    """
    db = SessionLocal()

    try:
        complaint = (
            db.query(Complaint)
            .filter(Complaint.id == complaint_id)
            .first()
        )

        if not complaint:
            return

        # --- Mark as processing so frontend knows work is happening ---
        complaint.analysis_status = "processing"
        db.commit()

        # --- If force re-analyze, delete old records first ---
        if force_reanalyze:
            old_analysis = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.complaint_id == complaint_id)
                .first()
            )
            if old_analysis:
                db.delete(old_analysis)

            old_capa = (
                db.query(CapaAction)
                .filter(CapaAction.complaint_id == complaint_id)
                .all()
            )
            for action in old_capa:
                db.delete(action)

            db.flush()

        # --- Apply extracted fields if extraction succeeded ---
        if result.get("extraction_success"):
            complaint.customer_name = (
                complaint.customer_name
                or result.get("extracted_customer_name")
            )
            complaint.customer_email = (
                complaint.customer_email
                or result.get("extracted_customer_email")
            )
            complaint.customer_phone = (
                complaint.customer_phone
                or result.get("extracted_customer_phone")
            )
            complaint.customer_company = (
                complaint.customer_company
                or result.get("extracted_customer_company")
            )
            complaint.customer_country = (
                complaint.customer_country
                or result.get("extracted_customer_country")
            )
            complaint.product_name = (
                complaint.product_name
                or result.get("extracted_product_name")
            )
            complaint.batch_number = (
                complaint.batch_number
                or result.get("extracted_batch_number")
            )
            complaint.manufacturing_date = (
                complaint.manufacturing_date
                or result.get("extracted_manufacturing_date")
            )
            complaint.expiry_date = (
                complaint.expiry_date
                or result.get("extracted_expiry_date")
            )
            complaint.quantity_affected = (
                complaint.quantity_affected
                or result.get("extracted_quantity_affected")
            )
            complaint.date_of_complaint = (
                complaint.date_of_complaint
                or result.get("extracted_date_of_complaint")
            )
            complaint.complaint_description = (
                complaint.complaint_description
                or result.get("extracted_description")
            )
            complaint.storage_conditions = (
                complaint.storage_conditions
                or result.get("extracted_storage_conditions")
            )
            complaint.actions_taken = (
                complaint.actions_taken
                or result.get("extracted_actions_taken")
            )
            complaint.coa_information = (
                complaint.coa_information
                or result.get("extracted_coa_information")
            )
            complaint.customer_requested_action = (
                complaint.customer_requested_action
                or result.get("extracted_customer_requested_action")
            )

        # --- Apply classification if it succeeded ---
        if result.get("classification_success"):
            risk_level = result.get("risk_level")
            if risk_level:
                try:
                    complaint.risk_level = RiskLevel(risk_level)
                except ValueError:
                    complaint.risk_level = RiskLevel.UNKNOWN

            category = result.get("complaint_category")
            if category:
                try:
                    complaint.category = ComplaintCategory(category)
                except ValueError:
                    complaint.category = ComplaintCategory.OTHER

            complaint.status = ComplaintStatus.UNDER_REVIEW

        # --- Apply duplicate detection ---
        duplicate_score = result.get("duplicate_score", 0.0) or 0.0
        similar_ids = result.get("similar_complaint_ids", []) or []

        complaint.is_duplicate = duplicate_score >= 0.8
        if complaint.is_duplicate and similar_ids:
            complaint.duplicate_of_id = similar_ids[0]

        # --- Determine final analysis status ---
        errors = result.get("errors", [])
        extraction_ok = result.get("extraction_success", False)
        classification_ok = result.get("classification_success", False)

        if not extraction_ok:
            # Nothing worked — full failure
            complaint.analysis_status = "failed"
        elif not classification_ok:
            # Partial — extracted but could not classify
            complaint.analysis_status = "partial"
        else:
            # All good
            complaint.analysis_status = "completed"
            complaint.ai_processed = True

        # --- Save AnalysisResult record ---
        analysis = AnalysisResult(
            complaint_id=complaint.id,
            extraction_confidence=result.get("extraction_confidence"),
            classified_risk=result.get("risk_level"),
            classified_category=result.get("complaint_category"),
            classification_reasoning=result.get("classification_reasoning"),
            regulatory_reference=result.get("regulatory_reference"),
            root_cause_analysis=result.get("root_cause_analysis"),
            probable_causes=result.get("probable_causes", []),
            is_complete=result.get("is_complete"),
            missing_fields=result.get("missing_fields", []),
            ai_summary=result.get("ai_summary"),
            duplicate_score=duplicate_score,
            similar_complaint_ids=similar_ids,
        )
        db.add(analysis)

        # --- Save CAPA actions ---
        for action in result.get("capa_actions", []):
            capa_action = CapaAction(
                complaint_id=complaint.id,
                action_type=action.get("action_type", "corrective"),
                title=action.get("title", "CAPA Action"),
                description=action.get("description", ""),
                priority=action.get("priority"),
                assigned_to=action.get("assigned_to"),
                due_date_suggestion=action.get("due_date_suggestion"),
                status=action.get("status", "open"),
            )
            db.add(capa_action)

        db.commit()

    except Exception as exc:
        db.rollback()
        # Best-effort: mark complaint as failed
        try:
            complaint = (
                db.query(Complaint)
                .filter(Complaint.id == complaint_id)
                .first()
            )
            if complaint:
                complaint.analysis_status = "failed"
                db.commit()
        except Exception:
            pass

    finally:
        db.close()


def _run_analysis_task(
    complaint_id: str,
    raw_text: str,
    existing_complaint_data: list,
    force_reanalyze: bool,
):
    """
    Background task entry point.
    Runs the LangGraph pipeline then saves results.
    """
    try:
        result = run_complaint_analysis(
            raw_text=raw_text,
            complaint_id=complaint_id,
            existing_complaints=existing_complaint_data,
        )
    except Exception as exc:
        result = {
            "extraction_success": False,
            "classification_success": False,
            "capa_success": False,
            "errors": [f"Pipeline failed entirely: {str(exc)}"],
        }

    _save_analysis_result(
        complaint_id=complaint_id,
        result=result,
        force_reanalyze=force_reanalyze,
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
def analyze_complaint(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == request.complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    # Already analyzed and not forcing re-run — return cached result
    if complaint.ai_processed and not request.force_reanalyze:
        analysis = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.complaint_id == complaint.id)
            .first()
        )
        capa_actions = (
            db.query(CapaAction)
            .filter(CapaAction.complaint_id == complaint.id)
            .all()
        )
        return AnalyzeResponse(
            complaint_id=complaint.id,
            success=True,
            message="Complaint already analyzed",
            analysis_status=complaint.analysis_status or "completed",
            analysis=analysis,
            capa_actions=capa_actions,
        )

    # Already processing — do not queue again
    if complaint.analysis_status == "processing":
        return AnalyzeResponse(
            complaint_id=complaint.id,
            success=True,
            message="Analysis already in progress",
            analysis_status="processing",
        )

    # Build existing complaints context for duplicate detection
    existing_complaints = (
        db.query(Complaint)
        .filter(Complaint.id != complaint.id)
        .all()
    )

    existing_complaint_data = [
        {
            "id": item.id,
            "complaint_number": item.complaint_number,
            "product_name": item.product_name,
            "batch_number": item.batch_number,
            "customer_name": item.customer_name,
            "complaint_description": item.complaint_description,
            "category": item.category.value if item.category else None,
            "risk_level": item.risk_level.value if item.risk_level else None,
        }
        for item in existing_complaints
    ]

    # Mark as queued immediately so the frontend knows
    complaint.analysis_status = "processing"
    db.commit()

    # Queue the background task — returns immediately to the client
    background_tasks.add_task(
        _run_analysis_task,
        complaint_id=complaint.id,
        raw_text=complaint.raw_input or "",
        existing_complaint_data=existing_complaint_data,
        force_reanalyze=request.force_reanalyze,
    )

    return AnalyzeResponse(
        complaint_id=complaint.id,
        success=True,
        message="Analysis started. Poll GET /analysis/{complaint_id} for results.",
        analysis_status="processing",
    )


@router.get(
    "/{complaint_id}",
    response_model=AnalyzeResponse,
)
def get_analysis(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    """
    Poll this endpoint after triggering analysis.
    Returns current status and results when ready.
    """
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.complaint_id == complaint_id)
        .first()
    )

    capa_actions = (
        db.query(CapaAction)
        .filter(CapaAction.complaint_id == complaint_id)
        .all()
    )

    status = complaint.analysis_status or "pending"

    if status == "processing":
        message = "Analysis in progress"
    elif status == "completed":
        message = "Analysis completed successfully"
    elif status == "partial":
        message = "Analysis partially completed — extraction succeeded but classification failed"
    elif status == "failed":
        message = "Analysis failed"
    else:
        message = "Analysis not started"

    return AnalyzeResponse(
        complaint_id=complaint_id,
        success=status not in ("failed",),
        message=message,
        analysis_status=status,
        analysis=analysis,
        capa_actions=capa_actions,
    )