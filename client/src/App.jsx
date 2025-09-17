import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useEffect, Suspense, lazy } from 'react'
import './App.css'
import './styles.css'
import './components/GameplayStyles.css'
import Dashboard from './pages/Dashboard' // Keep Dashboard eager-loaded for fast initial render
import StatsHeader from './components/StatsHeader'
import NotificationSystem from './components/NotificationSystem'
import { api } from './api'

// Lazy load secondary pages for better performance
const Tasks = lazy(() => import('./pages/Tasks'))
const Skills = lazy(() => import('./pages/Skills'))
const WorldMap = lazy(() => import('./pages/WorldMap'))
const Settings = lazy(() => import('./pages/Settings'))
const Achievements = lazy(() => import('./pages/Achievements'))
const Goals = lazy(() => import('./pages/Goals'))

// Loading component for lazy-loaded pages
function LoadingSpinner() {
  return (
    <div className="loading-container">
      <div className="loading-spinner">
        <i className="fas fa-sync-alt fa-spin text-glow"></i>
        <p className="loading-text">Loading...</p>
      </div>
    </div>
  )
}

function Nav() {
  const location = useLocation()
  const showStats = location.pathname !== '/' && location.pathname !== '/settings'

  return (
    <>
      <nav style={{ 
        display: 'flex', 
        gap: 12, 
        padding: '1rem 2rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        background: 'rgba(0, 0, 0, 0.8)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backdropFilter: 'blur(10px)'
      }}>
        {/* <div className="container" style={{ display: 'flex', gap: 24 }}>
          <NavLink to="/" end className="nav-link">
            <i className="fas fa-home"></i> Home
          </NavLink>
          <NavLink to="/tasks" className="nav-link">
            <i className="fas fa-tasks"></i> Quests
          </NavLink>
          <NavLink to="/skills" className="nav-link">
            <i className="fas fa-brain"></i> Skills
          </NavLink>
          <NavLink to="/world" className="nav-link">
            <i className="fas fa-globe"></i> World Map
          </NavLink>
          <NavLink to="/settings" className="nav-link">
            <i className="fas fa-cog"></i> Setings
          </NavLink>
        </div> */}
      </nav>
      {showStats && <StatsHeader />}
    </>
  )
}

export default function App() {
  useEffect(() => {
    // Initialize achievements on app start
    api.initializeAchievements().catch(console.error)
  }, [])

  return (
    <BrowserRouter>
      <div className="bg-grid-pattern min-h-screen">
        <Nav />
        <main className="container">
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/tasks" element={<Tasks />} />
              <Route path="/skills" element={<Skills />} />
              <Route path="/world" element={<WorldMap />} />
              <Route path="/achievements" element={<Achievements />} />
              <Route path="/goals" element={<Goals />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Suspense>
        </main>
        <NotificationSystem />
      </div>
    </BrowserRouter>
  )
}