import { ArrowRight, Menu, X } from "lucide-react";
import { useState } from "react";

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  const linkClass =
    "text-sm text-atlas-slate transition hover:text-atlas-cyan focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-atlas-cyan";

  return (
    <header className="fixed left-0 right-0 top-0 z-50 border-b border-atlas-mist bg-atlas-pearl/90 backdrop-blur-md">
      {" "}
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5"
        aria-label="Main navigation"
      >
        {/* Brand */}
        <a href="/" onClick={closeMenu} className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-atlas-cyan text-lg font-bold text-white">
            A
          </div>

          <span className="font-heading text-xl font-bold tracking-tight">
            AtlasGPT
          </span>
        </a>

        {/* Desktop navigation */}
        <div className="hidden items-center gap-9 md:flex">
          <a href="#features" className={linkClass}>
            Features
          </a>

          <a href="#how-it-works" className={linkClass}>
            How it works
          </a>

          <a href="#about" className={linkClass}>
            About
          </a>
        </div>

        {/* Desktop actions */}
        <div className="hidden items-center gap-5 md:flex">
          <a
            href="/login"
            className="text-sm font-medium text-atlas-navy transition hover:text-atlas-cyan focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-atlas-cyan"
          >
            Sign in
          </a>

          <a
            href="/register"
            className="flex items-center gap-2 rounded-full bg-atlas-navy px-5 py-3 text-sm font-medium text-white transition hover:bg-atlas-deep-cyan focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-atlas-cyan"
          >
            Get started
            <ArrowRight size={16} />
          </a>
        </div>

        {/* Mobile menu button */}
        <button
          type="button"
          aria-label={
            menuOpen ? "Close navigation menu" : "Open navigation menu"
          }
          aria-expanded={menuOpen}
          aria-controls="mobile-navigation"
          onClick={() => setMenuOpen(!menuOpen)}
          className="rounded-lg p-2 text-atlas-navy transition hover:bg-atlas-cloud focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-atlas-cyan md:hidden"
        >
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </nav>
      {/* Mobile navigation */}
      {menuOpen && (
        <div
          id="mobile-navigation"
          className="border-t border-atlas-mist bg-atlas-pearl px-6 py-5 md:hidden"
        >
          <div className="flex flex-col gap-5">
            <a href="#features" onClick={closeMenu} className={linkClass}>
              Features
            </a>

            <a href="#how-it-works" onClick={closeMenu} className={linkClass}>
              How it works
            </a>

            <a href="#about" onClick={closeMenu} className={linkClass}>
              About
            </a>

            <a
              href="/login"
              onClick={closeMenu}
              className="text-sm font-medium text-atlas-navy transition hover:text-atlas-cyan"
            >
              Sign in
            </a>

            <a
              href="/register"
              onClick={closeMenu}
              className="flex items-center justify-center gap-2 rounded-full bg-atlas-navy px-5 py-3 text-sm font-medium text-white transition hover:bg-atlas-deep-cyan"
            >
              Get started
              <ArrowRight size={16} />
            </a>
          </div>
        </div>
      )}
    </header>
  );
}

export default Navbar;
