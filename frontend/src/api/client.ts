import axios from 'axios'
import type {
  AllocationRun,
  AuditLogEntry,
  ComparisonData,
  ConstraintRule,
  DashboardData,
  EngineMetrics,
  Room,
  Sector,
  Team,
} from '../types'

const api = axios.create({ baseURL: '/api' })

export const listRooms = () => api.get<Room[]>('/rooms').then((r) => r.data)
export const createRoom = (payload: Partial<Room>) => api.post<Room>('/rooms', payload).then((r) => r.data)

export const listSectors = () => api.get<Sector[]>('/sectors').then((r) => r.data)
export const createSector = (payload: Partial<Sector>) => api.post<Sector>('/sectors', payload).then((r) => r.data)

export const listTeams = (sectorId?: number) =>
  api.get<Team[]>('/teams', { params: sectorId ? { sector_id: sectorId } : {} }).then((r) => r.data)
export const createTeam = (payload: Partial<Team>) => api.post<Team>('/teams', payload).then((r) => r.data)
export const updateTeam = (id: number, payload: Partial<Team>) =>
  api.put<Team>(`/teams/${id}`, payload).then((r) => r.data)
export const deleteTeam = (id: number) => api.delete(`/teams/${id}`)

export const listConstraints = () => api.get<ConstraintRule[]>('/constraints').then((r) => r.data)
export const createConstraint = (payload: Partial<ConstraintRule>) =>
  api.post<ConstraintRule>('/constraints', payload).then((r) => r.data)
export const deleteConstraint = (id: number) => api.delete(`/constraints/${id}`)
export const toggleConstraint = (id: number) =>
  api.patch<ConstraintRule>(`/constraints/${id}/toggle`).then((r) => r.data)

export const generateAllocation = (user: string) =>
  api.post<AllocationRun>('/allocation/generate', { user }).then((r) => r.data)
export const listRuns = () => api.get<AllocationRun[]>('/allocation/runs').then((r) => r.data)
export const getRun = (id: number) => api.get<AllocationRun>(`/allocation/runs/${id}`).then((r) => r.data)
export const overrideAssignment = (payload: {
  assignment_id: number
  action: 'ACCEPT' | 'REJECT' | 'MANUAL_OVERRIDE'
  new_room_id?: number
  user: string
  reason?: string
}) => api.post('/allocation/override', payload).then((r) => r.data)

export const getDashboard = (runId?: number) =>
  api.get<DashboardData>('/metrics/dashboard', { params: runId ? { run_id: runId } : {} }).then((r) => r.data)
export const getEngineMetrics = () => api.get<EngineMetrics>('/metrics/engine').then((r) => r.data)
export const getComparison = (runId?: number) =>
  api.get<ComparisonData>('/metrics/comparison', { params: runId ? { run_id: runId } : {} }).then((r) => r.data)

export const listAuditLogs = (runId?: number) =>
  api.get<AuditLogEntry[]>('/audit', { params: runId ? { run_id: runId } : {} }).then((r) => r.data)

export default api
