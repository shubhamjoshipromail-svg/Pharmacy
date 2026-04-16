import { useState } from 'react'

import api from '../api'
import SeverityBadge from './SeverityBadge'

const borderStyles = {
  contraindicated: 'border-l-red-500',
  major: 'border-l-orange-500',
  moderate: 'border-l-yellow-500',
  minor: 'border-l-blue-500',
  unknown: 'border-l-slate-300',
}

const confidenceStyles = {
  high: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-red-100 text-red-700',
}

export default function InteractionCard({
  summary,
  suppressed,
  findingId,
  patientId,
  interactionId,
  onReviewed,
}) {
  const [expanded, setExpanded] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [loadingExplanation, setLoadingExplanation] = useState(false)
  const [explanationError, setExplanationError] = useState('')
  const [reviewing, setReviewing] = useState(false)
  const [overrideOpen, setOverrideOpen] = useState(false)
  const [overrideNote, setOverrideNote] = useState('')
  const [overrideLoading, setOverrideLoading] = useState(false)
  const [overrideMessage, setOverrideMessage] = useState('')
  const [overrideError, setOverrideError] = useState('')

  const loadExplanation = async () => {
    if (explanation || loadingExplanation) {
      return
    }

    setLoadingExplanation(true)
    setExplanationError('')
    try {
      const response = await api.post(`/findings/${findingId}/explain`)
      setExplanation(response.data)
    } catch (error) {
      setExplanationError(error.response?.data?.detail || 'Unable to fetch AI explanation.')
    } finally {
      setLoadingExplanation(false)
    }
  }

  const handleReviewed = async () => {
    setReviewing(true)
    setExplanationError('')
    try {
      await api.post(`/patients/${patientId}/interactions/${interactionId}/acknowledge`, {})
      await onReviewed()
    } catch (error) {
      setExplanationError(error.response?.data?.detail || 'Unable to mark this interaction as reviewed.')
    } finally {
      setReviewing(false)
    }
  }

  const handleOverride = async () => {
    if (!overrideNote.trim()) {
      setOverrideError('An override note is required.')
      return
    }

    setOverrideLoading(true)
    setOverrideError('')
    setOverrideMessage('')
    try {
      await api.post(`/findings/${findingId}/override`, {
        action: 'overridden',
        note: overrideNote.trim(),
      })
      setOverrideMessage('Override recorded.')
      setOverrideOpen(false)
      setOverrideNote('')
    } catch (error) {
      setOverrideError(error.response?.data?.detail || 'Unable to save override.')
    } finally {
      setOverrideLoading(false)
    }
  }

  return (
    <div
      className={[
        'overflow-hidden rounded-2xl border border-slate-200 border-l-[3px] bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md',
        borderStyles[summary.severity] || borderStyles.unknown,
        suppressed ? 'opacity-70' : '',
      ].join(' ')}
    >
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="w-full px-5 py-4 text-left"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-slate-900">
              {summary.drug_a_name} ↔ {summary.drug_b_name}
            </div>
            <div className="mt-1 text-sm text-slate-500">{summary.mechanism_brief || 'No mechanism summary available.'}</div>
          </div>
          <SeverityBadge severity={summary.severity} />
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {summary.effect_brief ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">{summary.effect_brief}</span>
          ) : null}
          {summary.action_brief ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">{summary.action_brief}</span>
          ) : null}
        </div>

        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
          {summary.sources_conflict ? <div className="text-amber-600">⚠ Sources disagree</div> : null}
          {(summary.hub_score_a || 0) > 3 ? <div className="text-slate-400">High interaction drug</div> : null}
        </div>
      </button>

      {expanded ? (
        <div className="border-t border-slate-100 px-5 py-4">
          <div className="grid gap-4">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Clinical snapshot</div>
              <div className="mt-3 grid gap-3 text-sm text-slate-600">
                <div>
                  <div className="mb-1 font-medium text-slate-900">Mechanism</div>
                  <div>{summary.mechanism_brief || 'No mechanism detail available in current summary.'}</div>
                </div>
                <div>
                  <div className="mb-1 font-medium text-slate-900">Recommended action</div>
                  <div>{summary.action_brief || 'No management detail available in current summary.'}</div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={loadExplanation}
                disabled={loadingExplanation}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-60"
              >
                {loadingExplanation ? 'Loading…' : 'Get AI Explanation'}
              </button>
              <button
                type="button"
                onClick={handleReviewed}
                disabled={reviewing}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:opacity-60"
              >
                {reviewing ? 'Reviewing…' : 'Mark as Reviewed'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setOverrideOpen((value) => !value)
                  setOverrideError('')
                  setOverrideMessage('')
                }}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              >
                Override
              </button>
            </div>

            {explanationError ? <div className="text-sm text-red-600">{explanationError}</div> : null}

            {explanation ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-900">AI Explanation</div>
                  {explanation.confidence ? (
                    <span
                      className={[
                        'rounded-full px-2.5 py-1 text-xs font-medium capitalize',
                        confidenceStyles[explanation.confidence] || 'bg-slate-100 text-slate-600',
                      ].join(' ')}
                    >
                      {explanation.confidence} confidence
                    </span>
                  ) : null}
                </div>
                <div className="mt-3 grid gap-3 text-sm text-slate-600">
                  {explanation.summary ? (
                    <div>
                      <div className="mb-1 font-medium text-slate-900">Summary</div>
                      <div>{explanation.summary}</div>
                    </div>
                  ) : null}
                  {explanation.mechanism ? (
                    <div>
                      <div className="mb-1 font-medium text-slate-900">Mechanism</div>
                      <div>{explanation.mechanism}</div>
                    </div>
                  ) : null}
                  {explanation.clinical_effect ? (
                    <div>
                      <div className="mb-1 font-medium text-slate-900">Clinical effect</div>
                      <div>{explanation.clinical_effect}</div>
                    </div>
                  ) : null}
                  {explanation.management ? (
                    <div>
                      <div className="mb-1 font-medium text-slate-900">Management</div>
                      <div>{explanation.management}</div>
                    </div>
                  ) : null}
                </div>
                <div className="mt-3 text-xs text-slate-400">
                  sources: {(explanation.sources_used || []).join(', ') || 'No sources listed'}
                </div>
              </div>
            ) : null}

            {overrideOpen ? (
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="mb-2 text-sm font-semibold text-slate-900">Override Note</div>
                <textarea
                  value={overrideNote}
                  onChange={(event) => setOverrideNote(event.target.value)}
                  rows={3}
                  placeholder="Document the reason for this override..."
                  className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50"
                />
                {overrideError ? <div className="mt-2 text-sm text-red-600">{overrideError}</div> : null}
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleOverride}
                    disabled={overrideLoading}
                    className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-60"
                  >
                    {overrideLoading ? 'Saving…' : 'Confirm Override'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setOverrideOpen(false)}
                    className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : null}

            {overrideMessage ? <div className="text-sm text-emerald-700">{overrideMessage}</div> : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}
