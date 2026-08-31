interface Props {
  label: string
  value: string | number
  hint?: string
  tone?: 'default' | 'good' | 'bad' | 'warn'
}

const TONE_CLASSES: Record<string, string> = {
  default: 'border-slate-200 bg-white',
  good: 'border-emerald-200 bg-emerald-50',
  bad: 'border-red-200 bg-red-50',
  warn: 'border-amber-200 bg-amber-50',
}

export default function StatCard({ label, value, hint, tone = 'default' }: Props) {
  return (
    <div className={`rounded-lg border p-4 shadow-sm ${TONE_CLASSES[tone]}`}>
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-semibold text-slate-900 mt-1">{value}</div>
      {hint && <div className="text-xs text-slate-400 mt-1">{hint}</div>}
    </div>
  )
}
