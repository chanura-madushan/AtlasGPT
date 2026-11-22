import { useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'

function EntryRoute() {
  const { isAuthenticated, loading, continueAsGuest } = useAuth()
  const navigate = useNavigate()
  const started = useRef(false)

  useEffect(() => {
    if (loading || isAuthenticated || started.current) return

    started.current = true
    continueAsGuest().catch(() => {
      navigate('/login', { replace: true })
    })
  }, [loading, isAuthenticated, continueAsGuest, navigate])

  if (loading || !isAuthenticated) {
    return (
      <div className="app-loading" role="status" aria-live="polite">
        <span className="loading-mark">A</span>
        <span>Opening AtlasGPT…</span>
      </div>
    )
  }

  return <Navigate to="/dashboard" replace />
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="app-loading" role="status" aria-live="polite">
        <span className="loading-mark">A</span>
        <span>Opening your workspace…</span>
      </div>
    )
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EntryRoute />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
