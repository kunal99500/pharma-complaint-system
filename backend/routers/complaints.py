import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Attachment,
    Complaint,
    ComplaintCategory,
    ComplaintStatus,
    RiskLevel,
)
from schemas import (
    ComplaintCreate,
    ComplaintListItem,
    ComplaintResponse,
    ComplaintUpdate,
)


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def generate_complaint_number():
    return f"CMP-{uuid.uuid4().hex[:8].upper()}"


def get_complaint_or_404(
    complaint_id: str,
    db: Session,
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

    return complaint


def extract_file_text(
    file_path: str,
    file_type: str,
):
    if file_type == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)

            return "\n".join(text)

        except Exception:
            return ""

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


@router.post(
    "",
    response_model=ComplaintResponse,
)
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
):
    complaint = Complaint(
        complaint_number=generate_complaint_number(),
        source_type=complaint_data.source_type,
        raw_input=complaint_data.raw_input,
        customer_name=complaint_data.customer_name,
        customer_email=complaint_data.customer_email,
        customer_phone=complaint_data.customer_phone,
        customer_company=complaint_data.customer_company,
        customer_country=complaint_data.customer_country,
        product_name=complaint_data.product_name,
        batch_number=complaint_data.batch_number,
        manufacturing_date=complaint_data.manufacturing_date,
        expiry_date=complaint_data.expiry_date,
        quantity_affected=complaint_data.quantity_affected,
        complaint_description=complaint_data.complaint_description,
        date_of_complaint=complaint_data.date_of_complaint,
        category=complaint_data.category,
        storage_conditions=complaint_data.storage_conditions,
        actions_taken=complaint_data.actions_taken,
        coa_information=complaint_data.coa_information,
        customer_requested_action=complaint_data.customer_requested_action,
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint


@router.post(
    "/upload",
    response_model=ComplaintResponse,
)
async def upload_complaint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    extension = os.path.splitext(file.filename)[1].lower()

    allowed_extensions = {
        ".pdf": "pdf",
        ".txt": "text",
        ".eml": "email",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT and EML files are supported",
        )

    file_type = allowed_extensions[extension]
    unique_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    contents = await file.read()

    with open(file_path, "wb") as saved_file:
        saved_file.write(contents)

    extracted_text = extract_file_text(file_path, file_type)

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the uploaded file",
        )

    complaint = Complaint(
        complaint_number=generate_complaint_number(),
        source_type=file_type,
        raw_input=extracted_text,
    )

    db.add(complaint)
    db.flush()

    attachment = Attachment(
        complaint_id=complaint.id,
        filename=file.filename,
        file_type=file_type,
        file_size=len(contents),
        storage_path=file_path,
        extracted_text=extracted_text,
    )

    db.add(attachment)
    db.commit()
    db.refresh(complaint)

    return complaint


@router.get(
    "",
    response_model=list[ComplaintListItem],
)
def list_complaints(
    status: Optional[ComplaintStatus] = Query(default=None),
    risk_level: Optional[RiskLevel] = Query(default=None),
    category: Optional[ComplaintCategory] = Query(default=None),
    ai_processed: Optional[bool] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)

    if status is not None:
        query = query.filter(Complaint.status == status)

    if risk_level is not None:
        query = query.filter(Complaint.risk_level == risk_level)

    if category is not None:
        query = query.filter(Complaint.category == category)

    if ai_processed is not None:
        query = query.filter(Complaint.ai_processed == ai_processed)

    complaints = (
        query
        .order_by(Complaint.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return complaints


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
)
def get_complaint(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    return get_complaint_or_404(complaint_id, db)


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintResponse,
)
def update_complaint(
    complaint_id: str,
    complaint_data: ComplaintUpdate,
    db: Session = Depends(get_db),
):
    complaint = get_complaint_or_404(complaint_id, db)

    update_data = complaint_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(complaint, field, value)

    db.commit()
    db.refresh(complaint)

    return complaint


@router.delete("/{complaint_id}")
def delete_complaint(
    complaint_id: str,
    db: Session = Depends(get_db),
):
    complaint = get_complaint_or_404(complaint_id, db)

    db.delete(complaint)
    db.commit()

    return {
        "success": True,
        "message": "Complaint deleted successfully",
    }