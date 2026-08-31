"""Gera dados sintéticos para o protótipo: 9 andares, ~90 salas, 8 setores e ~60 equipes.

Determinístico (sem random puro) para que o mesmo seed produza sempre o mesmo cenário,
o que facilita reproduzir bugs e comparar execuções (governança).
"""
import random

from sqlalchemy.orm import Session

from app.database import SessionLocal, reset_db
from app.models import ConstraintRule, ConstraintType, Room, RoomType, Sector, Team

RNG_SEED = 42

SECTORS = [
    ("Tecnologia", "Mariana Alves"),
    ("Recursos Humanos", "Carlos Souza"),
    ("Financeiro", "Beatriz Lima"),
    ("Jurídico", "Rafael Nogueira"),
    ("Marketing", "Julia Ferreira"),
    ("Comercial", "Eduardo Rocha"),
    ("Operações", "Patricia Gomes"),
    ("Pesquisa e Desenvolvimento", "Thiago Martins"),
]

ROOM_TYPES_BY_FLOOR = {
    1: RoomType.AUDITORIO,
    2: RoomType.TREINAMENTO,
    3: RoomType.COLABORATIVO,
    4: RoomType.REUNIAO,
    5: RoomType.REUNIAO,
    6: RoomType.PROJETO,
    7: RoomType.REUNIAO,
    8: RoomType.LABORATORIO,
    9: RoomType.PROJETO,
}

RESOURCE_POOL = ["projetor", "videoconferencia", "lousa_digital", "tv", "som"]


def _rooms_for_floor(floor: int, rng: random.Random) -> list[dict]:
    rooms = []
    n_rooms = 12 if floor != 1 else 4  # térreo tem menos salas (mais espaços grandes)
    base_type = ROOM_TYPES_BY_FLOOR[floor]
    for i in range(1, n_rooms + 1):
        code = f"{floor}{i:02d}"
        if floor == 1:
            capacity = rng.choice([80, 100, 120, 150])
        else:
            capacity = rng.choice([8, 10, 15, 20, 25, 30, 40, 45, 60])
        resources = rng.sample(RESOURCE_POOL, k=rng.randint(1, 3))
        rooms.append(
            dict(
                code=code,
                floor=floor,
                capacity=capacity,
                type=base_type,
                resources=resources,
                accessibility=rng.random() > 0.3,
                available=True,
            )
        )
    return rooms


def _teams_for_sector(sector_name: str, sector_id: int, rng: random.Random) -> list[dict]:
    n_teams = rng.randint(5, 9)
    teams = []
    for i in range(1, n_teams + 1):
        size = rng.choice([4, 6, 8, 10, 12, 15, 18, 22, 28, 35, 42, 54])
        needs_access = rng.random() > 0.75
        reqs = rng.sample(RESOURCE_POOL, k=rng.randint(0, 2))
        teams.append(
            dict(
                sector_id=sector_id,
                name=f"{sector_name} - Equipe {chr(64 + i)}",
                size=size,
                schedule=rng.choice(["09:00-18:00", "08:00-17:00", "13:00-22:00"]),
                special_requirements=reqs,
                priority=rng.randint(1, 5),
                preferred_floor=rng.choice([None, None, rng.randint(2, 9)]),
                needs_accessibility=needs_access,
            )
        )
    return teams


def seed(db: Session | None = None, add_hard_case: bool = True) -> None:
    own_session = db is None
    if own_session:
        reset_db()
        db = SessionLocal()

    rng = random.Random(RNG_SEED)

    try:
        sector_objs = []
        for name, coordinator in SECTORS:
            sector = Sector(name=name, coordinator_name=coordinator, employee_count=0)
            db.add(sector)
            sector_objs.append(sector)
        db.flush()

        for floor in range(1, 10):
            for room_data in _rooms_for_floor(floor, rng):
                db.add(Room(**room_data))

        total_employees = 0
        for sector in sector_objs:
            teams_data = _teams_for_sector(sector.name, sector.id, rng)
            sector_size = sum(t["size"] for t in teams_data)
            sector.employee_count = sector_size
            total_employees += sector_size
            for team_data in teams_data:
                db.add(Team(**team_data))
        db.flush()

        if add_hard_case:
            # Equipe intencionalmente maior que qualquer sala disponível fora do térreo,
            # para demonstrar o tratamento de exceções (seção 11 do desafio).
            oversized_sector = sector_objs[0]
            oversized_team = Team(
                sector_id=oversized_sector.id,
                name=f"{oversized_sector.name} - Equipe Delta (piloto)",
                size=160,  # maior que a maior sala do prédio (capacidade máxima: 150)
                schedule="09:00-18:00",
                special_requirements=[],
                priority=4,
                preferred_floor=7,
                needs_accessibility=False,
            )
            db.add(oversized_team)
            oversized_sector.employee_count += 160

        db.flush()

        rh_team = db.query(Team).filter(Team.name.like("Recursos Humanos%")).first()
        juridico_team = db.query(Team).filter(Team.name.like("Jurídico%")).first()
        if rh_team and juridico_team:
            db.add(
                ConstraintRule(
                    type=ConstraintType.EXCLUSION,
                    hard=True,
                    active=True,
                    sector_id=rh_team.sector_id,
                    sector_id_b=juridico_team.sector_id,
                    payload={"reason": "dados sensíveis não podem compartilhar andar"},
                    description="RH e Jurídico não podem compartilhar o mesmo andar",
                )
            )

        tech_teams = db.query(Team).join(Sector).filter(Sector.name == "Tecnologia").limit(2).all()
        if len(tech_teams) == 2:
            db.add(
                ConstraintRule(
                    type=ConstraintType.PROXIMITY,
                    hard=False,
                    active=True,
                    team_id=tech_teams[0].id,
                    team_id_b=tech_teams[1].id,
                    payload={"max_floor_distance": 1},
                    description=f"{tech_teams[0].name} e {tech_teams[1].name} devem ficar em andares próximos",
                )
            )

        rd_first_team = db.query(Team).join(Sector).filter(Sector.name == "Pesquisa e Desenvolvimento").first()
        if rd_first_team:
            db.add(
                ConstraintRule(
                    type=ConstraintType.REQUIRE_ACCESSIBILITY,
                    hard=True,
                    active=True,
                    team_id=rd_first_team.id,
                    payload={},
                    description=f"{rd_first_team.name} exige sala acessível",
                )
            )

        db.commit()
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    seed()
    print("Base de dados semeada com sucesso.")
