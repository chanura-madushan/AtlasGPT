
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { ApiError } from '../services/api'
import ThemeToggle from '../components/theme/ThemeToggle'

export default function Register() {
  const { register, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }

    setLoading(true)

    try {
      await register(email, password)
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
        <div className="mb-8 flex items-center justify-between"><Link
          to="/"
          className="font-heading text-2xl font-bold text-atlas-navy"
        >
          AtlasGPT<span className="text-[#D83995]">.</span>
        </Link><ThemeToggle /></div>

        <section className="rounded-3xl border border-atlas-mist bg-white p-8 shadow-xl shadow-atlas-navy/5 sm:p-10">
          <div className="text-center">
            <h1 className="font-heading text-2xl font-bold text-atlas-navy">
              Create your account
            </h1>

            <p className="mt-3 text-sm leading-6 text-atlas-slate">
              Start building your personal knowledge space.
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
                placeholder="At least 8 characters"
                autoComplete="new-password"
                minLength={8}
                required
                className="w-full rounded-xl border border-atlas-mist px-4 py-3 text-sm outline-none transition focus:border-atlas-cyan focus:ring-2 focus:ring-atlas-cyan/10"
              />
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="mb-2 block text-sm font-semibold text-atlas-navy"
              >
                Confirm password
              </label>

              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Re-enter your password"
                autoComplete="new-password"
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
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="mt-7 text-center text-sm text-atlas-slate">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-semibold text-atlas-deep-cyan hover:underline"
            >
              Sign in
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
