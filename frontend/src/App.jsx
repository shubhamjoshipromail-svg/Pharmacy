import { BrowserRouter, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import PatientDetail from './components/PatientDetail'
import PatientList from './components/PatientList'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<PatientList />} />
          <Route path="patients/:patientId" element={<PatientDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
