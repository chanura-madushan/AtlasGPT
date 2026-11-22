
import { useState, type FormEvent } from 'react'
import { ArrowRight } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/api'
import ThemeToggle from '../components/theme/ThemeToggle'

export default function Login() {
  const { login, continueAsGuest } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [guestLoading, setGuestLoading] = useState(false)


  async function handleGuest() {
    setError('')
    setGuestLoading(true)
    try { await continueAsGuest(); navigate('/dashboard') }
    catch (err) { setError(err instanceof ApiError ? err.message : 'Unable to start a guest session.') }
    finally { setGuestLoading(false) }
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
    <main className="atlas-auth">
      <section className="atlas-auth__visual"><a href="/" className="atlas-auth__brand">ATLAS<span>GPT.</span></a><div className="atlas-auth__statement"><span>YOUR KNOWLEDGE, MAPPED</span><h1>Bring your<br/>thinking into<br/><em>focus.</em></h1><p>A quieter workspace for your documents, your questions and the ideas that connect them.</p></div><div className="atlas-auth__coordinates">ATLASGPT / PRIVATE KNOWLEDGE WORKSPACE</div></section>
      <section className="atlas-auth__form-side"><div className="atlas-auth__top"><a href="/" className="atlas-auth__mobile-brand">ATLAS<span style={{color:'#D83995'}}>GPT.</span></a><ThemeToggle/></div><div className="atlas-auth__card"><span className="atlas-overline">WELCOME BACK / 01</span><h2>Good to have you back.</h2><p>Sign in to return to your sources and continue where your thinking left off.</p><form onSubmit={handleSubmit}><label>Email address<input type="email" value={email} onChange={event=>setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" required/></label><label>Password<input type="password" value={password} onChange={event=>setPassword(event.target.value)} placeholder="Your password" autoComplete="current-password" required/></label>{error&&<div className="atlas-auth__error" role="alert">{error}</div>}<button className="atlas-auth__submit" type="submit" disabled={loading}>{loading?'Signing in…':'Sign in to AtlasGPT'} <ArrowRight size={15}/></button></form><div className="atlas-auth__divider">OR</div><button className="atlas-auth__guest" type="button" onClick={handleGuest} disabled={guestLoading||loading}>{guestLoading?'Preparing your guest space…':'Continue as a guest'}</button><p className="atlas-auth__switch">New to AtlasGPT? <Link to="/register">Create an account</Link></p></div><div className="atlas-auth__foot">YOUR SOURCES REMAIN YOURS. YOUR QUESTIONS LEAD THE WAY.</div></section>
    </main>
  )
}
