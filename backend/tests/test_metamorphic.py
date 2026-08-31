"""Testes metamórficos (seção 15 do desafio).

Para dezenas de equipes, salas e restrições não conhecemos de antemão a alocação
ótima — então, em vez de comparar contra um valor fixo, verificamos RELAÇÕES que
qualquer alocação correta deve respeitar quando o cenário é perturbado de forma
controlada.
"""
from app.database import SessionLocal, reset_db
from app.engine.allocation_engine import run_allocation
from app.models import ConstraintRule, Room, RoomType, Sector, Team
from app.seed import seed as seed_data


def _fresh_seeded_session():
    reset_db()
    db = SessionLocal()
    seed_data(db)
    return db


def test_adding_room_never_decreases_allocated_teams():
    """Teste 2 — Expansão da capacidade: adicionar uma sala nova, sem alterar mais
    nada, não deve reduzir a quantidade de equipes alocáveis."""
    db = _fresh_seeded_session()
    try:
        baseline = run_allocation(db, user="metamorphic-2")
        baseline_allocated = baseline.teams_allocated

        db.add(
            Room(
                code="EXTRA-900",
                floor=9,
                capacity=250,
                type=RoomType.AUDITORIO,
                resources=["projetor", "videoconferencia", "lousa_digital", "tv", "som"],
                accessibility=True,
                available=True,
            )
        )
        db.commit()

        after = run_allocation(db, user="metamorphic-2")
        assert after.teams_allocated >= baseline_allocated, (
            "Adicionar uma sala não pode reduzir o número de equipes alocadas."
        )
    finally:
        db.close()


def test_removing_hard_constraint_never_decreases_allocated_teams():
    """Teste 3 — Remoção de restrição: se uma restrição obrigatória é desativada,
    o espaço de soluções só pode crescer (ou permanecer igual) — nunca diminuir."""
    db = _fresh_seeded_session()
    try:
        baseline = run_allocation(db, user="metamorphic-3")
        baseline_allocated = baseline.teams_allocated

        db.query(ConstraintRule).filter(ConstraintRule.hard == True).update({"active": False})  # noqa: E712
        db.commit()

        after = run_allocation(db, user="metamorphic-3")
        assert after.teams_allocated >= baseline_allocated, (
            "Remover uma restrição obrigatória não pode reduzir o número de equipes alocadas."
        )
    finally:
        db.close()


def test_equivalent_teams_symmetry():
    """Teste 4 — Equipes equivalentes: duas equipes com exatamente os mesmos
    requisitos, apenas com os nomes trocados entre execuções, não devem produzir
    uma diferença relevante na qualidade global da solução (ocupação média)."""
    db = _fresh_seeded_session()
    try:
        sector = db.query(Sector).first()
        team_x = Team(sector_id=sector.id, name="Equipe Espelho X", size=14, priority=3)
        team_y = Team(sector_id=sector.id, name="Equipe Espelho Y", size=14, priority=3)
        db.add_all([team_x, team_y])
        db.commit()

        run1 = run_allocation(db, user="metamorphic-4")
        occupancy_before = run1.occupancy_rate

        team_x.name, team_y.name = team_y.name, team_x.name
        db.commit()

        run2 = run_allocation(db, user="metamorphic-4")
        occupancy_after = run2.occupancy_rate

        assert abs(occupancy_before - occupancy_after) < 2.0, (
            "Trocar os nomes de duas equipes equivalentes não deveria alterar "
            "significativamente a ocupação média da solução."
        )
    finally:
        db.close()
