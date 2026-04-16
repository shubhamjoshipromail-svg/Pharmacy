const severityStyles = {
  contraindicated: 'border-red-200 bg-red-100 text-red-700',
  major: 'border-orange-200 bg-orange-100 text-orange-700',
  moderate: 'border-yellow-200 bg-yellow-100 text-yellow-700',
  minor: 'border-blue-200 bg-blue-100 text-blue-700',
  unknown: 'border-slate-200 bg-slate-100 text-slate-500',
}

const severityLabels = {
  contraindicated: 'CONTRAINDICATED',
  major: 'MAJOR',
  moderate: 'MODERATE',
  minor: 'MINOR',
  unknown: 'UNKNOWN',
}

export default function SeverityBadge({ severity }) {
  const normalized = severity || 'unknown'

  return (
    <span
      className={[
        'inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-[0.12em]',
        severityStyles[normalized] || severityStyles.unknown,
      ].join(' ')}
    >
      {severityLabels[normalized] || severityLabels.unknown}
    </span>
  )
}
