from fastapi import FastAPI, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session as OrmSession
from models import Contractor, Session
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import io
import csv

app = FastAPI(title="GAF Contractor Insights API", description="Query contractors and AI-generated insights.")

# Pydantic schema for API responses
class ContractorOut(BaseModel):
    id: int
    name: Optional[str]
    rating: Optional[float]
    reviews: Optional[int]
    phone: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    certifications: Optional[str]
    type: Optional[str]
    contractor_id: Optional[str]
    url: Optional[str]
    insight: Optional[str]
    relevance_score: Optional[int]
    actionability_score: Optional[int]
    accuracy_score: Optional[int]
    clarity_score: Optional[int]
    evaluation_comment: Optional[str]
    manual_evaluation_comment: Optional[str]
    business_summary: Optional[str]
    sales_tip: Optional[str]
    risk_alert: Optional[str]
    priority_suggestion: Optional[str]
    next_action: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        orm_mode = True

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

@app.get("/contractors", response_model=List[ContractorOut])
def list_contractors(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Max number of records to return"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    max_rating: Optional[float] = Query(None, description="Maximum rating"),
    certification: Optional[str] = Query(None, description="Filter by certification substring"),
    order_by: Optional[str] = Query(None, description="Order by field: rating, reviews, updated_at"),
    order_desc: bool = Query(True, description="Descending order if true"),
    db: OrmSession = Depends(get_db)
):
    """List contractors with advanced filters and ordering."""
    try:
        query = db.query(Contractor)
        if city:
            query = query.filter(Contractor.city == city)
        if state:
            query = query.filter(Contractor.state == state)
        if min_rating is not None:
            query = query.filter(Contractor.rating >= min_rating)
        if max_rating is not None:
            query = query.filter(Contractor.rating <= max_rating)
        if certification:
            query = query.filter(Contractor.certifications.like(f"%{certification}%"))
        if order_by:
            field = getattr(Contractor, order_by, None)
            if field is not None:
                query = query.order_by(field.desc() if order_desc else field.asc())
        result = query.offset(skip).limit(limit).all()
        return result
    except Exception as e:
        import traceback
        print("Error in /contractors endpoint:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contractors/{contractor_id}", response_model=ContractorOut)
def get_contractor(contractor_id: str, db: OrmSession = Depends(get_db)):
    """Get contractor details by contractor_id."""
    contractor = db.query(Contractor).filter(Contractor.contractor_id == contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return contractor

@app.get("/export")
def export_contractors(
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    max_rating: Optional[float] = Query(None),
    certification: Optional[str] = Query(None),
    db: OrmSession = Depends(get_db)
):
    """Export filtered contractors as CSV."""
    query = db.query(Contractor)
    if city:
        query = query.filter(Contractor.city == city)
    if state:
        query = query.filter(Contractor.state == state)
    if min_rating is not None:
        query = query.filter(Contractor.rating >= min_rating)
    if max_rating is not None:
        query = query.filter(Contractor.rating <= max_rating)
    if certification:
        query = query.filter(Contractor.certifications.like(f"%{certification}%"))
    contractors = query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    header = [c.name for c in Contractor.__table__.columns]
    writer.writerow(header)
    for c in contractors:
        writer.writerow([getattr(c, col) for col in header])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=contractors_export.csv"})

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the GAF Contractor Insights API. See /docs for Swagger UI."} 