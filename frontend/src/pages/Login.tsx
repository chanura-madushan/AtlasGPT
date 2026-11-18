
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { ApiError } from '../services/api'

export default function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Unable to connect to the server. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-atlas-pearl px-6 py-12">
      <div className="w-full max-w-md">
        <Link
          to="/"
          className="mb-10 block text-center font-heading text-3xl font-bold text-atlas-navy"
        >
          AtlasGPT<span className="text-atlas-cyan">.</span>
        </Link>

        <section className="rounded-3xl border border-atlas-mist bg-white p-8 shadow-xl shadow-atlas-navy/5 sm:p-10">
          <div className="text-center">
            <h1 className="font-heading text-2xl font-bold text-atlas-navy">
              Welcome back
            </h1>

            <p className="mt-3 text-sm leading-6 text-atlas-slate">
              Sign in to continue exploring your knowledge.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-semibold text-atlas-navy"
              >
                Email address
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
                className="w-full rounded-xl border border-atlas-mist px-4 py-3 text-sm outline-none transition focus:border-atlas-cyan focus:ring-2 focus:ring-atlas-cyan/10"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-semibold text-atlas-navy"
              >
                Password
              </label>

              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
                className="w-full rounded-xl border border-atlas-mist px-4 py-3 text-sm outline-none transition focus:border-atlas-cyan focus:ring-2 focus:ring-atlas-cyan/10"
              />
            </div>

            {error && (
              <div
                role="alert"
                className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-atlas-cyan px-5 py-3.5 font-semibold text-white transition hover:bg-atlas-deep-cyan disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="mt-7 text-center text-sm text-atlas-slate">
            Don't have an account?{' '}
            <Link
              to="/register"
              className="font-semibold text-atlas-deep-cyan hover:underline"
            >
              Create account
            </Link>
          </p>
        </section>

        <p className="mt-6 text-center text-xs text-atlas-slate">
          Knowledge, beautifully connected.
        </p>
      </div>
    </main>
  )
}
