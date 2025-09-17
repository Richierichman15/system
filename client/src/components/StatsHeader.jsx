import { useEffect, useState } from 'react'
import { api } from '../api'

export default function StatsHeader({ onProfileUpdate }) {
  const [profile, setProfile] = useState(null)
  const [activeTasks, setActiveTasks] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [profileData, tasks] = await Promise.all([
        api.getProfile(),
        api.listTasks()
      ])
      setProfile(profileData)
      setActiveTasks(tasks.filter(t => !t.completed).length)
      
      // Notify parent component of profile update
      if (onProfileUpdate) {
        onProfileUpdate(profileData)
      }
    } catch (e) {
      setError(e.message)
    }
  }

  // Use backend's level calculation - matches the new leveling system
  const xpForLevel = (level) => {
    if (level <= 1) return 0
    return Math.pow(level - 1, 2) * 50
  }

  const getProgress = () => {
    if (!profile) return { current: 0, needed: 50, progress: 0, level: 1 }
    
    // Always use the level from backend (it's calculated server-side with the correct formula)
    const currentLevel = profile.level || 1
    const currentLevelXP = xpForLevel(currentLevel)
    const nextLevelXP = xpForLevel(currentLevel + 1)
    const progressXP = profile.xp - currentLevelXP
    const neededXP = nextLevelXP - currentLevelXP
    const progress = neededXP > 0 ? (progressXP / neededXP) * 100 : 0

    return {
      current: progressXP,
      needed: neededXP,
      progress: Math.min(Math.max(progress, 0), 100),
      level: currentLevel
    }
  }

  if (!profile) return null

  const { current, needed, progress, level } = getProgress()

  return (
    <div className="stats-header">
      <div className="stats-container">
        <div className="stat-item level-stat">
          <i className="fas fa-star text-glow"></i>
          <div className="level-info">
            <span className="level-text">Level {level}</span>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }} 
              />
            </div>
            <span className="xp-text">{current}/{needed} XP</span>
          </div>
        </div>

        <div className="stat-item">
          <i className="fas fa-gem text-glow"></i>
          <div className="stat-info">
            <span>Total XP</span>
            <div className="stat-value text-glow">{profile.xp.toLocaleString()}</div>
          </div>
        </div>

        <div className="stat-item">
          <i className="fas fa-brain text-glow"></i>
          <div className="stat-info">
            <span>Skill Points</span>
            <div className="stat-value text-glow">{profile.skill_points}</div>
          </div>
        </div>

        <div className="stat-item">
          <i className="fas fa-tasks text-glow"></i>
          <div className="stat-info">
            <span>Active Quests</span>
            <div className="stat-value text-glow">{activeTasks}</div>
          </div>
        </div>
      </div>
      
      {error && <div className="error-text">{error}</div>}
    </div>
  )
}
