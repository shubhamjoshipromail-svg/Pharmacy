import { useEffect, useMemo, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'

import api from '../api'
import AddMedicationForm from './AddMedicationForm'
import InteractionResults from './InteractionResults'
import MedicationList from './MedicationList'

const patientNameStorageKey = 'rxcheck:patient-names'

function readPatientNames() {
  try {
    return JSON.parse(window.localStorage.getItem(patientNameStorageKey) || '{}')
  } catch {
    return {}
  }
}

function readLastResult(patientId) {
  try {
    return JSON.parse(window.localStorage.getItem(`rxcheck:lastResult:${patientId}`) || 'null')
  } catch {
    return null
  }
}

function initialsForName(givenName, familyName) {
  const initials = `${givenName?.[0] || ''}${familyName?.[0] || ''}`.trim()
  return initials || 'AP'
}

function formatDob(value) {
  if (!value) {
    return null
  }
  return new Date(value).toLocaleDateString()
}

export default function PatientDetail() {
  const { patientId } = useParams()
  const location = useLocation()
  const [patient, setPatient] = useState(null)
  const [conditions, setConditions] = useState([])
  const [patientLoading, setPatientLoading] = useState(true)
  const [checkLoading, setCheckLoading] = useState(false)
  const [result, setResult] = useState(location.state?.initialResult || readLastResult(patientId))
  const [removingId, setRemovingId] = useState('')
  const [conditionInput, setConditionInput] = useState('')
  const [conditionSaving, setConditionSaving] = useState(false)
  const [removingConditionId, setRemovingConditionId] = useState('')
  const [error, setError] = useState('')

  const patientName = useMemo(() => {
    const stored = readPatientNames()[patientId] || location.state?.patientName || {}
    return {
      givenName: stored.givenName || '',
      familyName: stored.familyName || '',
    }
  }, [location.state, patientId])

  const fullName = [patientName.givenName, patientName.familyName].filter(Boolean).join(' ').trim() || 'Anonymous Patient'

  const loadPatient = async () => {
    setPatientLoading(true)
    setError('')
    try {
      const [patientResponse, conditionsResponse] = await Promise.all([
        api.get(`/patients/${patientId}`),
        api.get(`/patients/${patientId}/conditions`),
      ])
      setPatient(patientResponse.data)
      setConditions(conditionsResponse.data)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to load patient details.')
    } finally {
      setPatientLoading(false)
    }
  }

  useEffect(() => {
    loadPatient()
  }, [patientId, location.state?.refreshToken])

  useEffect(() => {
    setResult(location.state?.initialResult || readLastResult(patientId))
  }, [location.state?.initialResult, patientId])

  const activeMedications = (patient?.medications || []).filter((medication) => medication.is_active)

  const runCheck = async () => {
    setCheckLoading(true)
    setError('')
    try {
      const response = await api.post(`/patients/${patientId}/check`, {})
      setResult(response.data)
      window.localStorage.setItem(`rxcheck:lastResult:${patientId}`, JSON.stringify(response.data))
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to run interaction check.')
    } finally {
      setCheckLoading(false)
    }
  }

  const handleMedicationAdded = async () => {
    await loadPatient()
  }

  const handleRemoveMedication = async (_patientId, medId) => {
    setRemovingId(medId)
    setError('')
    try {
      await api.delete(`/patients/${patientId}/medications/${medId}`)
      await loadPatient()
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to remove medication.')
    } finally {
      setRemovingId('')
    }
  }

  const handleReviewed = async () => {
    await runCheck()
  }

  const handleConditionAdd = async (event) => {
    event.preventDefault()
    if (!conditionInput.trim()) {
      return
    }

    setConditionSaving(true)
    setError('')
    try {
      await api.post(`/patients/${patientId}/conditions`, { condition_name: conditionInput.trim() })
      setConditionInput('')
      await loadPatient()
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to add condition.')
    } finally {
      setConditionSaving(false)
    }
  }

  const handleConditionRemove = async (conditionId) => {
    setRemovingConditionId(String(conditionId))
    setError('')
    try {
      await api.delete(`/patients/${patientId}/conditions/${conditionId}`)
      await loadPatient()
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to remove condition.')
    } finally {
      setRemovingConditionId('')
    }
  }

  if (patientLoading) {
    return <div className="p-10 text-sm text-slate-400">Loading patient…</div>
  }

  if (!patient) {
    return <div className="p-10 text-sm text-red-600">{error || 'Patient not found.'}</div>
  }

  return (
    <div className="flex h-full overflow-hidden bg-stone-50">
      <div className="w-2/5 min-w-[340px] max-w-[520px] h-full overflow-y-auto border-r border-slate-100 p-6">
        <div className="space-y-6 pb-6">
          <section className="rounded-3xl border border-slate-200 bg-white p-6">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-200 text-sm font-semibold text-slate-600">
                {initialsForName(patientName.givenName, patientName.familyName)}
              </div>
              <div>
                <div className="text-base font-semibold text-slate-950">{fullName}</div>
                <div className="mt-1 text-sm text-slate-500">
                  {formatDob(patient.date_of_birth) ? `DOB ${formatDob(patient.date_of_birth)}` : 'DOB unavailable'}
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-4">
            <div className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-400">Conditions</div>
            {conditions.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {conditions.map((condition) => (
                  <span
                    key={condition.id}
                    className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-600"
                  >
                    {condition.condition_name}
                    <button
                      type="button"
                      onClick={() => handleConditionRemove(condition.condition_id)}
                      disabled={removingConditionId === String(condition.condition_id)}
                      className="text-slate-400 transition hover:text-slate-700 disabled:opacity-60"
                      aria-label={`Remove ${condition.condition_name}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            ) : (
              <div className="mt-3 text-sm text-slate-400">No conditions recorded</div>
            )}

            <form className="mt-4 flex items-center gap-2" onSubmit={handleConditionAdd}>
              <input
                value={conditionInput}
                onChange={(event) => setConditionInput(event.target.value)}
                placeholder="Add condition..."
                className="h-10 flex-1 rounded-xl border border-slate-200 px-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50"
              />
              <button
                type="submit"
                disabled={conditionSaving}
                className="h-10 rounded-xl border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-60"
              >
                {conditionSaving ? 'Adding…' : 'Add'}
              </button>
            </form>
          </section>

          <section className="space-y-3">
            <div className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-400">Medications</div>
            <MedicationList
              medications={activeMedications}
              patientId={patientId}
              onRemove={handleRemoveMedication}
              removingId={removingId}
            />
          </section>

          <AddMedicationForm patientId={patientId} onAdded={handleMedicationAdded} />

          <button
            type="button"
            onClick={runCheck}
            disabled={checkLoading}
            className="flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-indigo-600 px-5 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-500 disabled:opacity-60"
          >
            {checkLoading ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Running Interaction Check
              </>
            ) : (
              'Run Interaction Check'
            )}
          </button>

          {error ? <div className="text-sm text-red-600">{error}</div> : null}
        </div>
      </div>

      <div className="w-3/5 min-w-0 h-full overflow-y-auto p-6">
        <div className="pb-6">
          {!result ? (
            <div className="flex min-h-[720px] items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-white p-12 text-center">
              <div>
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-2xl text-slate-400">
                  ⌁
                </div>
                <div className="mt-5 text-lg font-medium text-slate-700">
                  Add medications and run a check to see interactions
                </div>
                <div className="mt-2 text-sm text-slate-400">
                  Results will appear here once the clinical review finishes.
                </div>
              </div>
            </div>
          ) : checkLoading ? (
            <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6">
              <div className="h-8 w-48 animate-pulse rounded bg-slate-100" />
              <div className="h-24 animate-pulse rounded-2xl bg-slate-100" />
              <div className="h-24 animate-pulse rounded-2xl bg-slate-100" />
              <div className="h-24 animate-pulse rounded-2xl bg-slate-100" />
            </div>
          ) : (
            <InteractionResults result={result} patientId={patientId} onReviewed={handleReviewed} />
          )}
        </div>
      </div>
    </div>
  )
}
