import { NavLink, Route, Routes } from 'react-router-dom'
import Alocacao from './pages/Alocacao'
import Auditoria from './pages/Auditoria'
import Comparacao from './pages/Comparacao'
import Dashboard from './pages/Dashboard'
import Monitoramento from './pages/Monitoramento'
import Salas from './pages/Salas'
import Setores from './pages/Setores'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/alocacao', label: 'Gerar Alocação' },
  { to: '/comparacao', label: 'Comparação' },
  { to: '/setores', label: 'Setores & Equipes' },
  { to: '/salas', label: 'Salas' },
  { to: '/monitoramento', label: 'Monitoramento' },
  { to: '/auditoria', label: 'Auditoria' },
]

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <h1 className="text-lg font-semibold">
            Sistema Inteligente de Gestão e Otimização de Espaços Corporativos
          </h1>
          <p className="text-slate-400 text-sm">Painel do Coordenador Geral · Prédio de 9 andares</p>
        </div>
        <nav className="max-w-7xl mx-auto px-6 flex gap-1 overflow-x-auto border-t border-slate-800">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `px-4 py-3 text-sm whitespace-nowrap border-b-2 transition-colors ${
                  isActive
                    ? 'border-purple-400 text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alocacao" element={<Alocacao />} />
          <Route path="/comparacao" element={<Comparacao />} />
          <Route path="/setores" element={<Setores />} />
          <Route path="/salas" element={<Salas />} />
          <Route path="/monitoramento" element={<Monitoramento />} />
          <Route path="/auditoria" element={<Auditoria />} />
        </Routes>
      </main>

      <footer className="text-center text-xs text-slate-400 py-4 border-t">
        Protótipo — ISTQB CT-AI · Qualidade e Testes de Sistemas Baseados em IA
      </footer>
    </div>
  )
}

export default App
