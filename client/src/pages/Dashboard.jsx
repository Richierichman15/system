import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getProfile().then(setProfile).catch((e) => setError(e.message))
  }, [])

  return (
    <div className="start-menu">
      <div className="menu-container">
        <h1 className="page-title text-glow">SYSTEM</h1>
        {profile && (
          <h2 className="welcome-text text-glow">Welcome, {profile.name}</h2>
        )}

        {error && <p style={{ color: 'tomato' }}>{error}</p>}

        <div className="menu-options">
          <Link to="/tasks" className="menu-button">
            <i className="fas fa-play text-glow"></i>
            <span>Start Quest</span>
          </Link>

          <Link to="/skills" className="menu-button">
            <i className="fas fa-brain text-glow"></i>
            <span>Skills & Abilities</span>
          </Link>

          <Link to="/world" className="menu-button">
            <i className="fas fa-globe text-glow"></i>
            <span>World Map</span>
          </Link>

          <Link to="/settings" className="menu-button">
            <i className="fas fa-cog text-glow"></i>
            <span>Settings</span>
          </Link>
        </div>

        <div className="menu-footer">
          <div className="player-stats">
            {profile && (
              <>
                <div className="stat-block">
                  <span className="stat-label">Level</span>
                  <span className="stat-value text-glow">
                    {Math.floor(profile.xp / 100) + 1}
                  </span>
                </div>
                <div className="stat-block">
                  <span className="stat-label">XP</span>
                  <span className="stat-value text-glow">{profile.xp}</span>
                </div>
                <div className="stat-block">
                  <span className="stat-label">Skill Points</span>
                  <span className="stat-value text-glow">
                    {profile.skill_points}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}