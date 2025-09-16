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
      setTasks(data)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  async function completeTask(id) {
    try {
      await api.completeTask(id)
      loadTasks()
    } catch (e) {
      setError(e.message)
    }
  }

  const [isGenerating, setIsGenerating] = useState(false)

  async function generateTasks() {
    try {
      setIsGenerating(true)
      await api.generateTasks({
        goals: 'Improve productivity and skills',
        frequency: 'daily'
      })
      loadTasks()
    } catch (e) {
      setError(e.message)
    } finally {
      setIsGenerating(false)
    }
  }

  const filteredTasks = tasks.filter(task => {
    if (filter === 'active') return !task.completed
    if (filter === 'completed') return task.completed
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
        {filteredTasks.map(task => (
          <div key={task.id} className="quest-card">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold">{task.title}</h3>
              <span className="px-3 py-1 rounded-full text-sm border border-white/30">
                {task.frequency}
              </span>
            </div>
            
            <p className="text-white/80 mb-6">{task.description}</p>
            
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="text-sm text-white/60">Reward:</span>
                <span className="text-glow">{task.xp} XP</span>
              </div>
              
              {!task.completed ? (
                <button 
                  onClick={() => completeTask(task.id)}
                  className="quest-btn"
                >
                  Complete
                </button>
              ) : (
                <span className="text-green-400 text-glow">✓ Completed</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col items-center mt-8">
        <div className="flex gap-4 mb-4">
          <button 
            onClick={generateTasks} 
            className="menu-button"
            disabled={isGenerating}
          >
            <span>{isGenerating ? 'Generating...' : 'Generate New Quests'}</span>
            <i className={`fas ${isGenerating ? 'fa-spinner fa-spin' : 'fa-magic'}`}></i>
          </button>
        </div>
      </div>

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}