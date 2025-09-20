import { useEffect, useState } from 'react'
import { api } from '../api'
import MainMenuButton from '../components/MainMenuButton'

export default function Goals() {
  const [goals, setGoals] = useState([])
  const [categories, setCategories] = useState([])
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    category: 'personal',
    priority: 'medium',
    target_date: ''
  })
  const [error, setError] = useState('')

  useEffect(() => {
    loadGoals()
    loadCategories()
  }, [])

  async function loadGoals() {
    try {
      const data = await api.getGoals()
      setGoals(data)
    } catch (e) {
      setError(e.message)
    }
  }

  async function loadCategories() {
    try {
      const data = await api.getGoalCategories()
      setCategories(data.categories)
    } catch (e) {
      console.error('Error loading categories:', e)
    }
  }

  async function createGoal(e) {
    e.preventDefault()
    try {
      await api.createGoal(newGoal)
      setNewGoal({
        title: '',
        description: '',
        category: 'personal',
        priority: 'medium',
        target_date: ''
      })
      setShowCreateForm(false)
      loadGoals()
    } catch (e) {
      setError(e.message)
    }
  }

  async function updateGoalProgress(goalId, progress) {
    try {
      await api.updateGoalProgress(goalId, { progress })
      loadGoals()
    } catch (e) {
      setError(e.message)
    }
  }

  async function deleteGoal(goalId) {
    if (!confirm('Are you sure you want to delete this goal?')) return
    
    try {
      await api.deleteGoal(goalId)
      loadGoals()
    } catch (e) {
      setError(e.message)
    }
  }

  async function completeGoal(goalId) {
    if (!confirm('Are you sure you want to mark this goal as complete? This will award XP!')) return
    
    try {
      const result = await api.completeGoal(goalId)
      loadGoals()
      
      // Show XP gained notification
      if (result.xp_gained) {
        window.dispatchEvent(new CustomEvent('game-notification', {
          detail: {
            type: 'xp',
            amount: result.xp_gained,
            duration: 3000
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
      
      // Show goal completion message
      window.dispatchEvent(new CustomEvent('game-notification', {
        detail: {
          type: 'success',
          message: result.message,
          duration: 4000
        }
      }))
      
    } catch (e) {
      setError(e.message)
    }
  }

  const getPriorityColor = (priority) => {
    const colors = {
      critical: 'text-red-400',
      high: 'text-orange-400',
      medium: 'text-yellow-400',
      low: 'text-green-400'
    }
    return colors[priority] || 'text-white'
  }

  const getCategoryIcon = (category) => {
    const icons = {
      career: 'fa-briefcase',
      health: 'fa-heart',
      personal: 'fa-user-plus',
      financial: 'fa-dollar-sign',
      learning: 'fa-graduation-cap',
      relationships: 'fa-users'
    }
    return icons[category] || 'fa-target'
  }

  return (
    <div>
      <h1 className="page-title text-glow">Goals & Objectives</h1>

      {error && <p style={{ color: 'tomato' }}>{error}</p>}

      <div className="flex justify-center mb-8">
        <button 
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="menu-button"
        >
          <i className="fas fa-plus"></i>
          <span>Create New Goal</span>
        </button>
      </div>

      {showCreateForm && (
        <div className="card max-w-2xl mx-auto mb-8">
          <form onSubmit={createGoal} className="flex flex-col gap-4">
            <div>
              <label className="block mb-2">
                <i className="fas fa-bullseye"></i> Goal Title
              </label>
              <input
                type="text"
                value={newGoal.title}
                onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                className="w-full bg-black border border-white/30 rounded p-2 text-white"
                placeholder="What do you want to achieve?"
                required
              />
            </div>

            <div>
              <label className="block mb-2">
                <i className="fas fa-align-left"></i> Description
              </label>
              <textarea
                rows={3}
                value={newGoal.description}
                onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })}
                className="w-full bg-black border border-white/30 rounded p-2 text-white"
                placeholder="Describe your goal in detail..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block mb-2">
                  <i className="fas fa-tag"></i> Category
                </label>
                <select
                  value={newGoal.category}
                  onChange={(e) => setNewGoal({ ...newGoal, category: e.target.value })}
                  className="w-full bg-black border border-white/30 rounded p-2 text-white"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block mb-2">
                  <i className="fas fa-exclamation"></i> Priority
                </label>
                <select
                  value={newGoal.priority}
                  onChange={(e) => setNewGoal({ ...newGoal, priority: e.target.value })}
                  className="w-full bg-black border border-white/30 rounded p-2 text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div>
                <label className="block mb-2">
                  <i className="fas fa-calendar"></i> Target Date
                </label>
                <input
                  type="date"
                  value={newGoal.target_date}
                  onChange={(e) => setNewGoal({ ...newGoal, target_date: e.target.value })}
                  className="w-full bg-black border border-white/30 rounded p-2 text-white"
                />
              </div>
            </div>

            <div className="flex gap-4">
              <button type="submit" className="menu-button flex-1">
                <i className="fas fa-save"></i>
                <span>Create Goal</span>
              </button>
              <button 
                type="button" 
                onClick={() => setShowCreateForm(false)}
                className="quest-btn"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid">
        {goals.map(goal => (
          <div key={goal.id} className={`quest-card ${goal.completed ? 'opacity-75' : ''}`}>
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-2">
                <i className={`fas ${getCategoryIcon(goal.category)} text-glow`}></i>
                <h3 className="text-xl font-bold">
                  {goal.title}
                  {goal.completed && <span className="ml-2 text-green-400">✓</span>}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                {goal.completed && (
                  <span className="px-2 py-1 rounded text-sm text-green-400 bg-green-400/20">
                    COMPLETED
                  </span>
                )}
                <span className={`px-2 py-1 rounded text-sm ${getPriorityColor(goal.priority)}`}>
                  {goal.priority.toUpperCase()}
                </span>
                <button 
                  onClick={() => deleteGoal(goal.id)}
                  className="text-red-400 hover:text-red-300"
                >
                  <i className="fas fa-trash"></i>
                </button>
              </div>
            </div>

            {goal.description && (
              <p className="text-white/80 mb-4">{goal.description}</p>
            )}

            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm">Progress</span>
                <span className="text-sm">{Math.round(goal.progress * 100)}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${goal.progress * 100}%` }}
                />
              </div>
            </div>

            <div className="flex items-center gap-4 mb-4">
              <input
                type="range"
                min="0"
                max="100"
                value={goal.progress * 100}
                onChange={(e) => updateGoalProgress(goal.id, e.target.value / 100)}
                className="flex-1"
                disabled={goal.completed}
              />
              <span className="text-sm text-white/60">
                {goal.target_date && new Date(goal.target_date).toLocaleDateString()}
                {goal.completed && goal.completed_at && (
                  <span className="block text-green-400">
                    Completed: {new Date(goal.completed_at).toLocaleDateString()}
                  </span>
                )}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <div className="text-sm text-white/60">
                Category: {goal.category} • Priority: {goal.priority}
              </div>
              <div className="flex gap-2">
                {goal.progress >= 0.8 && !goal.completed && (
                  <button 
                    onClick={() => completeGoal(goal.id)}
                    className="quest-btn complete-btn"
                    title="Complete Goal & Earn XP"
                  >
                    <i className="fas fa-trophy"></i>
                    Complete
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {goals.length === 0 && !showCreateForm && (
        <div className="text-center py-10">
          <p className="text-xl text-white/60 mb-4">No goals set yet</p>
          <p className="text-white/40">Create your first goal to get AI-generated tasks that align with your objectives!</p>
        </div>
      )}

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}
