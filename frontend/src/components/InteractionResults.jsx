import { useMemo, useState } from 'react'

import InteractionCard from './InteractionCard'

const severitySections = [
  { key: 'contraindicated', label: 'CONTRAINDICATED', tone: 'text-red-600' },
  { key: 'major', label: 'MAJOR', tone: 'text-orange-600' },
  { key: 'moderate', label: 'MODERATE', tone: 'text-yellow-600' },
  { key: 'minor', label: 'MINOR', tone: 'text-blue-600' },
]

const severityBadgeStyles = {
  contraindicated: 'border-red-200 bg-red-100 text-red-700',
  major: 'border-orange-200 bg-orange-100 text-orange-700',
  moderate: 'border-yellow-200 bg-yellow-100 text-yellow-700',
  minor: 'border-blue-200 bg-blue-100 text-blue-700',
}

function formatCheckedAt(result) {
  if (!result?.checked_at) {
    return 'No recent check'
  }

  return new Date(result.checked_at).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export default function InteractionResults({ result, patientId, onReviewed }) {
  const [showSuppressed, setShowSuppressed] = useState(false)

  const grouped = useMemo(() => {
    const buckets = {
      contraindicated: [],
      major: [],
      moderate: [],
      minor: [],
      suppressed: [],
    }

    for (const item of result?.summaries || []) {
      if (item.suppressed) {
        buckets.suppressed.push(item)
      } else if (buckets[item.summary.severity]) {
        buckets[item.summary.severity].push(item)
      }
    }

    return buckets
  }, [result])

  if (!result) {
    return null
  }

  if (result.total_interactions_found === 0) {
    return (
      <div className="flex h-full min-h-[420px] items-center justify-center rounded-3xl border border-emerald-100 bg-emerald-50 p-8 text-center">
        <div>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white text-xl text-emerald-600 shadow-sm">
            ✓
          </div>
          <div className="mt-4 text-lg font-semibold text-slate-900">No interactions found</div>
          <div className="mt-2 max-w-md text-sm text-slate-500">
            No interactions found in our database for this medication combination. Always verify with institutional references.
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6">
      <div className="border-b border-slate-100 pb-5">
        <div className="text-2xl font-semibold tracking-tight text-slate-950">
          {result.total_interactions_found} interactions found
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {severitySections.map((section) => {
            const countKey = section.key === 'contraindicated' ? 'critical_count' : `${section.key}_count`
            const count = result[countKey]
            if (!count) {
              return null
            }
            return (
              <span
                key={section.key}
                className={[
                  'rounded-full border px-2.5 py-1 text-xs font-semibold tracking-[0.08em]',
                  severityBadgeStyles[section.key],
                ].join(' ')}
              >
                {count} {section.label}
              </span>
            )
          })}
        </div>
        <div className="mt-3 text-sm text-slate-400">
          {result.total_medications} medications · {result.total_pairs_checked} pairs checked · {formatCheckedAt(result)}
        </div>
      </div>

      <div className="mt-6 space-y-6">
        {severitySections.map((section) => {
          const items = grouped[section.key]
          if (!items.length) {
            return null
          }

          return (
            <section key={section.key}>
              <div className={`mb-3 text-xs font-semibold tracking-[0.18em] ${section.tone}`}>{section.label}</div>
              <div className="space-y-3">
                {items.map((item) => (
                  <InteractionCard
                    key={item.finding_id}
                    summary={item.summary}
                    suppressed={item.suppressed}
                    findingId={item.finding_id}
                    patientId={patientId}
                    interactionId={item.interaction_id}
                    onReviewed={onReviewed}
                  />
                ))}
              </div>
            </section>
          )
        })}

        {grouped.suppressed.length ? (
          <section className="border-t border-slate-100 pt-5">
            <button
              type="button"
              onClick={() => setShowSuppressed((value) => !value)}
              className="text-sm font-medium text-slate-500 transition hover:text-slate-700"
            >
              {grouped.suppressed.length} previously reviewed {showSuppressed ? '−' : '+'}
            </button>
            {showSuppressed ? (
              <div className="mt-4 space-y-3">
                {grouped.suppressed.map((item) => (
                  <InteractionCard
                    key={item.finding_id}
                    summary={item.summary}
                    suppressed={item.suppressed}
                    findingId={item.finding_id}
                    patientId={patientId}
                    interactionId={item.interaction_id}
                    onReviewed={onReviewed}
                  />
                ))}
              </div>
            ) : null}
          </section>
        ) : null}
      </div>
    </div>
  )
}
