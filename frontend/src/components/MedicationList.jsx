function medicationMeta(medication) {
  return [medication.dose, medication.route, medication.frequency].filter(Boolean).join(' · ')
}

export default function MedicationList({ medications, patientId, onRemove, removingId }) {
  if (!medications.length) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-400">
        No medications added yet
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      {medications.map((medication, index) => (
        <div
          key={medication.id}
          className={[
            'group flex items-start gap-3 px-4 py-3',
            index !== medications.length - 1 ? 'border-b border-slate-100' : '',
          ].join(' ')}
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <div className="truncate text-sm font-semibold text-slate-900">
                {medication.is_placeholder ? medication.raw_input : medication.preferred_name}
              </div>
              <span
                title={
                  medication.is_placeholder
                    ? 'Drug could not be verified — interactions may be incomplete'
                    : 'Drug verified against NIH RxNorm database'
                }
                className={[
                  'rounded-full px-2 py-0.5 text-[11px] font-medium',
                  medication.is_placeholder
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-emerald-100 text-emerald-700',
                ].join(' ')}
              >
                {medication.is_placeholder ? '!' : '✓'}
              </span>
            </div>
            {medicationMeta(medication) ? (
              <div className="mt-1 text-xs text-slate-400">{medicationMeta(medication)}</div>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => onRemove(patientId, medication.id)}
            disabled={removingId === medication.id}
            className="rounded-md px-2 py-1 text-slate-300 opacity-0 transition hover:bg-slate-100 hover:text-slate-600 group-hover:opacity-100 disabled:opacity-100"
            aria-label={`Remove ${medication.preferred_name}`}
          >
            {removingId === medication.id ? '…' : '×'}
          </button>
        </div>
      ))}
    </div>
  )
}
