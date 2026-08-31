import { useEffect, useState } from 'react'
import { getComparison } from '../api/client'
import type { ComparisonData } from '../types'

export default function Comparacao() {
  const [data, setData] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getComparison()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-500">Carregando comparação...</p>
  if (!data || !data.after) {
    return <p className="text-slate-500">Gere uma alocação primeiro para ver a comparação Antes/Depois.</p>
  }

  const rows = [
    {
      label: 'Equipes alocadas',
      before: data.before.teams_allocated,
      after: data.after.teams_allocated,
      better: 'higher',
    },
    {
      label: 'Equipes sem sala',
      before: data.before.teams_unallocated,
      after: data.after.teams_unallocated,
      better: 'lower',
    },
    {
      label: 'Ocupação média',
      before: `${data.before.avg_occupancy_pct}%`,
      after: `${data.after.avg_occupancy_pct}%`,
      better: 'higher',
    },
    {
      label: 'Assentos ociosos',
      before: data.before.idle_seats,
      after: data.after.idle_seats,
      better: 'lower',
    },
    {
      label: 'Violações',
      before: data.before.violations,
      after: data.after.violations,
      better: 'lower',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Situação Inicial vs. Situação Otimizada</h2>
        <p className="text-sm text-slate-500">
          "Antes" simula o processo manual (primeira sala compatível encontrada, sem otimização).
          "Depois" é a recomendação da execução #{data.run_id} do motor de alocação.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3">Indicador</th>
              <th className="text-left px-4 py-3">Antes (manual)</th>
              <th className="text-left px-4 py-3">Depois (otimizado)</th>
              <th className="text-left px-4 py-3">Resultado</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const improved =
                row.better === 'higher' ? Number(row.after) >= Number(row.before) : Number(row.after) <= Number(row.before)
              return (
                <tr key={row.label} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium">{row.label}</td>
                  <td className="px-4 py-3 text-slate-500">{row.before}</td>
                  <td className="px-4 py-3 font-semibold">{row.after}</td>
                  <td className="px-4 py-3">
                    <span className={improved ? 'text-emerald-600' : 'text-red-600'}>
                      {improved ? '▲ Melhorou' : '▼ Piorou'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
