import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function Login() {
  const [username, setUsername] = useState('buck')
  const [password, setPassword] = useState('nasty')
  const [step, setStep] = useState('creds') // creds | askLive | askDesires
  const [desires, setDesires] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      setError('')
      const result = await api.login({ username, password })
      if (result.is_new_user) {
        setStep('askLive')
      } else {
        navigate('/')
      }
    } catch (err) {
      setError('Invalid credentials')
    }
  }

  const handleLiveAnswer = (answer) => {
    if (answer === 'yes') {
      setStep('askDesires')
    } else {
      alert('System: Now you will die.')
    }
  }

  const handleSubmitDesires = async () => {
    if (!desires.trim()) return
    // Save desires into profile.goals
    await api.updateProfile({ goals: desires })
    // Trigger AI generation using the desires as goals
    await api.generateTasks({ goals: desires, frequency: 'daily' })
    navigate('/')
  }

  return (
    <div className="container" style={{ maxWidth: 520, marginTop: 60 }}>
      <div className="glass-card" style={{ padding: 24 }}>
        {step === 'creds' && (
          <form onSubmit={handleLogin}>
            <h2 style={{ marginBottom: 16 }}>System Login</h2>
            <div style={{ display: 'grid', gap: 12 }}>
              <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
              {error && <div style={{ color: '#ff6b6b' }}>{error}</div>}
              <button className="button-primary" type="submit">Enter</button>
            </div>
          </form>
        )}

        {step === 'askLive' && (
          <div>
            <h2>System</h2>
            <p>Do you want to live?</p>
            <div style={{ display: 'flex', gap: 12 }}>
              <button className="button-primary" onClick={() => handleLiveAnswer('yes')}>Yes</button>
              <button className="button-secondary" onClick={() => handleLiveAnswer('no')}>No</button>
            </div>
          </div>
        )}

        {step === 'askDesires' && (
          <div>
            <h2>System</h2>
            <p>State your desires.</p>
            <textarea rows={4} value={desires} onChange={e => setDesires(e.target.value)} placeholder="e.g., I want to go to the gym and read more" />
            <div style={{ marginTop: 12 }}>
              <button className="button-primary" onClick={handleSubmitDesires}>Confirm</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


