import { ArrowRight, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import ThemeToggle from '../theme/ThemeToggle'

export default function Navbar() {
  const [menuOpen,setMenuOpen]=useState(false)
  const reduceMotion=useReducedMotion()
  const closeMenu=()=>setMenuOpen(false)
  return <header className="atlas-nav"><nav className="atlas-nav__inner" aria-label="Main navigation">
    <a href="/" className="atlas-brand"><span className="atlas-brand__symbol">A</span><span>ATLAS<span>GPT</span><i>.</i></span></a>
    <div className="atlas-nav__links"><a href="/#features">The workspace</a><a href="/#method">How it works</a><a href="/login">Sign in</a></div>
    <div className="atlas-nav__actions"><ThemeToggle/><a href="/register" className="atlas-nav__cta">Get started <ArrowRight size={14}/></a><button className="atlas-nav__menu" aria-label={menuOpen?'Close menu':'Open menu'} aria-expanded={menuOpen} onClick={()=>setMenuOpen(!menuOpen)}>{menuOpen?<X size={20}/>:<Menu size={20}/>}</button></div>
  </nav><AnimatePresence>{menuOpen&&<motion.div initial={reduceMotion?false:{opacity:0,height:0}} animate={{opacity:1,height:'auto'}} exit={{opacity:0,height:0}} className="atlas-nav__mobile"><a href="/#features" onClick={closeMenu}>The workspace</a><a href="/#method" onClick={closeMenu}>How it works</a><a href="/login" onClick={closeMenu}>Sign in</a><a href="/register" onClick={closeMenu}>Create account</a></motion.div>}</AnimatePresence></header>
}
