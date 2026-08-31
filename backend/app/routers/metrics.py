from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.engine.baseline import compute_baseline
from app.governance import compute_dashboard, compute_engine_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard")
def get_dashboard(run_id: int | None = None, db: Session = Depends(get_db)):
    return compute_dashboard(db, run_id=run_id)


@router.get("/engine")
def get_engine_metrics(db: Session = Depends(get_db)):
    return compute_engine_metrics(db)


@router.get("/comparison")
def get_comparison(run_id: int | None = None, db: Session = Depends(get_db)):
    baseline = compute_baseline(db)

    if run_id is not None:
        run = db.get(models.AllocationRun, run_id)
    else:
        run = db.query(models.AllocationRun).order_by(models.AllocationRun.id.desc()).first()

    if not run:
        return {"before": baseline, "after": None}

    assignments = db.query(models.AllocationAssignment).filter(models.AllocationAssignment.run_id == run.id).all()
    rooms_by_id = {r.id: r for r in db.query(models.Room).all()}
    teams_by_id = {t.id: t for t in db.query(models.Team).all()}

    idle_seats = 0
    for a in assignments:
        room_id = a.overridden_room_id or a.room_id
        if room_id:
            room = rooms_by_id.get(room_id)
            team = teams_by_id.get(a.team_id)
            if room and team:
                idle_seats += room.capacity - team.size

    after = {
        "teams_allocated": run.teams_allocated,
        "teams_unallocated": run.teams_unallocated,
        "avg_occupancy_pct": run.occupancy_rate,
        "idle_seats": idle_seats,
        "violations": run.violations,
    }
    return {"before": baseline, "after": after, "run_id": run.id}
