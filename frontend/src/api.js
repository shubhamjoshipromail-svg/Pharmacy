import axios from 'axios'

const baseApiUrl = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/$/, '')}/api/v1`
  : 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: baseApiUrl,
  headers: { 'Content-Type': 'application/json' },
})

export default api
