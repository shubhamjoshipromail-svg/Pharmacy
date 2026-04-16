import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import api from '../api'

const storageKey = 'rxcheck:patient-names'

function readPatientNames() {
  try {
    return JSON.parse(window.localStorage.getItem(storageKey) || '{}')
  } catch {
    return {}
  }
}

function writePatientName(patientId, givenName, familyName) {
  const current = readPatientNames()
  current[patientId] = {
    givenName: givenName || '',
    familyName: familyName || '',
  }
  window.localStorage.setItem(storageKey, JSON.stringify(current))
}

function patientDisplayName(patientId) {
  const entry = readPatientNames()[patientId]
  if (!entry) {
    return 'Anonymous Patient'
  }
  const name = [entry.givenName, entry.familyName].filter(Boolean).join(' ').trim()
  return name || 'Anonymous Patient'
}

function formatTimestamp(value) {
  if (!value) {
    return 'No prior checks'
  }
  return new Date(value).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export default function PatientList() {
  const navigate = useNavigate()
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingDemo, setLoadingDemo] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ given_name: '', family_name: '' })

  const loadPatients = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/patients')
      setPatients(response.data)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to load patients.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPatients()
  }, [])

  const handleDemo = async () => {
    setLoadingDemo(true)
    setError('')
    try {
      const response = await api.post('/dev/seed')
      window.localStorage.setItem(`rxcheck:lastResult:${response.data.patient_id}`, JSON.stringify(response.data))
      navigate(`/patients/${response.data.patient_id}`, {
        state: { initialResult: response.data, refreshToken: Date.now() },
      })
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to load demo patient.')
    } finally {
      setLoadingDemo(false)
    }
  }

  const handleCreate = async (event) => {
    event.preventDefault()
    setCreating(true)
    setError('')
    try {
      const response = await api.post('/patients', form)
      writePatientName(response.data.id, form.given_name, form.family_name)
      navigate(`/patients/${response.data.id}`, {
        state: {
          patientName: {
            givenName: form.given_name,
            familyName: form.family_name,
          },
          refreshToken: Date.now(),
        },
      })
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to create patient.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-10 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Patients</h1>
        <p className="mt-2 text-sm text-slate-500">
          Seed a realistic demo or create a new patient record to start checking interactions.
        </p>
      </div>

      <div className="grid gap-6">
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-lg font-semibold text-slate-950">Load Demo</div>
              <div className="mt-1 max-w-xl text-sm text-slate-500">
                Create a synthetic polypharmacy patient and jump directly into a full interaction review.
              </div>
            </div>
            <button
              type="button"
              onClick={handleDemo}
              disabled={loadingDemo}
              className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-500 disabled:opacity-60"
            >
              {loadingDemo ? 'Loading…' : 'Load Demo'}
            </button>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <div className="text-lg font-semibold text-slate-950">New Patient</div>
          <form className="mt-4 grid gap-4 md:grid-cols-[1fr_1fr_auto]" onSubmit={handleCreate}>
            <input
              value={form.given_name}
              onChange={(event) => setForm((current) => ({ ...current, given_name: event.target.value }))}
              placeholder="Given name"
              className="h-11 rounded-xl border border-slate-200 px-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50"
            />
            <input
              value={form.family_name}
              onChange={(event) => setForm((current) => ({ ...current, family_name: event.target.value }))}
              placeholder="Family name"
              className="h-11 rounded-xl border border-slate-200 px-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-300 focus:ring-4 focus:ring-indigo-50"
            />
            <button
              type="submit"
              disabled={creating}
              className="h-11 rounded-xl border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-60"
            >
              {creating ? 'Creating…' : 'Create Patient'}
            </button>
          </form>
          {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}
        </section>

        <section>
          <div className="mb-4 text-sm font-semibold uppercase tracking-[0.16em] text-slate-400">Patient List</div>
          {loading ? (
            <div className="rounded-3xl border border-slate-200 bg-white p-8 text-sm text-slate-400">Loading patients…</div>
          ) : (
            <div className="grid gap-4">
              {patients.map((patient) => (
                <button
                  key={patient.id}
                  type="button"
                  onClick={() => navigate(`/patients/${patient.id}`)}
                  className="rounded-3xl border border-slate-200 bg-white p-5 text-left transition hover:border-slate-300 hover:shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-base font-semibold text-slate-950">{patientDisplayName(patient.id)}</div>
                      <div className="mt-1 text-sm text-slate-500">{patient.medication_count} medications</div>
                    </div>
                    <div className="text-right text-xs text-slate-400">
                      <div>Last check</div>
                      <div className="mt-1">{formatTimestamp(patient.most_recent_check_run_at)}</div>
                    </div>
                  </div>
                </button>
              ))}
              {!patients.length ? (
                <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 text-sm text-slate-400">
                  No patients yet.
                </div>
              ) : null}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
