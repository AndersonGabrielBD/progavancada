import { useEffect, useState } from 'react'
import { generateAllocation, listRooms, listRuns, listTeams, overrideAssignment } from '../api/client'
import type { AllocationAssignment, AllocationRun, Room, Team } from '../types'

export default function Alocacao() {
  const [run, setRun] = useState<AllocationRun | null>(null)
  const [teams, setTeams] = useState<Team[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<AllocationAssignment | null>(null)
  const [overrideTarget, setOverrideTarget] = useState<number | null>(null)

  const teamsById = Object.fromEntries(teams.map((t) => [t.id, t]))
  const roomsById = Object.fromEntries(rooms.map((r) => [r.id, r]))

  const loadLastRun = async () => {
    const runs = await listRuns()
    if (runs.length > 0) setRun(runs[0])
  }

  useEffect(() => {
    listTeams().then(setTeams)
    listRooms().then(setRooms)
    loadLastRun()
  }, [])

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const newRun = await generateAllocation('coordenador-geral')
      setRun(newRun)
      setSelected(null)
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (assignment: AllocationAssignment, action: 'ACCEPT' | 'REJECT' | 'MANUAL_OVERRIDE', newRoomId?: number) => {
    await overrideAssignment({
      assignment_id: assignment.id,
      action,
      new_room_id: newRoomId,
      user: 'coordenador-geral',
      reason: action === 'MANUAL_OVERRIDE' ? 'Ajuste manual pelo Coordenador Geral' : undefined,
    })
    if (run) {
      const refreshed = await listRuns()
      setRun(refreshed.find((r) => r.id === run.id) ?? refreshed[0])
    }
    setOverrideTarget(null)
  }

  const allocated = run?.assignments.filter((a) => a.room_id !== null) ?? []
  const exceptions = run?.assignments.filter((a) => a.room_id === null) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Gerar Alocação Otimizada</h2>
          <p className="text-sm text-slate-500">
            Motor de otimização por restrições (OR-Tools CP-SAT) — considera capacidade, restrições
            obrigatórias, prioridade, proximidade e ociosidade.
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-lg"
        >
          {loading ? 'Gerando...' : 'GERAR ALOCAÇÃO OTIMIZADA'}
        </button>
      </div>

      {run && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
          <SummaryPill label="Execução" value={`#${run.id}`} />
          <SummaryPill label="Equipes alocadas" value={`${run.teams_allocated}/${run.teams_analyzed}`} />
          <SummaryPill label="Ocupação média" value={`${run.occupancy_rate}%`} />
          <SummaryPill label="Violações" value={run.violations} tone={run.violations > 0 ? 'bad' : 'good'} />
          <SummaryPill label="Tempo de solve" value={`${run.solve_time_ms} ms`} />
        </div>
      )}

      {!run && <p className="text-slate-500">Nenhuma execução ainda. Clique em "Gerar Alocação Otimizada".</p>}

      {run && (
        <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-2">Equipe</th>
                <th className="text-left px-4 py-2">Setor</th>
                <th className="text-left px-4 py-2">Pessoas</th>
                <th className="text-left px-4 py-2">Sala sugerida</th>
                <th className="text-left px-4 py-2">Capacidade</th>
                <th className="text-left px-4 py-2">Andar</th>
                <th className="text-left px-4 py-2">Ocupação</th>
                <th className="text-left px-4 py-2">Status</th>
                <th className="text-left px-4 py-2">Ações</th>
              </tr>
            </thead>
            <tbody>
              {allocated.map((a) => {
                const team = teamsById[a.team_id]
                const roomId = a.overridden_room_id ?? a.room_id!
                const room = roomsById[roomId]
                return (
                  <tr key={a.id} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-2 font-medium">{team?.name ?? a.team_id}</td>
                    <td className="px-4 py-2 text-slate-500">{team?.sector_id}</td>
                    <td className="px-4 py-2">{team?.size}</td>
                    <td className="px-4 py-2">
                      {room?.code}
                      {a.overridden_room_id && <span className="ml-1 text-xs text-amber-600">(sobrescrita)</span>}
                    </td>
                    <td className="px-4 py-2">{room?.capacity}</td>
                    <td className="px-4 py-2">{room?.floor}º</td>
                    <td className="px-4 py-2">{a.occupancy_pct}%</td>
                    <td className="px-4 py-2">
                      <StatusBadge status={a.status} />
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex gap-1 flex-wrap">
                        <button className="text-xs text-purple-600 hover:underline" onClick={() => setSelected(a)}>
                          Ver justificativa
                        </button>
                        <button className="text-xs text-emerald-600 hover:underline" onClick={() => handleAction(a, 'ACCEPT')}>
                          Aceitar
                        </button>
                        <button className="text-xs text-red-600 hover:underline" onClick={() => handleAction(a, 'REJECT')}>
                          Rejeitar
                        </button>
                        <button className="text-xs text-slate-600 hover:underline" onClick={() => setOverrideTarget(a.id)}>
                          Alterar sala
                        </button>
                      </div>
                      {overrideTarget === a.id && (
                        <select
                          autoFocus
                          className="mt-1 border rounded text-xs px-1 py-1"
                          onChange={(e) => handleAction(a, 'MANUAL_OVERRIDE', Number(e.target.value))}
                          defaultValue=""
                        >
                          <option value="" disabled>
                            Escolher sala...
                          </option>
                          {rooms
                            .filter((r) => r.available)
                            .map((r) => (
                              <option key={r.id} value={r.id}>
                                {r.code} ({r.capacity} lugares, {r.floor}º)
                              </option>
                            ))}
                        </select>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-lg max-w-lg w-full p-6 space-y-3" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-900">Por que esta sala foi recomendada?</h3>
            <p className="text-sm text-slate-700 leading-relaxed">{selected.explanation_text}</p>
            <div className="bg-slate-50 rounded p-3 text-xs font-mono whitespace-pre-wrap text-slate-600">
              {JSON.stringify(selected.justification, null, 2)}
            </div>
            <button
              className="text-sm text-purple-600 hover:underline"
              onClick={() => setSelected(null)}
            >
              Fechar
            </button>
          </div>
        </div>
      )}

      {run && exceptions.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="font-medium text-red-800 mb-2">
            ⚠ Alertas — {exceptions.length} equipe(s) não puderam ser alocadas
          </h3>
          <table className="w-full text-sm">
            <thead className="text-red-700 text-xs uppercase">
              <tr>
                <th className="text-left py-1">Equipe</th>
                <th className="text-left py-1">Pessoas</th>
                <th className="text-left py-1">Motivo / causa raiz</th>
              </tr>
            </thead>
            <tbody>
              {exceptions.map((a) => {
                const team = teamsById[a.team_id]
                return (
                  <tr key={a.id} className="border-t border-red-100">
                    <td className="py-2 font-medium">{team?.name ?? a.team_id}</td>
                    <td className="py-2">{team?.size}</td>
                    <td className="py-2">{a.reason_unallocated}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function SummaryPill({ label, value, tone }: { label: string; value: string | number; tone?: 'good' | 'bad' }) {
  const toneClass = tone === 'bad' ? 'text-red-600' : tone === 'good' ? 'text-emerald-600' : 'text-slate-900'
  return (
    <div className="bg-white border border-slate-200 rounded-lg px-3 py-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`font-semibold ${toneClass}`}>{value}</div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    recommended: 'bg-blue-100 text-blue-700',
    accepted: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-red-100 text-red-700',
    overridden: 'bg-amber-100 text-amber-700',
  }
  const labelMap: Record<string, string> = {
    recommended: 'Sugerida',
    accepted: 'Aceita',
    rejected: 'Rejeitada',
    overridden: 'Sobrescrita',
  }
  return <span className={`text-xs px-2 py-0.5 rounded-full ${map[status] ?? 'bg-slate-100'}`}>{labelMap[status] ?? status}</span>
}
