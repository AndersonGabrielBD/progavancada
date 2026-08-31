"""Motor de alocação: modela o problema como Programação por Restrições (CP-SAT,
Google OR-Tools) e resolve como um problema de atribuição equipe->sala com
restrições obrigatórias (hard) e uma função objetivo que pondera ocupação,
prioridade, preferência de andar, proximidade entre equipes e ociosidade.

ALGORITHM_VERSION é registrado em cada execução para fins de governança (seção 12).
"""
import time

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from app.ai.explainer import generate_explanation
from app.engine.candidates import build_candidates
from app.models import (
    AllocationAssignment,
    AllocationRun,
    ConstraintRule,
    ConstraintType,
    Room,
    Team,
)

ALGORITHM_VERSION = "allocation-engine-v1 (CP-SAT)"

ASSIGN_BASE = 1000
PRIORITY_WEIGHT = 20
IDLE_PENALTY = 2
PREFERRED_FLOOR_BONUS = 50
PROXIMITY_BONUS = 150


def run_allocation(db: Session, user: str = "coordenador-geral", time_limit_seconds: float = 5.0) -> AllocationRun:
    start = time.perf_counter()

    teams: list[Team] = db.query(Team).all()
    rooms: list[Room] = db.query(Room).all()
    rules: list[ConstraintRule] = db.query(ConstraintRule).filter(ConstraintRule.active == True).all()  # noqa: E712

    model = cp_model.CpModel()

    x: dict[tuple[int, int], cp_model.IntVar] = {}
    candidates_by_team: dict[int, list[Room]] = {}
    elimination_by_team: dict[int, tuple[str, str]] = {}

    for team in teams:
        result = build_candidates(team, rooms, rules)
        candidates_by_team[team.id] = result.rooms
        if result.elimination_stage:
            elimination_by_team[team.id] = (result.elimination_stage, result.elimination_detail)
        for room in result.rooms:
            x[(team.id, room.id)] = model.NewBoolVar(f"x_t{team.id}_r{room.id}")

    # cada equipe em no máximo 1 sala
    for team in teams:
        vars_for_team = [x[(team.id, r.id)] for r in candidates_by_team[team.id]]
        if vars_for_team:
            model.Add(sum(vars_for_team) <= 1)

    # cada sala usada por no máximo 1 equipe
    rooms_by_id = {r.id: r for r in rooms}
    for room in rooms:
        vars_for_room = [x[(t.id, room.id)] for t in teams if (t.id, room.id) in x]
        if vars_for_room:
            model.Add(sum(vars_for_room) <= 1)

    allocated_bool: dict[int, cp_model.IntVar] = {}
    floor_var: dict[int, cp_model.IntVar] = {}
    for team in teams:
        cands = candidates_by_team[team.id]
        allocated = model.NewBoolVar(f"alloc_{team.id}")
        team_vars = [x[(team.id, r.id)] for r in cands]
        if team_vars:
            model.Add(allocated == sum(team_vars))
        else:
            model.Add(allocated == 0)
        allocated_bool[team.id] = allocated

        fvar = model.NewIntVar(0, 9, f"floor_{team.id}")
        if team_vars:
            model.Add(fvar == sum(x[(team.id, r.id)] * r.floor for r in cands))
        else:
            model.Add(fvar == 0)
        floor_var[team.id] = fvar

    # restrição de exclusão: dois setores não podem compartilhar o mesmo andar
    exclusion_rules = [r for r in rules if r.type == ConstraintType.EXCLUSION]
    teams_by_sector: dict[int, list[Team]] = {}
    for t in teams:
        teams_by_sector.setdefault(t.sector_id, []).append(t)

    for rule in exclusion_rules:
        sector_a, sector_b = rule.sector_id, rule.sector_id_b
        if sector_a is None or sector_b is None:
            continue
        teams_a = teams_by_sector.get(sector_a, [])
        teams_b = teams_by_sector.get(sector_b, [])
        for floor in range(1, 10):
            vars_a = [x[(t.id, r.id)] for t in teams_a for r in candidates_by_team[t.id] if r.floor == floor and (t.id, r.id) in x]
            vars_b = [x[(t.id, r.id)] for t in teams_b for r in candidates_by_team[t.id] if r.floor == floor and (t.id, r.id) in x]
            if not vars_a or not vars_b:
                continue
            occ_a = model.NewBoolVar(f"occA_{rule.id}_{floor}")
            occ_b = model.NewBoolVar(f"occB_{rule.id}_{floor}")
            model.AddMaxEquality(occ_a, vars_a)
            model.AddMaxEquality(occ_b, vars_b)
            model.Add(occ_a + occ_b <= 1)

    # bônus de proximidade (soft): equipes relacionadas devem ficar em andares próximos
    proximity_terms = []
    proximity_rules = [r for r in rules if r.type == ConstraintType.PROXIMITY]
    for rule in proximity_rules:
        if rule.team_id is None or rule.team_id_b is None:
            continue
        if rule.team_id not in floor_var or rule.team_id_b not in floor_var:
            continue
        max_dist = rule.payload.get("max_floor_distance", 1)
        diff = model.NewIntVar(-9, 9, f"diff_{rule.id}")
        model.Add(diff == floor_var[rule.team_id] - floor_var[rule.team_id_b])
        abs_diff = model.NewIntVar(0, 9, f"absdiff_{rule.id}")
        model.AddAbsEquality(abs_diff, diff)
        close = model.NewBoolVar(f"close_{rule.id}")
        model.Add(abs_diff <= max_dist).OnlyEnforceIf(close)
        model.Add(abs_diff > max_dist).OnlyEnforceIf(close.Not())
        both_allocated = model.NewBoolVar(f"both_{rule.id}")
        model.AddMultiplicationEquality(both_allocated, [allocated_bool[rule.team_id], allocated_bool[rule.team_id_b]])
        effective = model.NewBoolVar(f"prox_eff_{rule.id}")
        model.AddMultiplicationEquality(effective, [close, both_allocated])
        proximity_terms.append(effective)

    objective_terms = []
    teams_by_id = {t.id: t for t in teams}
    for (team_id, room_id), var in x.items():
        team = teams_by_id[team_id]
        room = rooms_by_id[room_id]
        occupancy_pct = round(100 * team.size / room.capacity)
        idle_seats = room.capacity - team.size
        score = ASSIGN_BASE
        score += PRIORITY_WEIGHT * team.priority
        score += occupancy_pct
        score -= IDLE_PENALTY * idle_seats
        if team.preferred_floor is not None and team.preferred_floor == room.floor:
            score += PREFERRED_FLOOR_BONUS
        objective_terms.append(score * var)

    for term in proximity_terms:
        objective_terms.append(PROXIMITY_BONUS * term)

    if objective_terms:
        model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    solve_time_ms = (time.perf_counter() - start) * 1000

    run = AllocationRun(
        user=user,
        algorithm_version=ALGORITHM_VERSION,
        teams_analyzed=len(teams),
        rooms_analyzed=len(rooms),
        solve_time_ms=round(solve_time_ms, 2),
    )
    db.add(run)
    db.flush()

    allocated_count = 0
    violations = 0
    occ_ratios = []

    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    for team in teams:
        cands = candidates_by_team[team.id]
        assigned_room = None
        if feasible:
            for room in cands:
                if solver.Value(x[(team.id, room.id)]) == 1:
                    assigned_room = room
                    break

        if assigned_room is not None:
            if assigned_room.capacity < team.size:
                violations += 1  # não deveria acontecer; guarda de sanidade (critério de aceitação #1)

            occupancy_pct = round(100 * team.size / assigned_room.capacity, 1)
            occ_ratios.append(occupancy_pct)
            justification = {
                "capacity": assigned_room.capacity,
                "team_size": team.size,
                "occupancy_pct": occupancy_pct,
                "floor": assigned_room.floor,
                "resources_required": team.special_requirements,
                "resources_available": assigned_room.resources,
                "resources_ok": set(team.special_requirements or []).issubset(set(assigned_room.resources or [])),
                "accessibility_required": team.needs_accessibility,
                "accessibility_ok": (not team.needs_accessibility) or assigned_room.accessibility,
                "alternatives_evaluated": len(cands),
                "priority": team.priority,
            }
            explanation_text = generate_explanation(
                {
                    "team_name": team.name,
                    "room_code": assigned_room.code,
                    **justification,
                }
            )
            assignment = AllocationAssignment(
                run_id=run.id,
                team_id=team.id,
                room_id=assigned_room.id,
                occupancy_pct=occupancy_pct,
                alternatives_evaluated=len(cands),
                justification=justification,
                explanation_text=explanation_text,
                status="recommended",
            )
            allocated_count += 1
        else:
            stage, detail = elimination_by_team.get(team.id, ("contencao", None))
            if stage != "contencao" or not cands:
                reason = detail or "Nenhuma sala candidata restou após aplicar as restrições obrigatórias."
            else:
                reason = (
                    f"{len(cands)} sala(s) compatível(is) foram encontradas, mas todas foram "
                    "atribuídas a outras equipes com prioridade/pontuação maior nesta execução "
                    "(concorrência por capacidade)."
                )
            assignment = AllocationAssignment(
                run_id=run.id,
                team_id=team.id,
                room_id=None,
                occupancy_pct=None,
                alternatives_evaluated=len(cands),
                justification={"eliminated_at_stage": stage, "candidates_found": len(cands)},
                explanation_text=None,
                reason_unallocated=reason,
                status="recommended",
            )
        db.add(assignment)

    run.teams_allocated = allocated_count
    run.teams_unallocated = len(teams) - allocated_count
    run.violations = violations
    run.occupancy_rate = round(sum(occ_ratios) / len(occ_ratios), 1) if occ_ratios else 0.0
    run.status = "success" if feasible else "infeasible_partial"

    db.commit()
    db.refresh(run)
    return run
