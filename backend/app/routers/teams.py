from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.governance import log_audit

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[schemas.TeamOut])
def list_teams(sector_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Team)
    if sector_id is not None:
        q = q.filter(models.Team.sector_id == sector_id)
    return q.order_by(models.Team.sector_id, models.Team.name).all()


@router.post("", response_model=schemas.TeamOut, status_code=201)
def create_team(payload: schemas.TeamCreate, db: Session = Depends(get_db)):
    sector = db.get(models.Sector, payload.sector_id)
    if not sector:
        raise HTTPException(404, "Setor não encontrado.")
    team = models.Team(**payload.model_dump())
    db.add(team)
    sector.employee_count = (sector.employee_count or 0) + team.size
    db.commit()
    db.refresh(team)
    log_audit(db, user=sector.coordinator_name, action="CREATE", entity="team", entity_id=team.id,
              details={"name": team.name, "size": team.size, "sector": sector.name})
    return team


@router.put("/{team_id}", response_model=schemas.TeamOut)
def update_team(team_id: int, payload: schemas.TeamUpdate, db: Session = Depends(get_db)):
    team = db.get(models.Team, team_id)
    if not team:
        raise HTTPException(404, "Equipe não encontrada.")
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(team, k, v)
    db.commit()
    db.refresh(team)
    log_audit(db, user=team.sector.coordinator_name, action="UPDATE", entity="team", entity_id=team.id, details=changes)
    return team


@router.delete("/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.get(models.Team, team_id)
    if not team:
        raise HTTPException(404, "Equipe não encontrada.")
    db.delete(team)
    db.commit()
