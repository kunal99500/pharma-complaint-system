from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.complaint_agent import run_complaint_analysis
from database import get_db
from models import (
    Complaint,
    AnalysisResult,
    CapaAction,
    ComplaintCategory,
    ComplaintStatus,
    RiskLevel,
)
from schemas import (
    AnalysisResultResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    CapaActionResponse,
)


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
def analyze_complaint(
    request: AnalyzeRequest,
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

    if complaint.ai_processed and not request.force_reanalyze:
        analysis = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.complaint_id
                == complaint.id
            )
            .first()
        )

        capa_actions = (
            db.query(CapaAction)
            .filter(
                CapaAction.complaint_id
                == complaint.id
            )
            .all()
        )

        return AnalyzeResponse(
            complaint_id=complaint.id,
            success=True,
            message="Complaint has already been analyzed",
            analysis=analysis,
            capa_actions=capa_actions,
        )

    existing_complaints = (
        db.query(Complaint)
        .filter(Complaint.id != complaint.id)
        .all()
    )

    existing_complaint_data = []

    for item in existing_complaints:
        existing_complaint_data.append(
            {
                "id": item.id,
                "complaint_number": item.complaint_number,
                "product_name": item.product_name,
                "batch_number": item.batch_number,
                "customer_name": item.customer_name,
                "complaint_description": item.complaint_description,
                "category": (
                    item.category.value
                    if item.category
                    else None
                ),
                "risk_level": (
                    item.risk_level.value
                    if item.risk_level
                    else None
                ),
            }
        )

    try:
        result = run_complaint_analysis(
            raw_text=complaint.raw_input or "",
            complaint_id=complaint.id,
            existing_complaints=existing_complaint_data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(exc)}",
        )

    if result.get("errors"):
        raise HTTPException(
            status_code=500,
            detail=result["errors"][0],
        )

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
        or result.get(
            "extracted_customer_requested_action"
        )
    )

    risk_level = result.get("risk_level")

    if risk_level:
        try:
            complaint.risk_level = RiskLevel(
                risk_level
            )
        except ValueError:
            complaint.risk_level = RiskLevel.UNKNOWN

    category = result.get("complaint_category")

    if category:
        try:
            complaint.category = ComplaintCategory(
                category
            )
        except ValueError:
            complaint.category = ComplaintCategory.OTHER

    complaint.ai_processed = True

    complaint.status = ComplaintStatus.UNDER_REVIEW

    duplicate_score = result.get(
        "duplicate_score",
        0.0,
    )

    similar_ids = result.get(
        "similar_complaint_ids",
        [],
    )

    complaint.is_duplicate = (
        duplicate_score >= 0.8
    )

    if complaint.is_duplicate and similar_ids:
        complaint.duplicate_of_id = (
            similar_ids[0]
        )

    if request.force_reanalyze:
        old_analysis = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.complaint_id
                == complaint.id
            )
            .first()
        )

        if old_analysis:
            db.delete(old_analysis)

        old_capa_actions = (
            db.query(CapaAction)
            .filter(
                CapaAction.complaint_id
                == complaint.id
            )
            .all()
        )

        for action in old_capa_actions:
            db.delete(action)

        db.flush()

    analysis = AnalysisResult(
        complaint_id=complaint.id,
        extraction_confidence=result.get(
            "extraction_confidence"
        ),
        classified_risk=result.get(
            "risk_level"
        ),
        classified_category=result.get(
            "complaint_category"
        ),
        classification_reasoning=result.get(
            "classification_reasoning"
        ),
        regulatory_reference=result.get(
            "regulatory_reference"
        ),
        root_cause_analysis=result.get(
            "root_cause_analysis"
        ),
        probable_causes=result.get(
            "probable_causes",
            []
        ),
        is_complete=result.get(
            "is_complete"
        ),
        missing_fields=result.get(
            "missing_fields",
            []
        ),
        ai_summary=result.get(
            "ai_summary"
        ),
        duplicate_score=duplicate_score,
        similar_complaint_ids=similar_ids,
    )

    db.add(analysis)
    db.flush()

    capa_actions = []

    for action in result.get(
        "capa_actions",
        [],
    ):
        capa_action = CapaAction(
            complaint_id=complaint.id,
            action_type=action.get(
                "action_type",
                "corrective",
            ),
            title=action.get(
                "title",
                "CAPA Action",
            ),
            description=action.get(
                "description",
                "",
            ),
            priority=action.get(
                "priority"
            ),
            assigned_to=action.get(
                "assigned_to"
            ),
            due_date_suggestion=action.get(
                "due_date_suggestion"
            ),
            status=action.get(
                "status",
                "open",
            ),
        )

        db.add(capa_action)
        capa_actions.append(capa_action)

    db.commit()

    db.refresh(complaint)
    db.refresh(analysis)

    for action in capa_actions:
        db.refresh(action)

    return AnalyzeResponse(
        complaint_id=complaint.id,
        success=True,
        message="Complaint analyzed successfully",
        analysis=analysis,
        capa_actions=capa_actions,
    )


@router.get(
    "/{complaint_id}",
    response_model=AnalyzeResponse,
)
def get_analysis(
    complaint_id: str,
    db: Session = Depends(get_db),
):
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
        .filter(
            AnalysisResult.complaint_id
            == complaint_id
        )
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    capa_actions = (
        db.query(CapaAction)
        .filter(
            CapaAction.complaint_id
            == complaint_id
        )
        .all()
    )

    return AnalyzeResponse(
        complaint_id=complaint_id,
        success=True,
        message="Analysis retrieved successfully",
        analysis=analysis,
        capa_actions=capa_actions,
    )