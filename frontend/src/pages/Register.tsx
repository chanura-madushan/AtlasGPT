
import { useState, type FormEvent } from 'react'
import { ArrowRight } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../services/api'
import ThemeToggle from '../components/theme/ThemeToggle'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)


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
    <main className="atlas-auth">
      <section className="atlas-auth__visual"><a href="/" className="atlas-auth__brand">ATLAS<span>GPT.</span></a><div className="atlas-auth__statement"><span>A SPACE FOR YOUR CURIOSITY</span><h1>Collect ideas.<br/>Find the<br/><em>connections.</em></h1><p>Bring your documents into one place and turn them into a knowledge space you can explore.</p></div><div className="atlas-auth__coordinates">ATLASGPT / PRIVATE KNOWLEDGE WORKSPACE</div></section>
      <section className="atlas-auth__form-side"><div className="atlas-auth__top"><a href="/" className="atlas-auth__mobile-brand">ATLAS<span style={{color:'#D83995'}}>GPT.</span></a><ThemeToggle/></div><div className="atlas-auth__card"><span className="atlas-overline">CREATE YOUR SPACE / 01</span><h2>Start with your sources.</h2><p>Create an account to keep your documents and conversations together.</p><form onSubmit={handleSubmit}><label>Email address<input type="email" value={email} onChange={event=>setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" required/></label><label>Password<input type="password" value={password} onChange={event=>setPassword(event.target.value)} placeholder="At least 8 characters" autoComplete="new-password" minLength={8} required/></label><label>Confirm password<input type="password" value={confirmPassword} onChange={event=>setConfirmPassword(event.target.value)} placeholder="Enter your password again" autoComplete="new-password" required/></label>{error&&<div className="atlas-auth__error" role="alert">{error}</div>}<button className="atlas-auth__submit" type="submit" disabled={loading}>{loading?'Creating your account…':'Create your account'} <ArrowRight size={15}/></button></form><p className="atlas-auth__switch">Already have an account? <Link to="/login">Sign in</Link></p></div><div className="atlas-auth__foot">YOUR SOURCES REMAIN YOURS. YOUR QUESTIONS LEAD THE WAY.</div></section>
    </main>
  )
}
