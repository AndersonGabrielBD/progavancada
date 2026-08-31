"""Critérios de aceitação #3, #4 e #5: justificativa em 100% das recomendações
aceitas, motivo registrado para toda equipe não alocada, e tempo de resposta
dentro do limite definido pela equipe (seção 14)."""
from app.engine.allocation_engine import run_allocation
from app.models import AllocationAssignment

SLA_MS = 5000  # limite definido pela equipe: 5s para até ~200 equipes/salas


def test_every_allocated_assignment_has_justification_and_explanation(db_session):
    run = run_allocation(db_session, user="test-engine")
    allocated = (
        db_session.query(AllocationAssignment)
        .filter(AllocationAssignment.run_id == run.id, AllocationAssignment.room_id.isnot(None))
        .all()
    )
    assert len(allocated) > 0
    for a in allocated:
        assert a.justification, f"Assignment {a.id} sem justificativa estruturada."
        assert a.explanation_text, f"Assignment {a.id} sem texto explicativo."
        assert "occupancy_pct" in a.justification
        assert "alternatives_evaluated" in a.justification


def test_every_unallocated_team_has_a_registered_reason(db_session):
    run = run_allocation(db_session, user="test-engine")
    unallocated = (
        db_session.query(AllocationAssignment)
        .filter(AllocationAssignment.run_id == run.id, AllocationAssignment.room_id.is_(None))
        .all()
    )
    # o cenário sintético inclui de propósito uma equipe de 160 pessoas (seção 11 do desafio)
    assert len(unallocated) >= 1
    for a in unallocated:
        assert a.reason_unallocated, f"Equipe {a.team_id} não alocada sem motivo registrado."


def test_solve_time_within_defined_sla(db_session):
    run = run_allocation(db_session, user="test-engine", time_limit_seconds=5.0)
    assert run.solve_time_ms <= SLA_MS


def test_run_registers_governance_fields(db_session):
    run = run_allocation(db_session, user="coordenador-geral")
    assert run.algorithm_version
    assert run.created_at is not None
    assert run.teams_analyzed > 0
    assert run.rooms_analyzed > 0
    assert run.status in ("success", "infeasible_partial")
