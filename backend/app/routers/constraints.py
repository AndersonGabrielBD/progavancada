from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/constraints", tags=["constraints"])


@router.get("", response_model=list[schemas.ConstraintOut])
def list_constraints(db: Session = Depends(get_db)):
    return db.query(models.ConstraintRule).order_by(models.ConstraintRule.id).all()


@router.post("", response_model=schemas.ConstraintOut, status_code=201)
def create_constraint(payload: schemas.ConstraintCreate, db: Session = Depends(get_db)):
    rule = models.ConstraintRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{constraint_id}", status_code=204)
def delete_constraint(constraint_id: int, db: Session = Depends(get_db)):
    rule = db.get(models.ConstraintRule, constraint_id)
    if not rule:
        raise HTTPException(404, "Restrição não encontrada.")
    db.delete(rule)
    db.commit()


@router.patch("/{constraint_id}/toggle", response_model=schemas.ConstraintOut)
def toggle_constraint(constraint_id: int, db: Session = Depends(get_db)):
    rule = db.get(models.ConstraintRule, constraint_id)
    if not rule:
        raise HTTPException(404, "Restrição não encontrada.")
    rule.active = not rule.active
    db.commit()
    db.refresh(rule)
    return rule
