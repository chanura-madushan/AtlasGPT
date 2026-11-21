import { ArrowRight, Menu, X } from 'lucide-react'
import { useState } from 'react'
import ThemeToggle from '../theme/ThemeToggle'

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const closeMenu = () => setMenuOpen(false)
  const linkClass = 'text-sm text-atlas-slate transition hover:text-atlas-cyan focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-atlas-cyan'

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-atlas-mist bg-atlas-pearl/90 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4" aria-label="Main navigation">
        <a href="/" onClick={closeMenu} className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#D83995] text-base font-bold text-white shadow-lg shadow-[#D83995]/20">A</span>
          <span className="font-heading text-lg font-semibold tracking-tight">AtlasGPT<span className="text-[#D83995]">.</span></span>
        </a>
        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className={linkClass}>Features</a>
          <a href="#how-it-works" className={linkClass}>How it works</a>
          <a href="#about" className={linkClass}>About</a>
        </div>
        <div className="hidden items-center gap-4 md:flex">
          <ThemeToggle />
          <a href="/login" className="text-sm font-medium text-atlas-navy transition hover:text-atlas-cyan">Sign in</a>
          <a href="/register" className="inline-flex items-center gap-2 rounded-full bg-atlas-navy px-5 py-2.5 text-sm font-medium text-white transition hover:bg-atlas-deep-cyan">Get started <ArrowRight size={15} /></a>
        </div>
        <button type="button" aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'} aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen(!menuOpen)} className="rounded-lg p-2 text-atlas-navy md:hidden">
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>
      {menuOpen && <div id="mobile-navigation" className="border-t border-atlas-mist bg-atlas-pearl px-6 py-5 md:hidden">
        <div className="flex flex-col items-start gap-5">
          <a href="#features" onClick={closeMenu} className={linkClass}>Features</a>
          <a href="#how-it-works" onClick={closeMenu} className={linkClass}>How it works</a>
          <a href="#about" onClick={closeMenu} className={linkClass}>About</a>
          <ThemeToggle showLabel />
          <a href="/login" onClick={closeMenu} className="text-sm font-medium">Sign in</a>
          <a href="/register" onClick={closeMenu} className="inline-flex items-center gap-2 rounded-full bg-atlas-navy px-5 py-3 text-sm font-medium text-white">Get started <ArrowRight size={15} /></a>
        </div>
      </div>}
    </header>
  )
}
