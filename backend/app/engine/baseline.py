"""Estratégia 'ingênua' (first-fit, sem otimização), usada apenas como referência
de comparação 'Antes' na tela de comparação (seção 8). Representa o processo manual:
cada equipe recebe a primeira sala compatível encontrada, sem buscar o melhor encaixe.
"""
from sqlalchemy.orm import Session

from app.engine.candidates import build_candidates
from app.models import ConstraintRule, Room, Team


def compute_baseline(db: Session) -> dict:
    teams: list[Team] = db.query(Team).order_by(Team.id).all()
    rooms: list[Room] = db.query(Room).order_by(Room.id).all()
    rules: list[ConstraintRule] = db.query(ConstraintRule).filter(ConstraintRule.active == True).all()  # noqa: E712

    used_rooms: set[int] = set()
    allocated = 0
    unallocated = 0
    occ_ratios = []
    idle_seats_total = 0

    for team in teams:
        candidates = build_candidates(team, rooms, rules).rooms
        candidates = [r for r in candidates if r.id not in used_rooms]
        if not candidates:
            unallocated += 1
            continue
        room = candidates[0]  # primeira sala compatível, sem otimizar o encaixe
        used_rooms.add(room.id)
        allocated += 1
        occ_ratios.append(100 * team.size / room.capacity)
        idle_seats_total += room.capacity - team.size

    total_rooms = len(rooms)
    return {
        "teams_allocated": allocated,
        "teams_unallocated": unallocated,
        "avg_occupancy_pct": round(sum(occ_ratios) / len(occ_ratios), 1) if occ_ratios else 0.0,
        "idle_seats": idle_seats_total,
        "rooms_used": len(used_rooms),
        "rooms_idle": total_rooms - len(used_rooms),
        "violations": 0,
    }
