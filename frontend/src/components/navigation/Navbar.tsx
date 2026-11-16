
import { ArrowRight, Menu, X } from 'lucide-react'
import { useState } from 'react'

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="relative z-50 border-b border-atlas-mist bg-atlas-pearl/90 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        {/* Brand */}
        <a href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-atlas-cyan text-lg font-bold text-white">
            A
          </div>

          <span className="font-heading text-xl font-bold tracking-tight">
            AtlasGPT
          </span>
        </a>

        {/* Desktop navigation */}
        <div className="hidden items-center gap-9 md:flex">
          <a href="#features" className="text-sm text-atlas-slate transition hover:text-atlas-cyan">
            Features
          </a>

          <a href="#how-it-works" className="text-sm text-atlas-slate transition hover:text-atlas-cyan">
            How it works
          </a>

          <a href="#about" className="text-sm text-atlas-slate transition hover:text-atlas-cyan">
            About
          </a>
        </div>

        {/* Desktop actions */}
        <div className="hidden items-center gap-5 md:flex">
          <a href="/login" className="text-sm font-medium text-atlas-navy transition hover:text-atlas-cyan">
            Sign in
          </a>

          <a
            href="/register"
            className="flex items-center gap-2 rounded-full bg-atlas-navy px-5 py-3 text-sm font-medium text-white transition hover:bg-atlas-deep-cyan"
          >
            Get started
            <ArrowRight size={16} />
          </a>
        </div>

        {/* Mobile menu button */}
        <button
          type="button"
          aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen(!menuOpen)}
          className="rounded-lg p-2 text-atlas-navy hover:bg-atlas-cloud md:hidden"
        >
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </nav>

      {/* Mobile navigation */}
      {menuOpen && (
        <div className="border-t border-atlas-mist bg-atlas-pearl px-6 py-5 md:hidden">
          <div className="flex flex-col gap-5">
            <a href="#features" onClick={() => setMenuOpen(false)} className="text-sm text-atlas-slate">
              Features
            </a>

            <a href="#how-it-works" onClick={() => setMenuOpen(false)} className="text-sm text-atlas-slate">
              How it works
            </a>

            <a href="#about" onClick={() => setMenuOpen(false)} className="text-sm text-atlas-slate">
              About
            </a>

            <a href="/login" className="text-sm font-medium text-atlas-navy">
              Sign in
            </a>

            <a
              href="/register"
              className="flex items-center justify-center gap-2 rounded-full bg-atlas-navy px-5 py-3 text-sm font-medium text-white"
            >
              Get started
              <ArrowRight size={16} />
            </a>
          </div>
        </div>
      )}
    </header>
  )
}

export default Navbar
