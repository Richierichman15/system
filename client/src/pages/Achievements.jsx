import { useState, useEffect } from 'react'
import { api } from '../api'
import MainMenuButton from '../components/MainMenuButton'

export default function Achievements() {
  const [achievements, setAchievements] = useState([])
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all') // all, unlocked, locked

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [achievementData, statsData] = await Promise.all([
        api.getAchievements(),
        api.getAchievementStats()
      ])
      setAchievements(achievementData)
      setStats(statsData)
    } catch (e) {
      setError(e.message)
    }
  }

  const getCategoryColor = (category) => {
    const colors = {
      progression: '#3B82F6',
      tasks: '#10B981',
      skills: '#8B5CF6',
      social: '#F59E0B',
      special: '#EF4444'
    }
    return colors[category] || '#6B7280'
  }

  const filteredAchievements = achievements.filter(achievement => {
    if (filter === 'unlocked') return achievement.unlocked
    if (filter === 'locked') return !achievement.unlocked
    return true
  })

  const groupedAchievements = filteredAchievements.reduce((groups, achievement) => {
    const category = achievement.category
    if (!groups[category]) {
      groups[category] = []
    }
    groups[category].push(achievement)
    return groups
  }, {})

  if (!stats) {
    return (
      <div>
        <h1 className="page-title text-glow">Achievements</h1>
        <div className="loading">Loading achievements...</div>
        {error && <p style={{ color: 'tomato' }}>{error}</p>}
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title text-glow">Hall of Achievements</h1>

      {/* Achievement Stats */}
      <div className="achievement-stats">
        <div className="stat-card">
          <div className="stat-icon">
            <i className="fas fa-trophy"></i>
          </div>
          <div className="stat-info">
            <div className="stat-value">{stats.unlocked}</div>
            <div className="stat-label">Unlocked</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <i className="fas fa-medal"></i>
          </div>
          <div className="stat-info">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <i className="fas fa-chart-line"></i>
          </div>
          <div className="stat-info">
            <div className="stat-value">{Math.round(stats.progress * 100)}%</div>
            <div className="stat-label">Progress</div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="achievement-progress-container">
        <div className="achievement-progress-bar">
          <div 
            className="achievement-progress-fill" 
            style={{ width: `${stats.progress * 100}%` }}
          />
        </div>
        <div className="achievement-progress-text">
          {stats.unlocked} of {stats.total} achievements unlocked
        </div>
      </div>

      {/* Filters */}
      <div className="achievement-filters">
        <button 
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          <i className="fas fa-list"></i>
          All ({achievements.length})
        </button>
        <button 
          className={`filter-btn ${filter === 'unlocked' ? 'active' : ''}`}
          onClick={() => setFilter('unlocked')}
        >
          <i className="fas fa-check"></i>
          Unlocked ({stats.unlocked})
        </button>
        <button 
          className={`filter-btn ${filter === 'locked' ? 'active' : ''}`}
          onClick={() => setFilter('locked')}
        >
          <i className="fas fa-lock"></i>
          Locked ({stats.total - stats.unlocked})
        </button>
      </div>

      {/* Achievement Groups */}
      {Object.entries(groupedAchievements).map(([category, categoryAchievements]) => (
        <div key={category} className="achievement-category">
          <div className="category-header">
            <h2 className="category-title" style={{ color: getCategoryColor(category) }}>
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </h2>
            <div className="category-count">
              {categoryAchievements.filter(a => a.unlocked).length} / {categoryAchievements.length}
            </div>
          </div>

          <div className="achievement-grid">
            {categoryAchievements.map(achievement => (
              <div 
                key={achievement.id} 
                className={`achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'}`}
              >
                <div className="achievement-icon-container">
                  <i 
                    className={`fas ${achievement.icon} achievement-icon`}
                    style={{ color: achievement.unlocked ? getCategoryColor(category) : '#6B7280' }}
                  />
                  {achievement.unlocked && (
                    <div className="achievement-unlock-badge">
                      <i className="fas fa-check"></i>
                    </div>
                  )}
                </div>

                <div className="achievement-content">
                  <h3 className="achievement-name">
                    {achievement.unlocked ? achievement.name : '???'}
                  </h3>
                  
                  <p className="achievement-description">
                    {achievement.unlocked ? achievement.description : 'Complete more tasks to unlock this achievement'}
                  </p>

                  {achievement.unlocked && achievement.xp_reward > 0 && (
                    <div className="achievement-reward">
                      <i className="fas fa-star"></i>
                      <span>+{achievement.xp_reward} XP</span>
                    </div>
                  )}

                  {achievement.unlocked && achievement.unlocked_at && (
                    <div className="achievement-unlock-date">
                      Unlocked: {new Date(achievement.unlocked_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {filteredAchievements.length === 0 && (
        <div className="no-achievements">
          <i className="fas fa-medal"></i>
          <h3>No achievements found</h3>
          <p>Complete more tasks to unlock achievements!</p>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}
