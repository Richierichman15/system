import MainMenuButton from '../components/MainMenuButton'

export default function WorldMap() {
  const locations = [
    {
      name: 'Training Grounds',
      description: 'Perfect for daily tasks and basic skill development',
      difficulty: 'Easy',
      icon: 'fa-dumbbell',
      unlocked: true
    },
    {
      name: 'Knowledge Library',
      description: 'Study and research challenges await',
      difficulty: 'Medium',
      icon: 'fa-book',
      unlocked: true
    },
    {
      name: 'Challenge Arena',
      description: 'Test your skills against tough objectives',
      difficulty: 'Hard',
      icon: 'fa-trophy',
      unlocked: false
    },
    {
      name: 'Meditation Garden',
      description: 'Focus on mental and spiritual growth',
      difficulty: 'Medium',
      icon: 'fa-leaf',
      unlocked: true
    }
  ]

  return (
    <div>
      <h1 className="page-title text-glow">World Map</h1>
      <p className="text-center mb-8">Explore different areas to find new quests and challenges</p>

      <div className="grid">
        {locations.map(location => (
          <div 
            key={location.name}
            className={`world-location ${!location.unlocked ? 'opacity-50' : ''}`}
          >
            <div className="flex items-center gap-4 mb-4">
              <i className={`fas ${location.icon} text-2xl text-glow`}></i>
              <h3 className="text-glow">{location.name}</h3>
            </div>
            <p>{location.description}</p>
            <div className="flex justify-between items-center mt-4">
              <span className={`
                px-2 py-1 rounded text-sm text-glow
                ${location.difficulty === 'Easy' ? 'text-green-400' :
                  location.difficulty === 'Medium' ? 'text-yellow-400' :
                  'text-red-400'}
              `}>
                {location.difficulty}
              </span>
              {location.unlocked ? (
                <button className="quest-btn">
                  <i className="fas fa-arrow-right"></i> Enter
                </button>
              ) : (
                <button className="quest-btn opacity-50" disabled>
                  <i className="fas fa-lock"></i> Locked
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}