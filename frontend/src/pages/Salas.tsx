import { useEffect, useState } from 'react'
import { createRoom, listRooms, listSectors } from '../api/client'
import type { Room, Sector } from '../types'

const ROOM_TYPES = ['reuniao', 'treinamento', 'auditorio', 'laboratorio', 'projeto', 'colaborativo']

const emptyForm = {
  code: '',
  floor: 1,
  capacity: 10,
  type: 'reuniao',
  resources: '',
  accessibility: false,
  reserved_for_sector_id: '',
}

export default function Salas() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [sectors, setSectors] = useState<Sector[]>([])
  const [form, setForm] = useState(emptyForm)
  const [floorFilter, setFloorFilter] = useState<number | null>(null)

  const reload = () => {
    listRooms().then(setRooms)
    listSectors().then(setSectors)
  }

  useEffect(reload, [])

  const sectorsById = Object.fromEntries(sectors.map((s) => [s.id, s.name]))

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    await createRoom({
      code: form.code,
      floor: Number(form.floor),
      capacity: Number(form.capacity),
      type: form.type,
      resources: form.resources ? form.resources.split(',').map((r) => r.trim()) : [],
      accessibility: form.accessibility,
      available: true,
      reserved_for_sector_id: form.reserved_for_sector_id ? Number(form.reserved_for_sector_id) : null,
    })
    setForm(emptyForm)
    reload()
  }

  const visibleRooms = floorFilter ? rooms.filter((r) => r.floor === floorFilter) : rooms

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Salas do Prédio</h2>
        <p className="text-sm text-slate-500">Visão do Coordenador Geral — cadastro e características dos espaços.</p>
      </div>

      <form onSubmit={handleCreate} className="bg-white border border-slate-200 rounded-lg p-4 grid md:grid-cols-4 gap-3">
        <input
          required
          placeholder="Código (ex: 705)"
          className="border rounded px-2 py-1.5 text-sm"
          value={form.code}
          onChange={(e) => setForm({ ...form, code: e.target.value })}
        />
        <input
          type="number"
          min={1}
          max={9}
          required
          placeholder="Andar"
          className="border rounded px-2 py-1.5 text-sm"
          value={form.floor}
          onChange={(e) => setForm({ ...form, floor: Number(e.target.value) })}
        />
        <input
          type="number"
          min={1}
          required
          placeholder="Capacidade"
          className="border rounded px-2 py-1.5 text-sm"
          value={form.capacity}
          onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })}
        />
        <select className="border rounded px-2 py-1.5 text-sm" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
          {ROOM_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <input
          placeholder="Recursos (separados por vírgula)"
          className="border rounded px-2 py-1.5 text-sm md:col-span-2"
          value={form.resources}
          onChange={(e) => setForm({ ...form, resources: e.target.value })}
        />
        <select
          className="border rounded px-2 py-1.5 text-sm"
          value={form.reserved_for_sector_id}
          onChange={(e) => setForm({ ...form, reserved_for_sector_id: e.target.value })}
        >
          <option value="">Sem reserva de setor</option>
          {sectors.map((s) => (
            <option key={s.id} value={s.id}>
              Reservada: {s.name}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.accessibility} onChange={(e) => setForm({ ...form, accessibility: e.target.checked })} />
          Acessível
        </label>
        <button className="bg-purple-600 text-white text-sm px-4 py-2 rounded md:col-span-4">Cadastrar sala</button>
      </form>

      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFloorFilter(null)}
          className={`text-xs px-3 py-1 rounded-full border ${!floorFilter ? 'bg-purple-600 text-white border-purple-600' : 'border-slate-300 text-slate-600'}`}
        >
          Todos
        </button>
        {Array.from({ length: 9 }, (_, i) => i + 1).map((f) => (
          <button
            key={f}
            onClick={() => setFloorFilter(f)}
            className={`text-xs px-3 py-1 rounded-full border ${floorFilter === f ? 'bg-purple-600 text-white border-purple-600' : 'border-slate-300 text-slate-600'}`}
          >
            {f}º andar
          </button>
        ))}
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Código</th>
              <th className="text-left px-4 py-2">Andar</th>
              <th className="text-left px-4 py-2">Capacidade</th>
              <th className="text-left px-4 py-2">Tipo</th>
              <th className="text-left px-4 py-2">Recursos</th>
              <th className="text-left px-4 py-2">Acessível</th>
              <th className="text-left px-4 py-2">Reservada</th>
              <th className="text-left px-4 py-2">Disponível</th>
            </tr>
          </thead>
          <tbody>
            {visibleRooms.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-medium">{r.code}</td>
                <td className="px-4 py-2">{r.floor}º</td>
                <td className="px-4 py-2">{r.capacity}</td>
                <td className="px-4 py-2">{r.type}</td>
                <td className="px-4 py-2 text-slate-500">{r.resources.join(', ') || '—'}</td>
                <td className="px-4 py-2">{r.accessibility ? 'Sim' : 'Não'}</td>
                <td className="px-4 py-2">{r.reserved_for_sector_id ? sectorsById[r.reserved_for_sector_id] : '—'}</td>
                <td className="px-4 py-2">{r.available ? 'Sim' : 'Não'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
