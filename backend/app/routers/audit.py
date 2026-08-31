from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[schemas.AuditLogOut])
def list_audit_logs(run_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.AuditLog)
    if run_id is not None:
        q = q.filter(models.AuditLog.run_id == run_id)
    return q.order_by(models.AuditLog.id.desc()).limit(200).all()
