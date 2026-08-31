import { useEffect, useState } from 'react'
import {
  createConstraint,
  createTeam,
  deleteConstraint,
  listConstraints,
  listSectors,
  listTeams,
  toggleConstraint,
} from '../api/client'
import type { ConstraintRule, Sector, Team } from '../types'

const CONSTRAINT_TYPES = [
  { value: 'allowed_floor', label: 'Andar permitido (restringe a equipe a andar(es) específicos)' },
  { value: 'require_accessibility', label: 'Acessibilidade obrigatória' },
  { value: 'require_equipment', label: 'Equipamento obrigatório' },
  { value: 'proximity', label: 'Proximidade entre duas equipes (soft)' },
  { value: 'exclusion', label: 'Exclusão entre dois setores (não podem dividir andar)' },
]

const emptyTeamForm = {
  sector_id: '',
  name: '',
  size: 10,
  schedule: '09:00-18:00',
  priority: 3,
  preferred_floor: '',
  needs_accessibility: false,
  special_requirements: '',
}

export default function Setores() {
  const [sectors, setSectors] = useState<Sector[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [constraints, setConstraints] = useState<ConstraintRule[]>([])
  const [teamForm, setTeamForm] = useState(emptyTeamForm)
  const [constraintForm, setConstraintForm] = useState({
    type: 'allowed_floor',
    hard: true,
    team_id: '',
    team_id_b: '',
    sector_id: '',
    sector_id_b: '',
    floor: '',
    equipment: '',
    max_floor_distance: 1,
    description: '',
  })

  const reload = () => {
    listSectors().then(setSectors)
    listTeams().then(setTeams)
    listConstraints().then(setConstraints)
  }

  useEffect(reload, [])

  const sectorsById = Object.fromEntries(sectors.map((s) => [s.id, s]))

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault()
    await createTeam({
      sector_id: Number(teamForm.sector_id),
      name: teamForm.name,
      size: Number(teamForm.size),
      schedule: teamForm.schedule,
      priority: Number(teamForm.priority),
      preferred_floor: teamForm.preferred_floor ? Number(teamForm.preferred_floor) : null,
      needs_accessibility: teamForm.needs_accessibility,
      special_requirements: teamForm.special_requirements
        ? teamForm.special_requirements.split(',').map((s) => s.trim())
        : [],
    })
    setTeamForm(emptyTeamForm)
    reload()
  }

  const handleCreateConstraint = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload: Record<string, unknown> = {}
    if (constraintForm.type === 'allowed_floor' && constraintForm.floor) payload.floors = [Number(constraintForm.floor)]
    if (constraintForm.type === 'require_equipment') payload.equipment = constraintForm.equipment
    if (constraintForm.type === 'proximity') payload.max_floor_distance = Number(constraintForm.max_floor_distance)

    await createConstraint({
      type: constraintForm.type,
      hard: constraintForm.type === 'proximity' ? false : constraintForm.hard,
      active: true,
      team_id: constraintForm.team_id ? Number(constraintForm.team_id) : null,
      team_id_b: constraintForm.team_id_b ? Number(constraintForm.team_id_b) : null,
      sector_id: constraintForm.sector_id ? Number(constraintForm.sector_id) : null,
      sector_id_b: constraintForm.sector_id_b ? Number(constraintForm.sector_id_b) : null,
      payload,
      description: constraintForm.description || undefined,
    })
    reload()
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Setores & Equipes</h2>
        <p className="text-sm text-slate-500">Visão do Coordenador de Setor — cadastro de equipes e restrições.</p>
      </div>

      <div className="grid md:grid-cols-8 gap-6">
        {sectors.map((sector) => (
          <div key={sector.id} className="bg-white border border-slate-200 rounded-lg p-4 md:col-span-2">
            <h3 className="font-medium text-slate-800">{sector.name}</h3>
            <p className="text-xs text-slate-500 mb-2">Coordenador: {sector.coordinator_name}</p>
            <p className="text-xs text-slate-500 mb-2">{sector.employee_count} funcionários</p>
            <ul className="text-xs text-slate-600 space-y-1">
              {teams
                .filter((t) => t.sector_id === sector.id)
                .map((t) => (
                  <li key={t.id} className="flex justify-between">
                    <span>{t.name}</span>
                    <span className="text-slate-400">{t.size}p</span>
                  </li>
                ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <form onSubmit={handleCreateTeam} className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
          <h3 className="font-medium text-slate-800">Cadastrar nova equipe</h3>
          <select
            required
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={teamForm.sector_id}
            onChange={(e) => setTeamForm({ ...teamForm, sector_id: e.target.value })}
          >
            <option value="">Setor...</option>
            {sectors.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input
            required
            placeholder="Nome da equipe"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={teamForm.name}
            onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              min={1}
              required
              placeholder="Qtd. funcionários"
              className="border rounded px-2 py-1.5 text-sm"
              value={teamForm.size}
              onChange={(e) => setTeamForm({ ...teamForm, size: Number(e.target.value) })}
            />
            <input
              placeholder="Horário (ex: 09:00-18:00)"
              className="border rounded px-2 py-1.5 text-sm"
              value={teamForm.schedule}
              onChange={(e) => setTeamForm({ ...teamForm, schedule: e.target.value })}
            />
            <select
              className="border rounded px-2 py-1.5 text-sm"
              value={teamForm.priority}
              onChange={(e) => setTeamForm({ ...teamForm, priority: Number(e.target.value) })}
            >
              {[1, 2, 3, 4, 5].map((p) => (
                <option key={p} value={p}>
                  Prioridade {p}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={1}
              max={9}
              placeholder="Andar preferido"
              className="border rounded px-2 py-1.5 text-sm"
              value={teamForm.preferred_floor}
              onChange={(e) => setTeamForm({ ...teamForm, preferred_floor: e.target.value })}
            />
          </div>
          <input
            placeholder="Recursos necessários (separados por vírgula: projetor, tv...)"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={teamForm.special_requirements}
            onChange={(e) => setTeamForm({ ...teamForm, special_requirements: e.target.value })}
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={teamForm.needs_accessibility}
              onChange={(e) => setTeamForm({ ...teamForm, needs_accessibility: e.target.checked })}
            />
            Necessita acessibilidade
          </label>
          <button className="bg-purple-600 text-white text-sm px-4 py-2 rounded">Cadastrar equipe</button>
        </form>

        <form onSubmit={handleCreateConstraint} className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
          <h3 className="font-medium text-slate-800">Nova restrição</h3>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={constraintForm.type}
            onChange={(e) => setConstraintForm({ ...constraintForm, type: e.target.value })}
          >
            {CONSTRAINT_TYPES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>

          {['allowed_floor', 'require_accessibility', 'require_equipment'].includes(constraintForm.type) && (
            <select
              className="w-full border rounded px-2 py-1.5 text-sm"
              value={constraintForm.team_id}
              onChange={(e) => setConstraintForm({ ...constraintForm, team_id: e.target.value })}
            >
              <option value="">Equipe...</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          )}

          {constraintForm.type === 'allowed_floor' && (
            <input
              type="number"
              min={1}
              max={9}
              placeholder="Andar permitido"
              className="w-full border rounded px-2 py-1.5 text-sm"
              value={constraintForm.floor}
              onChange={(e) => setConstraintForm({ ...constraintForm, floor: e.target.value })}
            />
          )}

          {constraintForm.type === 'require_equipment' && (
            <input
              placeholder="Equipamento (ex: projetor)"
              className="w-full border rounded px-2 py-1.5 text-sm"
              value={constraintForm.equipment}
              onChange={(e) => setConstraintForm({ ...constraintForm, equipment: e.target.value })}
            />
          )}

          {constraintForm.type === 'proximity' && (
            <>
              <select
                className="w-full border rounded px-2 py-1.5 text-sm"
                value={constraintForm.team_id}
                onChange={(e) => setConstraintForm({ ...constraintForm, team_id: e.target.value })}
              >
                <option value="">Equipe A...</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              <select
                className="w-full border rounded px-2 py-1.5 text-sm"
                value={constraintForm.team_id_b}
                onChange={(e) => setConstraintForm({ ...constraintForm, team_id_b: e.target.value })}
              >
                <option value="">Equipe B...</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </>
          )}

          {constraintForm.type === 'exclusion' && (
            <>
              <select
                className="w-full border rounded px-2 py-1.5 text-sm"
                value={constraintForm.sector_id}
                onChange={(e) => setConstraintForm({ ...constraintForm, sector_id: e.target.value })}
              >
                <option value="">Setor A...</option>
                {sectors.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <select
                className="w-full border rounded px-2 py-1.5 text-sm"
                value={constraintForm.sector_id_b}
                onChange={(e) => setConstraintForm({ ...constraintForm, sector_id_b: e.target.value })}
              >
                <option value="">Setor B...</option>
                {sectors.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </>
          )}

          <input
            placeholder="Descrição (opcional)"
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={constraintForm.description}
            onChange={(e) => setConstraintForm({ ...constraintForm, description: e.target.value })}
          />

          <button className="bg-slate-800 text-white text-sm px-4 py-2 rounded">Adicionar restrição</button>
        </form>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <h3 className="font-medium text-slate-800 p-4 pb-0">Restrições cadastradas</h3>
        <table className="w-full text-sm mt-2">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Tipo</th>
              <th className="text-left px-4 py-2">Obrigatória</th>
              <th className="text-left px-4 py-2">Descrição</th>
              <th className="text-left px-4 py-2">Ativa</th>
              <th className="text-left px-4 py-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {constraints.map((c) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="px-4 py-2">{c.type}</td>
                <td className="px-4 py-2">{c.hard ? 'Sim' : 'Não (preferência)'}</td>
                <td className="px-4 py-2 text-slate-500">
                  {c.description || `${c.team_id ? `equipe ${c.team_id}` : ''} ${c.sector_id ? `setor ${c.sector_id}` : ''}`}
                </td>
                <td className="px-4 py-2">
                  <button
                    className={c.active ? 'text-emerald-600 text-xs' : 'text-slate-400 text-xs'}
                    onClick={() => toggleConstraint(c.id).then(reload)}
                  >
                    {c.active ? 'Ativa' : 'Inativa'}
                  </button>
                </td>
                <td className="px-4 py-2">
                  <button className="text-red-600 text-xs" onClick={() => deleteConstraint(c.id).then(reload)}>
                    Remover
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {Object.keys(sectorsById).length === 0 && <p className="text-slate-400 text-sm">Nenhum setor cadastrado.</p>}
    </div>
  )
}
