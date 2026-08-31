"""Filtra, para cada equipe, o conjunto de salas candidatas e explica por que uma
sala foi descartada. Isso é o que permite ao motor apontar a CAUSA RAIZ de uma
equipe não alocável (seção 11 do desafio), em vez de simplesmente dizer "sem sala".
"""
from dataclasses import dataclass, field

from app.models import ConstraintRule, ConstraintType, Room, Team


@dataclass
class CandidateResult:
    rooms: list[Room]
    elimination_stage: str | None = None   # None se rooms não está vazio
    elimination_detail: str | None = None
    stage_counts: dict[str, int] = field(default_factory=dict)


def _team_hard_rules(team: Team, rules: list[ConstraintRule]) -> list[ConstraintRule]:
    return [
        r
        for r in rules
        if r.active
        and r.hard
        and (r.team_id == team.id or r.sector_id == team.sector_id)
        and r.type in (ConstraintType.ALLOWED_FLOOR, ConstraintType.REQUIRE_ACCESSIBILITY, ConstraintType.REQUIRE_EQUIPMENT)
    ]


def build_candidates(team: Team, rooms: list[Room], rules: list[ConstraintRule]) -> CandidateResult:
    stage_counts: dict[str, int] = {}

    pool = [r for r in rooms if r.available]
    stage_counts["disponiveis"] = len(pool)

    pool = [r for r in pool if r.capacity >= team.size]
    stage_counts["capacidade_suficiente"] = len(pool)
    if not pool:
        return CandidateResult([], "capacidade", f"Nenhuma sala com capacidade >= {team.size} pessoas.", stage_counts)

    hard_rules = _team_hard_rules(team, rules)

    if team.needs_accessibility:
        pool2 = [r for r in pool if r.accessibility]
        stage_counts["acessibilidade"] = len(pool2)
        if not pool2:
            return CandidateResult([], "acessibilidade", "Equipe exige acessibilidade e nenhuma sala compatível restou.", stage_counts)
        pool = pool2

    for rule in hard_rules:
        if rule.type == ConstraintType.REQUIRE_ACCESSIBILITY:
            pool2 = [r for r in pool if r.accessibility]
            stage_counts["acessibilidade_restricao"] = len(pool2)
            if not pool2:
                return CandidateResult([], "acessibilidade", rule.description or "Restrição de acessibilidade não atendida.", stage_counts)
            pool = pool2

        elif rule.type == ConstraintType.REQUIRE_EQUIPMENT:
            equip = rule.payload.get("equipment")
            if equip:
                pool2 = [r for r in pool if equip in (r.resources or [])]
                stage_counts[f"equipamento_{equip}"] = len(pool2)
                if not pool2:
                    return CandidateResult([], "equipamento", rule.description or f"Nenhuma sala possui o equipamento obrigatório '{equip}'.", stage_counts)
                pool = pool2

        elif rule.type == ConstraintType.ALLOWED_FLOOR:
            floors = rule.payload.get("floors") or ([rule.payload["floor"]] if "floor" in rule.payload else [])
            if floors:
                pool2 = [r for r in pool if r.floor in floors]
                stage_counts["andar_permitido"] = len(pool2)
                if not pool2:
                    return CandidateResult([], "andar", rule.description or f"Nenhuma sala nos andares permitidos {floors}.", stage_counts)
                pool = pool2

    if team.special_requirements:
        pool2 = [r for r in pool if set(team.special_requirements).issubset(set(r.resources or []))]
        stage_counts["recursos_solicitados"] = len(pool2)
        if not pool2:
            return CandidateResult(
                [],
                "recursos",
                f"Nenhuma sala possui todos os recursos solicitados: {team.special_requirements}.",
                stage_counts,
            )
        pool = pool2

    reserved_pool = [r for r in pool if r.reserved_for_sector_id in (None, team.sector_id)]
    stage_counts["reserva"] = len(reserved_pool)
    if not reserved_pool:
        return CandidateResult([], "reserva", "As salas restantes estão reservadas para outro setor.", stage_counts)
    pool = reserved_pool

    return CandidateResult(pool, None, None, stage_counts)
