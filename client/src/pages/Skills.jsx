import { useState, useEffect } from 'react'
import { api } from '../api'
import MainMenuButton from '../components/MainMenuButton'

const SKILL_CATEGORIES = [
  {
    name: 'Physical',
    icon: 'fa-dumbbell',
    skills: [
      { id: 'strength', name: 'Strength', description: 'Raw physical power and lifting capacity' },
      { id: 'endurance', name: 'Endurance', description: 'Stamina and cardiovascular fitness' },
      { id: 'agility', name: 'Agility', description: 'Speed, flexibility, and coordination' }
    ]
  },
  {
    name: 'Mental',
    icon: 'fa-brain',
    skills: [
      { id: 'focus', name: 'Focus', description: 'Concentration and attention span' },
      { id: 'memory', name: 'Memory', description: 'Information retention and recall' },
      { id: 'problem_solving', name: 'Problem Solving', description: 'Analytical and creative thinking' }
    ]
  },
  {
    name: 'Social',
    icon: 'fa-users',
    skills: [
      { id: 'communication', name: 'Communication', description: 'Verbal and written expression' },
      { id: 'leadership', name: 'Leadership', description: 'Influence and team management' },
      { id: 'empathy', name: 'Empathy', description: 'Understanding and connecting with others' }
    ]
  }
]

export default function Skills() {
  const [selectedCategory, setSelectedCategory] = useState('Physical')
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')
  const [allocatingSkill, setAllocatingSkill] = useState(null)

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      const data = await api.getProfile()
      setProfile(data)
    } catch (e) {
      setError(e.message)
    }
  }

  const allocateSkillPoint = async (skillId) => {
    if (!profile || profile.skill_points <= 0 || allocatingSkill) return
    
    setAllocatingSkill(skillId)
    try {
      // Prepare the update data
      const updateData = {}
      updateData[skillId] = (profile[skillId] || 1) + 1
      
      const updatedProfile = await api.updateProfile(updateData)
      setProfile(updatedProfile)
      
      // Show skill increase notification
      window.dispatchEvent(new CustomEvent('game-notification', {
        detail: {
          type: 'skill',
          skill: SKILL_CATEGORIES.flatMap(c => c.skills).find(s => s.id === skillId)?.name,
          amount: 1,
          duration: 2500
        }
      }))
      
    } catch (e) {
      setError(e.message)
    } finally {
      setAllocatingSkill(null)
    }
  }

  const getSkillLevel = (skillId) => {
    return profile?.[skillId] || 1
  }

  const getSkillCost = (currentLevel) => {
    return Math.floor(currentLevel / 3) + 1 // Cost increases every 3 levels
  }

  if (!profile) {
    return (
      <div>
        <h1 className="page-title text-glow">Skills & Abilities</h1>
        <div className="loading">Loading skills...</div>
        {error && <p style={{ color: 'tomato' }}>{error}</p>}
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title text-glow">Skills & Abilities</h1>
      
      <div className="skill-points-display">
        <div className="skill-points-available">
          <i className="fas fa-brain"></i>
          <span>Available Skill Points: <strong className="text-glow">{profile.skill_points}</strong></span>
        </div>
      </div>

      <div className="flex gap-4 justify-center mb-8">
        {SKILL_CATEGORIES.map(category => (
          <button
            key={category.name}
            className={`menu-button ${selectedCategory === category.name ? 'border-blue-500' : ''}`}
            onClick={() => setSelectedCategory(category.name)}
          >
            <i className={`fas ${category.icon}`}></i>
            <span>{category.name}</span>
          </button>
        ))}
      </div>

      <div className="grid">
        {SKILL_CATEGORIES.find(c => c.name === selectedCategory)?.skills.map(skill => {
          const level = getSkillLevel(skill.id)
          const cost = getSkillCost(level)
          const canAfford = profile.skill_points >= cost
          const isAllocating = allocatingSkill === skill.id
          
          return (
            <div key={skill.id} className="skill-card">
              <div className="skill-header">
                <h3 className="skill-name text-glow">{skill.name}</h3>
                <div className="skill-level">Level {level}</div>
              </div>
              
              <p className="skill-description">{skill.description}</p>
              
              <div className="skill-progress">
                <div className="skill-bar">
                  <div 
                    className="skill-fill" 
                    style={{ width: `${Math.min((level - 1) * 10, 100)}%` }}
                  />
                </div>
              </div>
              
              <div className="skill-footer">
                <div className="skill-stats">
                  <span className="current-bonus">
                    Bonus: +{level - 1}
                  </span>
                </div>
                
                <button 
                  onClick={() => allocateSkillPoint(skill.id)}
                  className={`skill-btn ${!canAfford || isAllocating ? 'disabled' : ''}`}
                  disabled={!canAfford || isAllocating}
                >
                  {isAllocating ? (
                    <>
                      <i className="fas fa-spinner fa-spin"></i>
                      Upgrading...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-arrow-up"></i>
                      Upgrade ({cost} {cost === 1 ? 'point' : 'points'})
                    </>
                  )}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}