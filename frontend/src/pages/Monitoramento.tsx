import { useEffect, useState } from 'react'
import { getEngineMetrics } from '../api/client'
import StatCard from '../components/StatCard'
import type { EngineMetrics } from '../types'

export default function Monitoramento() {
  const [metrics, setMetrics] = useState<EngineMetrics | null>(null)

  useEffect(() => {
    getEngineMetrics().then(setMetrics)
  }, [])

  if (!metrics) return <p className="text-slate-500">Carregando indicadores...</p>

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Monitoramento do Motor de Alocação</h2>
        <p className="text-sm text-slate-500">
          Indicadores agregados de todas as execuções — permite acompanhar se o mecanismo de
          recomendação continua funcionando corretamente em produção.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Execuções totais" value={metrics.total_executions} />
        <StatCard label="Tempo da última otimização" value={metrics.last_solve_time_ms !== null ? `${metrics.last_solve_time_ms} ms` : '—'} />
        <StatCard label="Tempo médio de solve" value={metrics.avg_solve_time_ms !== null ? `${metrics.avg_solve_time_ms} ms` : '—'} />
        <StatCard label="Taxa de alocação média" value={metrics.avg_allocation_rate_pct !== null ? `${metrics.avg_allocation_rate_pct}%` : '—'} tone="good" />
        <StatCard label="Ocupação média" value={metrics.avg_occupancy_pct !== null ? `${metrics.avg_occupancy_pct}%` : '—'} />
        <StatCard
          label="Violações acumuladas"
          value={metrics.total_violations}
          tone={metrics.total_violations > 0 ? 'bad' : 'good'}
        />
        <StatCard label="Equipes não alocadas (acumulado)" value={metrics.total_unallocated_teams} tone="warn" />
        <StatCard label="Intervenções manuais" value={metrics.manual_interventions} />
        <StatCard label="Erros" value={metrics.errors} tone={metrics.errors > 0 ? 'bad' : 'good'} />
      </div>
    </div>
  )
}
