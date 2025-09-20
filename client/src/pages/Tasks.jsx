import { useEffect, useState } from 'react'
import { api } from '../api'
import MainMenuButton from '../components/MainMenuButton'

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState('')

  async function loadTasks() {
    try {
      const data = await api.listTasks()
      console.log('Loaded tasks:', data.length, 'tasks')
      console.log('Latest task:', data[0])
      setTasks(data)
    } catch (e) {
      setError(e.message)
      console.error('Error loading tasks:', e)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  async function completeTask(id) {
    try {
      const result = await api.completeTask(id)
      loadTasks()
      
      // Show visual feedback
      if (result.xp_gained) {
        window.dispatchEvent(new CustomEvent('game-notification', {
          detail: {
            type: 'xp',
            amount: result.xp_gained,
            duration: 2000
          }
        }))
      }
      
      // Show level up notification
      if (result.level_up) {
        window.dispatchEvent(new CustomEvent('game-notification', {
          detail: {
            type: 'level-up',
            newLevel: result.new_level,
            oldLevel: result.old_level,
            duration: 4000
          }
        }))
      }
      
      // Show skill bonuses
      if (result.skill_bonuses && Object.keys(result.skill_bonuses).length > 0) {
        Object.entries(result.skill_bonuses).forEach(([skill, amount]) => {
          window.dispatchEvent(new CustomEvent('game-notification', {
            detail: {
              type: 'skill',
              skill: skill.charAt(0).toUpperCase() + skill.slice(1),
              amount,
              duration: 2500
            }
          }))
        })
      }
      
      // Show achievement notifications
      if (result.achievements && result.achievements.length > 0) {
        result.achievements.forEach(achievement => {
          setTimeout(() => {
            window.dispatchEvent(new CustomEvent('game-notification', {
              detail: {
                type: 'achievement',
                name: achievement.name,
                description: achievement.description,
                icon: achievement.icon,
                duration: 5000
              }
            }))
          }, 1000) // Delay achievements so they don't overlap with other notifications
        })
      }
      
    } catch (e) {
      setError(e.message)
    }
  }

  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('general')
  const [useAdvancedAI, setUseAdvancedAI] = useState(true)

  async function generateTasks() {
    try {
      setIsGenerating(true)
      // Get user's actual goals from profile
      const profile = await api.getProfile()
      const userGoals = profile.goals || 'Improve productivity and skills'
      
      // Add variety for different generations
      const timestamp = Date.now()
      const varietyWords = ['focus on', 'work towards', 'achieve', 'improve', 'develop']
      const randomWord = varietyWords[Math.floor(Math.random() * varietyWords.length)]
      
      const goalText = `${randomWord} ${userGoals} [${timestamp}]`
      console.log('Generating tasks with goals:', goalText)
      
      let result
      if (useAdvancedAI) {
        result = await api.generateTasksAdvanced({
          goals: goalText,
          frequency: 'daily',
          category: selectedCategory,
          preferences: {
            preferred_model_type: selectedCategory === 'creative' ? 'creative' : 
                                 selectedCategory === 'work' || selectedCategory === 'learning' ? 'analytical' : 'balanced'
          }
        })
      } else {
        result = await api.generateTasks({
          goals: goalText,
          frequency: 'daily'
        })
      }
      
      console.log('Generated tasks:', result)
      console.log('Reloading tasks...')
      await loadTasks()
      console.log('Tasks reloaded')
    } catch (e) {
      setError(e.message)
    } finally {
      setIsGenerating(false)
    }
  }

  async function submitTaskFeedback(taskId, rating, completed, completionTime = null) {
    try {
      await api.submitTaskFeedback(taskId, rating, completed, completionTime)
      console.log('Feedback submitted for task', taskId)
    } catch (e) {
      console.error('Error submitting feedback:', e)
    }
  }

  async function toggleActive(id) {
    try {
      await api.toggleTaskActive(id)
      loadTasks()
    } catch (e) {
      setError(e.message)
    }
  }

  async function deleteTask(id) {
    if (!confirm('Are you sure you want to delete this quest? This action cannot be undone.')) {
      return
    }
    
    try {
      await api.deleteTask(id)
      loadTasks()
      
      // Show deletion notification
      window.dispatchEvent(new CustomEvent('game-notification', {
        detail: {
          type: 'info',
          message: 'Quest deleted successfully',
          duration: 2000
        }
      }))
    } catch (e) {
      setError(e.message)
    }
  }

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return !task.completed // Show all incomplete tasks
    if (filter === 'active') return !task.completed && task.active // Show only active incomplete tasks
    if (filter === 'completed') return task.completed // Show only completed tasks
    return true
  })

  return (
    <div>
      <h1 className="page-title text-glow">Available Quests</h1>

      {error && <p style={{ color: 'tomato' }}>{error}</p>}

      <div className="flex justify-center gap-4 mb-8">
        <button 
          className={`menu-button ${filter === 'all' ? 'border-blue-500' : ''}`}
          onClick={() => setFilter('all')}
        >
          <i className="fas fa-list"></i>
          <span>All Quests</span>
        </button>
        <button 
          className={`menu-button ${filter === 'active' ? 'border-blue-500' : ''}`}
          onClick={() => setFilter('active')}
        >
          <i className="fas fa-running"></i>
          <span>Active</span>
        </button>
        <button 
          className={`menu-button ${filter === 'completed' ? 'border-blue-500' : ''}`}
          onClick={() => setFilter('completed')}
        >
          <i className="fas fa-check"></i>
          <span>Completed</span>
        </button>
      </div>

      <div className="grid">
        {filteredTasks.map(task => {
          const difficultyColors = {
            easy: '#10B981',
            medium: '#F59E0B', 
            hard: '#EF4444',
            expert: '#8B5CF6'
          }
          
          const categoryIcons = {
            work: 'fa-briefcase',
            fitness: 'fa-dumbbell',
            learning: 'fa-book',
            social: 'fa-users',
            personal: 'fa-heart',
            general: 'fa-star'
          }
          
          return (
            <div key={task.id} className="quest-card">
              <div className="quest-header">
                <div className="quest-title-section">
                  <h3 className="quest-title">{task.title}</h3>
                  <div className="quest-tags">
                    <span className="frequency-tag">{task.frequency}</span>
                    {task.difficulty && (
                      <span 
                        className="difficulty-tag"
                        style={{ 
                          borderColor: difficultyColors[task.difficulty],
                          color: difficultyColors[task.difficulty]
                        }}
                      >
                        {task.difficulty.charAt(0).toUpperCase() + task.difficulty.slice(1)}
                      </span>
                    )}
                    {task.category && (
                      <span className="category-tag">
                        <i className={`fas ${categoryIcons[task.category] || 'fa-star'}`}></i>
                        {task.category}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <p className="quest-description">{task.description}</p>
              
              <div className="quest-footer">
                <div className="quest-reward">
                  <span className="reward-label">Reward:</span>
                  <span className="reward-value text-glow">{task.xp} XP</span>
                  {task.is_recurring && (
                    <span className="recurring-indicator">
                      <i className="fas fa-sync-alt"></i>
                      Recurring
                    </span>
                  )}
                </div>
                
                {!task.completed ? (
                  <div className="quest-actions">
                    <button 
                      onClick={() => toggleActive(task.id)}
                      className={`quest-btn ${task.active ? 'active-btn' : 'inactive-btn'}`}
                    >
                      <i className={`fas ${task.active ? 'fa-pause' : 'fa-play'}`}></i>
                      {task.active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button 
                      onClick={() => completeTask(task.id)}
                      className="quest-btn complete-btn"
                      disabled={!task.active}
                    >
                      <i className="fas fa-check"></i>
                      Complete
                    </button>
                    <button 
                      onClick={() => deleteTask(task.id)}
                      className="quest-btn delete-btn"
                      title="Delete Quest"
                    >
                      <i className="fas fa-trash"></i>
                      Delete
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="completed-indicator">
                      <i className="fas fa-check-circle"></i>
                      Completed
                      {task.completed_at && (
                        <span className="completion-time">
                          {new Date(task.completed_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <div className="quest-actions">
                      <button 
                        onClick={() => deleteTask(task.id)}
                        className="quest-btn delete-btn"
                        title="Delete Quest"
                      >
                        <i className="fas fa-trash"></i>
                        Delete
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="flex flex-col items-center mt-8">
        <div className="glass-card" style={{ padding: '20px', marginBottom: '20px', maxWidth: '600px' }}>
          <h3 style={{ marginBottom: '16px', textAlign: 'center' }}>AI Quest Generation</h3>
          
          <div style={{ display: 'grid', gap: '12px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <label style={{ minWidth: '120px' }}>AI Mode:</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  className={`button-${useAdvancedAI ? 'primary' : 'secondary'}`}
                  onClick={() => setUseAdvancedAI(true)}
                  style={{ padding: '6px 12px', fontSize: '14px' }}
                >
                  Advanced AI
                </button>
                <button 
                  className={`button-${!useAdvancedAI ? 'primary' : 'secondary'}`}
                  onClick={() => setUseAdvancedAI(false)}
                  style={{ padding: '6px 12px', fontSize: '14px' }}
                >
                  Standard
                </button>
              </div>
            </div>
            
            {useAdvancedAI && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <label style={{ minWidth: '120px' }}>Category:</label>
                <select 
                  value={selectedCategory} 
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  style={{ padding: '6px', borderRadius: '4px', border: '1px solid #333', background: '#1a1a1a', color: 'white' }}
                >
                  <option value="general">General</option>
                  <option value="fitness">Fitness & Health</option>
                  <option value="learning">Learning & Education</option>
                  <option value="work">Work & Career</option>
                  <option value="personal">Personal Development</option>
                  <option value="creative">Creative Projects</option>
                  <option value="social">Social & Relationships</option>
                </select>
              </div>
            )}
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button 
              onClick={generateTasks} 
              className="menu-button"
              disabled={isGenerating}
            >
              <span>{isGenerating ? 'Generating...' : `Generate ${useAdvancedAI ? 'Specialized' : 'Standard'} Quests`}</span>
              <i className={`fas ${isGenerating ? 'fa-spinner fa-spin' : useAdvancedAI ? 'fa-brain' : 'fa-magic'}`}></i>
            </button>
          </div>
          
          {useAdvancedAI && (
            <div style={{ fontSize: '12px', textAlign: 'center', marginTop: '12px', opacity: '0.7' }}>
              Using specialized AI model for {selectedCategory} tasks with custom learning
            </div>
          )}
        </div>
      </div>

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}