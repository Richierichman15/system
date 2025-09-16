import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Profile() {
  const [profile, setProfile] = useState({ name: '', goals: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getProfile().then(setProfile).catch((e) => setError(e.message))
  }, [])

  async function save(e) {
    e.preventDefault()
    setSaving(true)
    try {
      const updated = await api.updateProfile(profile)
      setProfile(updated)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h1>Profile</h1>
      {error && <p style={{ color: 'tomato' }}>{error}</p>}
      <form onSubmit={save} style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 420 }}>
        <label>
          Name
          <input value={profile.name || ''} onChange={(e) => setProfile({ ...profile, name: e.target.value })} />
        </label>
        <label>
          Goals
          <textarea rows={4} value={profile.goals || ''} onChange={(e) => setProfile({ ...profile, goals: e.target.value })} />
        </label>
        <button type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
      </form>
    </div>
  )
}

