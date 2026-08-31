"""Funções de governança (auditoria) e observabilidade (métricas do motor).

Governança (seção 12): toda execução do motor já fica registrada em AllocationRun.
Toda intervenção humana (aceitar/rejeitar/sobrescrever) é registrada aqui em AuditLog,
permitindo responder depois: quem, quando, com quais dados, qual versão, qual resultado.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AllocationAssignment, AllocationRun, AuditLog


def log_audit(db: Session, user: str, action: str, entity: str | None = None,
              entity_id: int | None = None, run_id: int | None = None, details: dict | None = None) -> AuditLog:
    entry = AuditLog(
        user=user,
        action=action,
        entity=entity,
        entity_id=entity_id,
        run_id=run_id,
        details=details or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def compute_engine_metrics(db: Session) -> dict:
    """Indicadores de observabilidade do motor de alocação (seção 13)."""
    runs = db.query(AllocationRun).all()
    n_runs = len(runs)

    if n_runs == 0:
        return {
            "total_executions": 0,
            "last_solve_time_ms": None,
            "avg_solve_time_ms": None,
            "avg_allocation_rate_pct": None,
            "avg_occupancy_pct": None,
            "total_violations": 0,
            "total_unallocated_teams": 0,
            "manual_interventions": 0,
            "errors": 0,
        }

    last_run = max(runs, key=lambda r: r.id)
    avg_solve = sum(r.solve_time_ms for r in runs) / n_runs
    allocation_rates = [
        (r.teams_allocated / r.teams_analyzed * 100) if r.teams_analyzed else 0.0 for r in runs
    ]
    avg_alloc_rate = sum(allocation_rates) / n_runs
    avg_occupancy = sum(r.occupancy_rate for r in runs) / n_runs
    total_violations = sum(r.violations for r in runs)
    total_unallocated = sum(r.teams_unallocated for r in runs)
    errors = sum(1 for r in runs if r.status == "error")

    manual_interventions = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.action.in_(["MANUAL_OVERRIDE", "REJECT"]))
        .scalar()
        or 0
    )

    return {
        "total_executions": n_runs,
        "last_solve_time_ms": last_run.solve_time_ms,
        "avg_solve_time_ms": round(avg_solve, 1),
        "avg_allocation_rate_pct": round(avg_alloc_rate, 1),
        "avg_occupancy_pct": round(avg_occupancy, 1),
        "total_violations": total_violations,
        "total_unallocated_teams": total_unallocated,
        "manual_interventions": manual_interventions,
        "errors": errors,
    }


def compute_dashboard(db: Session, run_id: int | None = None) -> dict:
    """Indicadores executivos do prédio (seção 7), a partir da execução mais recente
    (ou de uma execução específica)."""
    from app.models import Room, Team

    rooms = db.query(Room).all()
    teams = db.query(Team).all()

    if run_id is not None:
        run = db.query(AllocationRun).filter(AllocationRun.id == run_id).first()
    else:
        run = db.query(AllocationRun).order_by(AllocationRun.id.desc()).first()

    total_capacity = sum(r.capacity for r in rooms)
    total_rooms = len(rooms)

    by_floor = {f: {"floor": f, "rooms": 0, "capacity": 0, "occupied_rooms": 0, "allocated_people": 0} for f in range(1, 10)}
    for r in rooms:
        by_floor[r.floor]["rooms"] += 1
        by_floor[r.floor]["capacity"] += r.capacity

    assignments: list[AllocationAssignment] = []
    if run:
        assignments = db.query(AllocationAssignment).filter(AllocationAssignment.run_id == run.id).all()

    allocated_people = 0
    occupied_rooms = 0
    rooms_by_id = {r.id: r for r in rooms}
    teams_by_id = {t.id: t for t in teams}
    violations = 0

    for a in assignments:
        effective_room_id = a.overridden_room_id or a.room_id
        if effective_room_id:
            room = rooms_by_id.get(effective_room_id)
            team = teams_by_id.get(a.team_id)
            if room and team:
                allocated_people += team.size
                occupied_rooms += 1
                by_floor[room.floor]["occupied_rooms"] += 1
                by_floor[room.floor]["allocated_people"] += team.size
                if team.size > room.capacity:
                    violations += 1

    total_employees_in_teams = sum(t.size for t in teams)
    unallocated_teams = len(teams) - len([a for a in assignments if (a.overridden_room_id or a.room_id)])

    return {
        "run_id": run.id if run else None,
        "run_created_at": run.created_at.isoformat() if run else None,
        "total_rooms": total_rooms,
        "total_capacity": total_capacity,
        "rooms_available": len([r for r in rooms if r.available]),
        "rooms_occupied": occupied_rooms,
        "rooms_idle": total_rooms - occupied_rooms,
        "utilization_pct": round(100 * occupied_rooms / total_rooms, 1) if total_rooms else 0.0,
        "total_teams": len(teams),
        "total_employees_in_teams": total_employees_in_teams,
        "allocated_people": allocated_people,
        "unallocated_teams": unallocated_teams,
        "violations": violations,
        "by_floor": list(by_floor.values()),
    }
