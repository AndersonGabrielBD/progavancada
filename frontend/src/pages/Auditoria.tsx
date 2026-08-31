import { useEffect, useState } from 'react'
import { listAuditLogs } from '../api/client'
import type { AuditLogEntry } from '../types'

const ACTION_LABEL: Record<string, string> = {
  RERUN: 'Execução do motor',
  ACCEPT: 'Recomendação aceita',
  REJECT: 'Recomendação rejeitada',
  MANUAL_OVERRIDE: 'Alocação alterada manualmente',
  CREATE: 'Cadastro criado',
  UPDATE: 'Cadastro atualizado',
}

export default function Auditoria() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])

  useEffect(() => {
    listAuditLogs().then(setLogs)
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Auditoria & Governança</h2>
        <p className="text-sm text-slate-500">
          Histórico de execuções e intervenções humanas — quem executou, quando, com quais dados e
          qual foi o resultado.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Data/hora</th>
              <th className="text-left px-4 py-2">Usuário</th>
              <th className="text-left px-4 py-2">Ação</th>
              <th className="text-left px-4 py-2">Entidade</th>
              <th className="text-left px-4 py-2">Execução</th>
              <th className="text-left px-4 py-2">Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-t border-slate-100">
                <td className="px-4 py-2 whitespace-nowrap">{new Date(l.created_at).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-2">{l.user}</td>
                <td className="px-4 py-2">{ACTION_LABEL[l.action] ?? l.action}</td>
                <td className="px-4 py-2 text-slate-500">
                  {l.entity ? `${l.entity} #${l.entity_id}` : '—'}
                </td>
                <td className="px-4 py-2 text-slate-500">{l.run_id ? `#${l.run_id}` : '—'}</td>
                <td className="px-4 py-2 text-xs font-mono text-slate-500 max-w-xs truncate" title={JSON.stringify(l.details)}>
                  {JSON.stringify(l.details)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && <p className="text-slate-400 text-sm p-4">Nenhum registro de auditoria ainda.</p>}
      </div>
    </div>
  )
}
