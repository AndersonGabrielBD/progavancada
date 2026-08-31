import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getDashboard } from '../api/client'
import StatCard from '../components/StatCard'
import type { DashboardData } from '../types'

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => setError('Não foi possível carregar o dashboard. Verifique se a API está no ar.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-500">Carregando dashboard...</p>
  if (error) return <p className="text-red-600">{error}</p>
  if (!data) return null

  const floorChartData = data.by_floor.map((f) => ({
    andar: `${f.floor}º`,
    'Ocupadas': f.occupied_rooms,
    'Livres': f.rooms - f.occupied_rooms,
  }))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Dashboard Executivo</h2>
        <p className="text-sm text-slate-500">
          {data.run_id
            ? `Baseado na execução #${data.run_id} (${new Date(data.run_created_at!).toLocaleString('pt-BR')})`
            : 'Nenhuma alocação foi gerada ainda — os números refletem apenas o cadastro de salas e equipes.'}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Ocupação do prédio" value={`${data.utilization_pct}%`} hint="salas ocupadas / total" />
        <StatCard label="Salas ocupadas" value={data.rooms_occupied} tone="good" />
        <StatCard label="Salas disponíveis" value={data.rooms_available} />
        <StatCard label="Salas ociosas" value={data.rooms_idle} tone="warn" />
        <StatCard label="Funcionários alocados" value={data.allocated_people} tone="good" />
        <StatCard label="Equipes sem sala" value={data.unallocated_teams} tone={data.unallocated_teams > 0 ? 'bad' : 'good'} />
        <StatCard label="Capacidade total do prédio" value={data.total_capacity} />
        <StatCard
          label="Restrições violadas"
          value={data.violations}
          tone={data.violations > 0 ? 'bad' : 'good'}
        />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <h3 className="font-medium text-slate-800 mb-3">Ocupação por andar (salas)</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={floorChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="andar" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="Ocupadas" stackId="a" fill="#7c3aed" />
            <Bar dataKey="Livres" stackId="a" fill="#e2e8f0" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <h3 className="font-medium text-slate-800 p-4 pb-0">Mapa simplificado dos andares</h3>
        <table className="w-full text-sm mt-2">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Andar</th>
              <th className="text-left px-4 py-2">Salas</th>
              <th className="text-left px-4 py-2">Capacidade</th>
              <th className="text-left px-4 py-2">Ocupadas</th>
              <th className="text-left px-4 py-2">Pessoas alocadas</th>
              <th className="text-left px-4 py-2">Ocupação</th>
            </tr>
          </thead>
          <tbody>
            {data.by_floor
              .slice()
              .sort((a, b) => b.floor - a.floor)
              .map((f) => {
                const pct = f.rooms ? Math.round((f.occupied_rooms / f.rooms) * 100) : 0
                return (
                  <tr key={f.floor} className="border-t border-slate-100">
                    <td className="px-4 py-2 font-medium">{f.floor}º andar</td>
                    <td className="px-4 py-2">{f.rooms}</td>
                    <td className="px-4 py-2">{f.capacity}</td>
                    <td className="px-4 py-2">{f.occupied_rooms}</td>
                    <td className="px-4 py-2">{f.allocated_people}</td>
                    <td className="px-4 py-2">
                      <div className="w-32 h-2 bg-slate-100 rounded overflow-hidden">
                        <div className="h-full bg-purple-500" style={{ width: `${pct}%` }} />
                      </div>
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
