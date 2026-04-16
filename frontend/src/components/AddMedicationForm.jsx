import { useState } from 'react'
import axios from 'axios'

import api from '../api'

export default function AddMedicationForm({ patientId, onAdded }) {
  const [rawInput, setRawInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [warning, setWarning] = useState('')
  const [candidates, setCandidates] = useState([])

  const submitMedication = async (value) => {
    setLoading(true)
    setError('')
    setWarning('')

    try {
      const response = await api.post(`/patients/${patientId}/medications`, { raw_input: value })
      if (response.status === 202 && response.data?.candidates) {
        setCandidates(response.data.candidates)
        setWarning(response.data.message || '')
        return
      }

      setCandidates([])
      setRawInput('')
      setWarning(response.data.warning || '')
      onAdded(response.data)
    } catch (requestError) {
      if (!axios.isAxiosError(requestError)) {
        setError('Unable to add medication right now.')
      } else {
        setError(requestError.response?.data?.detail || 'Unable to add medication right now.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!rawInput.trim()) {
      return
    }
    await submitMedication(rawInput.trim())
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="mb-3 text-sm font-semibold text-slate-900">Add Medication</div>
      <form className="flex items-center gap-2" onSubmit={handleSubmit}>
        <input
          value={rawInput}
          onChange={(event) => setRawInput(event.target.value)}
          placeholder="Type a drug name..."
          className="h-11 flex-1 rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50"
        />
        <button
          type="submit"
          disabled={loading}
          className="h-11 rounded-xl border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-60"
        >
          {loading ? 'Adding…' : 'Add'}
        </button>
      </form>

      {warning ? <div className="mt-3 text-sm text-amber-700">{warning}</div> : null}
      {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}

      {candidates.length ? (
        <div className="mt-4">
          <div className="mb-2 text-xs font-medium uppercase tracking-[0.12em] text-slate-400">
            Suggested matches
          </div>
          <div className="flex flex-wrap gap-2">
            {candidates.map((candidate) => (
              <button
                key={`${candidate.rxcui}-${candidate.preferred_name}`}
                type="button"
                onClick={() => submitMedication(candidate.preferred_name)}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
              >
                {candidate.preferred_name}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
