from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/sectors", tags=["sectors"])


@router.get("", response_model=list[schemas.SectorOut])
def list_sectors(db: Session = Depends(get_db)):
    return db.query(models.Sector).order_by(models.Sector.name).all()


@router.post("", response_model=schemas.SectorOut, status_code=201)
def create_sector(payload: schemas.SectorCreate, db: Session = Depends(get_db)):
    if db.query(models.Sector).filter(models.Sector.name == payload.name).first():
        raise HTTPException(400, "Já existe um setor com esse nome.")
    sector = models.Sector(**payload.model_dump())
    db.add(sector)
    db.commit()
    db.refresh(sector)
    return sector


@router.get("/{sector_id}", response_model=schemas.SectorOut)
def get_sector(sector_id: int, db: Session = Depends(get_db)):
    sector = db.get(models.Sector, sector_id)
    if not sector:
        raise HTTPException(404, "Setor não encontrado.")
    return sector
