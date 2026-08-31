export interface Room {
  id: number
  code: string
  floor: number
  capacity: number
  type: string
  resources: string[]
  accessibility: boolean
  available: boolean
  reserved_for_sector_id: number | null
}

export interface Sector {
  id: number
  name: string
  coordinator_name: string
  employee_count: number
}

export interface Team {
  id: number
  sector_id: number
  name: string
  size: number
  schedule: string
  special_requirements: string[]
  priority: number
  preferred_floor: number | null
  needs_accessibility: boolean
}

export interface ConstraintRule {
  id: number
  type: string
  hard: boolean
  active: boolean
  team_id: number | null
  team_id_b: number | null
  sector_id: number | null
  sector_id_b: number | null
  room_id: number | null
  payload: Record<string, unknown>
  description: string | null
}

export interface AllocationAssignment {
  id: number
  team_id: number
  room_id: number | null
  occupancy_pct: number | null
  alternatives_evaluated: number
  justification: Record<string, unknown>
  explanation_text: string | null
  reason_unallocated: string | null
  status: string
  overridden_room_id: number | null
}

export interface AllocationRun {
  id: number
  created_at: string
  user: string
  algorithm_version: string
  teams_analyzed: number
  rooms_analyzed: number
  teams_allocated: number
  teams_unallocated: number
  violations: number
  occupancy_rate: number
  solve_time_ms: number
  status: string
  error_message: string | null
  assignments: AllocationAssignment[]
}

export interface DashboardData {
  run_id: number | null
  run_created_at: string | null
  total_rooms: number
  total_capacity: number
  rooms_available: number
  rooms_occupied: number
  rooms_idle: number
  utilization_pct: number
  total_teams: number
  total_employees_in_teams: number
  allocated_people: number
  unallocated_teams: number
  violations: number
  by_floor: {
    floor: number
    rooms: number
    capacity: number
    occupied_rooms: number
    allocated_people: number
  }[]
}

export interface EngineMetrics {
  total_executions: number
  last_solve_time_ms: number | null
  avg_solve_time_ms: number | null
  avg_allocation_rate_pct: number | null
  avg_occupancy_pct: number | null
  total_violations: number
  total_unallocated_teams: number
  manual_interventions: number
  errors: number
}

export interface ComparisonSide {
  teams_allocated: number
  teams_unallocated: number
  avg_occupancy_pct: number
  idle_seats: number
  violations: number
  rooms_used?: number
  rooms_idle?: number
}

export interface ComparisonData {
  before: ComparisonSide
  after: ComparisonSide | null
  run_id?: number
}

export interface AuditLogEntry {
  id: number
  created_at: string
  user: string
  action: string
  entity: string | null
  entity_id: number | null
  run_id: number | null
  details: Record<string, unknown>
}
