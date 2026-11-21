import { ArrowRight, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import ThemeToggle from '../theme/ThemeToggle'

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const reduceMotion = useReducedMotion()
  const closeMenu = () => setMenuOpen(false)
  const linkClass = 'text-sm text-atlas-slate transition hover:text-atlas-cyan focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-atlas-cyan'

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-atlas-mist/80 bg-atlas-pearl/85 backdrop-blur-2xl">
      <nav className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-6 lg:px-12" aria-label="Main navigation">
        <a href="/" onClick={closeMenu} className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#D83995] text-base font-bold text-white shadow-lg shadow-[#D83995]/20">A</span>
          <span className="font-heading text-lg font-semibold tracking-tight">AtlasGPT<span className="text-[#D83995]">.</span></span>
        </a>
        <div className="hidden items-center gap-9 md:flex">
          <a href="/#features" className={linkClass}>Features</a>
          <a href="/#how-it-works" className={linkClass}>How it works</a>
          <a href="/#about" className={linkClass}>About</a>
        </div>
        <div className="hidden items-center gap-5 md:flex">
          <ThemeToggle />
          <a href="/login" className="text-sm font-medium text-atlas-navy transition hover:text-atlas-cyan">Sign in</a>
          <a href="/register" className="inline-flex items-center gap-2 rounded-full bg-atlas-navy px-5 py-2.5 text-sm font-medium text-white transition hover:-translate-y-0.5 hover:bg-atlas-deep-cyan">Get started <ArrowRight size={15} /></a>
        </div>
        <button type="button" aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'} aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen(!menuOpen)} className="rounded-lg p-2 text-atlas-navy md:hidden">
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>
      <AnimatePresence>
        {menuOpen && (
          <motion.div id="mobile-navigation" initial={reduceMotion ? false : { opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={reduceMotion ? undefined : { opacity: 0, height: 0 }} transition={{ duration: reduceMotion ? 0 : .2 }} className="overflow-hidden border-t border-atlas-mist bg-atlas-pearl px-6 md:hidden">
            <div className="flex flex-col items-start gap-5 py-6">
              <a href="/#features" onClick={closeMenu} className={linkClass}>Features</a>
              <a href="/#how-it-works" onClick={closeMenu} className={linkClass}>How it works</a>
              <a href="/#about" onClick={closeMenu} className={linkClass}>About</a>
              <ThemeToggle showLabel />
              <a href="/login" onClick={closeMenu} className="text-sm font-medium">Sign in</a>
              <a href="/register" onClick={closeMenu} className="inline-flex items-center gap-2 rounded-full bg-atlas-navy px-5 py-3 text-sm font-medium text-white">Get started <ArrowRight size={15} /></a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
