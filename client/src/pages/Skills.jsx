import { useState } from 'react'
import MainMenuButton from '../components/MainMenuButton'

const SKILL_CATEGORIES = [
  {
    name: 'Physical',
    icon: 'fa-dumbbell',
    skills: ['Strength', 'Endurance', 'Agility']
  },
  {
    name: 'Mental',
    icon: 'fa-brain',
    skills: ['Focus', 'Memory', 'Problem Solving']
  },
  {
    name: 'Social',
    icon: 'fa-users',
    skills: ['Communication', 'Leadership', 'Empathy']
  }
]

export default function Skills() {
  const [selectedCategory, setSelectedCategory] = useState('Physical')

  return (
    <div>
      <h1 className="page-title text-glow">Skills & Abilities</h1>

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
        {SKILL_CATEGORIES.find(c => c.name === selectedCategory)?.skills.map(skill => (
          <div key={skill} className="card">
            <h3 className="text-glow">{skill}</h3>
            <div className="stat-value text-glow">Lv. 1</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: '30%' }} />
            </div>
            <p>Progress: 30/100 XP</p>
            <button className="quest-btn mt-4">
              Level Up (2 points)
            </button>
          </div>
        ))}
      </div>

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}