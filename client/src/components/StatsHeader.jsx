import { useEffect, useState } from 'react'
import { api } from '../api'

export default function StatsHeader() {
  const [profile, setProfile] = useState(null)
  const [activeTasks, setActiveTasks] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    // Load profile and active tasks count
    Promise.all([
      api.getProfile(),
      api.listTasks()
    ]).then(([profileData, tasks]) => {
      setProfile(profileData)
      setActiveTasks(tasks.filter(t => !t.completed).length)
    }).catch(e => setError(e.message))
  }, [])

  if (!profile) return null

  return (
    <div className="stats-header">
      <div className="stats-container">
        <div className="stat-item">
          <i className="fas fa-star text-glow"></i>
          <span>Level {Math.floor(profile.xp / 100) + 1}</span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(profile.xp % 100)}%` }} 
            />
          </div>
          <span className="text-sm">{profile.xp} XP</span>
        </div>

        <div className="stat-item">
          <i className="fas fa-brain text-glow"></i>
          <span>Skill Points</span>
          <div className="stat-value text-glow">{profile.skill_points}</div>
        </div>

        <div className="stat-item">
          <i className="fas fa-tasks text-glow"></i>
          <span>Active Quests</span>
          <div className="stat-value text-glow">{activeTasks}</div>
        </div>
      </div>
    </div>
  )
}
