from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.engine.allocation_engine import run_allocation
from app.governance import log_audit

router = APIRouter(prefix="/allocation", tags=["allocation"])


@router.post("/generate", response_model=schemas.AllocationRunOut)
def generate_allocation(payload: schemas.GenerateAllocationRequest, db: Session = Depends(get_db)):
    try:
        run = run_allocation(db, user=payload.user, time_limit_seconds=payload.time_limit_seconds)
    except Exception as exc:  # pragma: no cover - guarda de segurança
        error_run = models.AllocationRun(
            user=payload.user,
            algorithm_version="allocation-engine-v1 (CP-SAT)",
            status="error",
            error_message=str(exc),
        )
        db.add(error_run)
        db.commit()
        db.refresh(error_run)
        raise HTTPException(500, f"Falha ao gerar alocação: {exc}") from exc

    log_audit(db, user=payload.user, action="RERUN", entity="allocation_run", entity_id=run.id, run_id=run.id,
              details={"teams_allocated": run.teams_allocated, "teams_unallocated": run.teams_unallocated})
    return run


@router.get("/runs", response_model=list[schemas.AllocationRunOut])
def list_runs(db: Session = Depends(get_db)):
    return db.query(models.AllocationRun).order_by(models.AllocationRun.id.desc()).all()


@router.get("/runs/{run_id}", response_model=schemas.AllocationRunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(models.AllocationRun, run_id)
    if not run:
        raise HTTPException(404, "Execução não encontrada.")
    return run


@router.get("/runs/{run_id}/exceptions", response_model=list[schemas.AssignmentOut])
def get_exceptions(run_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.AllocationAssignment)
        .filter(models.AllocationAssignment.run_id == run_id, models.AllocationAssignment.room_id.is_(None))
        .all()
    )


@router.post("/override", response_model=schemas.AssignmentOut)
def override_assignment(payload: schemas.OverrideRequest, db: Session = Depends(get_db)):
    assignment = db.get(models.AllocationAssignment, payload.assignment_id)
    if not assignment:
        raise HTTPException(404, "Recomendação não encontrada.")

    if payload.action == "ACCEPT":
        assignment.status = "accepted"
    elif payload.action == "REJECT":
        assignment.status = "rejected"
    elif payload.action == "MANUAL_OVERRIDE":
        if payload.new_room_id is None:
            raise HTTPException(400, "new_room_id é obrigatório para MANUAL_OVERRIDE.")
        room = db.get(models.Room, payload.new_room_id)
        if not room:
            raise HTTPException(404, "Sala informada não encontrada.")
        assignment.overridden_room_id = payload.new_room_id
        assignment.status = "overridden"
    else:
        raise HTTPException(400, f"Ação inválida: {payload.action}")

    db.commit()
    db.refresh(assignment)

    log_audit(
        db,
        user=payload.user,
        action=payload.action,
        entity="assignment",
        entity_id=assignment.id,
        run_id=assignment.run_id,
        details={"reason": payload.reason, "new_room_id": payload.new_room_id},
    )
    return assignment
