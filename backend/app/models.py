import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RoomType(str, enum.Enum):
    REUNIAO = "reuniao"
    TREINAMENTO = "treinamento"
    AUDITORIO = "auditorio"
    LABORATORIO = "laboratorio"
    PROJETO = "projeto"
    COLABORATIVO = "colaborativo"


class ConstraintType(str, enum.Enum):
    MIN_CAPACITY = "min_capacity"
    ALLOWED_FLOOR = "allowed_floor"
    REQUIRE_ACCESSIBILITY = "require_accessibility"
    REQUIRE_EQUIPMENT = "require_equipment"
    PROXIMITY = "proximity"          # duas equipes devem ficar em andares próximos
    EXCLUSION = "exclusion"          # dois setores não podem compartilhar andar
    RESERVED_ROOM = "reserved_room"  # sala reservada para um setor específico
    PRIORITY_BOOST = "priority_boost"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    type = Column(Enum(RoomType), nullable=False, default=RoomType.REUNIAO)
    resources = Column(JSON, default=list)          # ["projetor", "videoconferencia", ...]
    accessibility = Column(Boolean, default=False)
    available = Column(Boolean, default=True)
    reserved_for_sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)

    reserved_for_sector = relationship("Sector", foreign_keys=[reserved_for_sector_id])


class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    coordinator_name = Column(String(100), nullable=False)
    employee_count = Column(Integer, default=0)

    teams = relationship("Team", back_populates="sector", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
    name = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    schedule = Column(String(50), default="09:00-18:00")
    special_requirements = Column(JSON, default=list)   # ["projetor", "acessibilidade", ...]
    priority = Column(Integer, default=3)                # 1 (baixa) - 5 (crítica)
    preferred_floor = Column(Integer, nullable=True)
    needs_accessibility = Column(Boolean, default=False)

    sector = relationship("Sector", back_populates="teams")


class ConstraintRule(Base):
    __tablename__ = "constraint_rules"

    id = Column(Integer, primary_key=True)
    type = Column(Enum(ConstraintType), nullable=False)
    hard = Column(Boolean, default=True)   # hard = obrigatória / soft = preferência
    active = Column(Boolean, default=True)

    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team_id_b = Column(Integer, ForeignKey("teams.id"), nullable=True)  # usada em PROXIMITY/EXCLUSION
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    sector_id_b = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)

    payload = Column(JSON, default=dict)   # ex: {"floor": 5} ou {"equipment": "projetor"}
    description = Column(Text, nullable=True)


class AllocationRun(Base):
    __tablename__ = "allocation_runs"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = Column(String(100), default="coordenador-geral")
    algorithm_version = Column(String(50), default="allocation-engine-v1")

    teams_analyzed = Column(Integer, default=0)
    rooms_analyzed = Column(Integer, default=0)
    teams_allocated = Column(Integer, default=0)
    teams_unallocated = Column(Integer, default=0)
    violations = Column(Integer, default=0)
    occupancy_rate = Column(Float, default=0.0)
    solve_time_ms = Column(Float, default=0.0)
    status = Column(String(20), default="success")   # success | infeasible_partial | error
    error_message = Column(Text, nullable=True)

    assignments = relationship("AllocationAssignment", back_populates="run", cascade="all, delete-orphan")


class AllocationAssignment(Base):
    __tablename__ = "allocation_assignments"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("allocation_runs.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)   # null = não alocada

    occupancy_pct = Column(Float, nullable=True)
    alternatives_evaluated = Column(Integer, default=0)
    justification = Column(JSON, default=dict)      # objeto estruturado (constraints checadas, etc.)
    explanation_text = Column(Text, nullable=True)   # texto em linguagem natural (IA)

    reason_unallocated = Column(String(255), nullable=True)

    status = Column(String(20), default="recommended")  # recommended | accepted | rejected | overridden
    overridden_room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)

    run = relationship("AllocationRun", back_populates="assignments")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)   # ACCEPT | REJECT | MANUAL_OVERRIDE | RERUN | CREATE | UPDATE
    entity = Column(String(50), nullable=True)     # ex: "assignment", "room", "team"
    entity_id = Column(Integer, nullable=True)
    run_id = Column(Integer, ForeignKey("allocation_runs.id"), nullable=True)
    details = Column(JSON, default=dict)
