from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class RoomBase(BaseModel):
    code: str
    floor: int
    capacity: int
    type: str = "reuniao"
    resources: list[str] = []
    accessibility: bool = False
    available: bool = True
    reserved_for_sector_id: Optional[int] = None


class RoomCreate(RoomBase):
    pass


class RoomOut(RoomBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SectorBase(BaseModel):
    name: str
    coordinator_name: str
    employee_count: int = 0


class SectorCreate(SectorBase):
    pass


class SectorOut(SectorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TeamBase(BaseModel):
    sector_id: int
    name: str
    size: int
    schedule: str = "09:00-18:00"
    special_requirements: list[str] = []
    priority: int = 3
    preferred_floor: Optional[int] = None
    needs_accessibility: bool = False


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    size: Optional[int] = None
    schedule: Optional[str] = None
    special_requirements: Optional[list[str]] = None
    priority: Optional[int] = None
    preferred_floor: Optional[int] = None
    needs_accessibility: Optional[bool] = None


class TeamOut(TeamBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ConstraintBase(BaseModel):
    type: str
    hard: bool = True
    active: bool = True
    team_id: Optional[int] = None
    team_id_b: Optional[int] = None
    sector_id: Optional[int] = None
    sector_id_b: Optional[int] = None
    room_id: Optional[int] = None
    payload: dict[str, Any] = {}
    description: Optional[str] = None


class ConstraintCreate(ConstraintBase):
    pass


class ConstraintOut(ConstraintBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    team_id: int
    room_id: Optional[int]
    occupancy_pct: Optional[float]
    alternatives_evaluated: int
    justification: dict[str, Any]
    explanation_text: Optional[str]
    reason_unallocated: Optional[str]
    status: str
    overridden_room_id: Optional[int]


class AllocationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    user: str
    algorithm_version: str
    teams_analyzed: int
    rooms_analyzed: int
    teams_allocated: int
    teams_unallocated: int
    violations: int
    occupancy_rate: float
    solve_time_ms: float
    status: str
    error_message: Optional[str]
    assignments: list[AssignmentOut] = []


class OverrideRequest(BaseModel):
    assignment_id: int
    new_room_id: Optional[int] = None
    action: str  # "ACCEPT" | "REJECT" | "MANUAL_OVERRIDE"
    user: str = "coordenador-geral"
    reason: Optional[str] = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    user: str
    action: str
    entity: Optional[str]
    entity_id: Optional[int]
    run_id: Optional[int]
    details: dict[str, Any]


class GenerateAllocationRequest(BaseModel):
    user: str = "coordenador-geral"
    time_limit_seconds: float = 5.0
