import { Moon, Sun } from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { useTheme } from '../../hooks/useTheme'

interface ThemeToggleProps {
  className?: string
  showLabel?: boolean
}

export default function ThemeToggle({ className = '', showLabel = false }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme()
  const reduceMotion = useReducedMotion()
  const nextTheme = theme === 'light' ? 'dark' : 'light'

  return (
    <button type="button" onClick={toggleTheme} className={`theme-toggle ${className}`} aria-label={`Switch to ${nextTheme} mode`} title={`Switch to ${nextTheme} mode`}>
      <motion.span className="theme-toggle__icon inline-flex" aria-hidden="true" animate={reduceMotion ? undefined : { rotate: theme === 'light' ? 0 : 180 }} transition={{ duration: .35 }}>
        {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
      </motion.span>
      {showLabel && <span>{theme === 'light' ? 'Dark appearance' : 'Light appearance'}</span>}
    </button>
  )
}
