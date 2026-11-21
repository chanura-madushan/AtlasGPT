import { useEffect, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'

export default function RouteTransition({ children }: { children: ReactNode }) {
  const location = useLocation()

  useEffect(() => {
    const root = document.getElementById('route-content')
    if (!root) return

    root.classList.remove('route-enter')
    // Force a style boundary so repeated navigations replay the entrance.
    void root.offsetWidth
    root.classList.add('route-enter')
  }, [location.pathname])

  return <div id="route-content" className="route-enter">{children}</div>
}
