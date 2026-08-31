"""Critério de aceitação #1: nenhuma sala pode receber mais pessoas que sua capacidade.

Teste 1 do desafio (seção 15) — propriedade de capacidade, verificada tanto no
cenário sintético principal quanto em cenários pequenos gerados aleatoriamente
(teste baseado em propriedades / hypothesis), já que não sabemos de antemão qual
é a alocação ótima para dezenas de equipes e salas.
"""
import random

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.database import SessionLocal, reset_db
from app.engine.allocation_engine import run_allocation
from app.models import AllocationAssignment, Room, Sector, Team


def test_no_assignment_exceeds_room_capacity_on_seeded_scenario(db_session):
    run = run_allocation(db_session, user="test-capacity")

    assignments = (
        db_session.query(AllocationAssignment).filter(AllocationAssignment.run_id == run.id).all()
    )
    rooms_by_id = {r.id: r for r in db_session.query(Room).all()}
    teams_by_id = {t.id: t for t in db_session.query(Team).all()}

    checked = 0
    for a in assignments:
        if a.room_id is not None:
            room = rooms_by_id[a.room_id]
            team = teams_by_id[a.team_id]
            assert team.size <= room.capacity, (
                f"Equipe {team.name} ({team.size} pessoas) alocada na sala {room.code} "
                f"(capacidade {room.capacity}) — violação de capacidade."
            )
            checked += 1

    assert checked > 0, "Nenhuma alocação foi produzida; o teste não teve o que verificar."
    assert run.violations == 0


@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed_value=st.integers(min_value=0, max_value=10_000))
def test_capacity_property_holds_on_random_small_scenarios(seed_value):
    reset_db()
    db = SessionLocal()
    try:
        rng = random.Random(seed_value)
        sector = Sector(name=f"Setor-{seed_value}", coordinator_name="Coord Teste", employee_count=0)
        db.add(sector)
        db.flush()

        for i in range(rng.randint(3, 10)):
            db.add(
                Room(
                    code=f"R{seed_value}-{i}",
                    floor=rng.randint(1, 9),
                    capacity=rng.randint(5, 100),
                    resources=[],
                    accessibility=rng.random() > 0.5,
                    available=True,
                )
            )
        for i in range(rng.randint(3, 10)):
            db.add(
                Team(
                    sector_id=sector.id,
                    name=f"Equipe-{seed_value}-{i}",
                    size=rng.randint(1, 120),
                    priority=rng.randint(1, 5),
                )
            )
        db.commit()

        run = run_allocation(db, user="hypothesis")
        assignments = (
            db.query(AllocationAssignment).filter(AllocationAssignment.run_id == run.id).all()
        )
        rooms_by_id = {r.id: r for r in db.query(Room).all()}
        teams_by_id = {t.id: t for t in db.query(Team).all()}

        for a in assignments:
            if a.room_id is not None:
                assert teams_by_id[a.team_id].size <= rooms_by_id[a.room_id].capacity
        assert run.violations == 0
    finally:
        db.close()
