import { useEffect, useState } from 'react'
import { api } from '../api'
import MainMenuButton from '../components/MainMenuButton'

export default function Settings() {
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
      <h1 className="page-title text-glow">Settings</h1>

      {error && <p style={{ color: 'tomato' }}>{error}</p>}

      <div className="card max-w-xl mx-auto">
        <form onSubmit={save} className="flex flex-col gap-6">
          <div>
            <label className="block mb-2">
              <i className="fas fa-user"></i> Name
            </label>
            <input
              type="text"
              value={profile.name || ''}
              onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              className="w-full bg-black border border-white/30 rounded p-2 text-white"
            />
          </div>

          <div>
            <label className="block mb-2">
              <i className="fas fa-bullseye"></i> Goals
            </label>
            <textarea
              rows={4}
              value={profile.goals || ''}
              onChange={(e) => setProfile({ ...profile, goals: e.target.value })}
              className="w-full bg-black border border-white/30 rounded p-2 text-white"
              placeholder="What are your main goals? This helps generate relevant tasks..."
            />
          </div>

          <div>
            <label className="block mb-2">
              <i className="fas fa-sliders-h"></i> Task Generation
            </label>
            <select 
              className="w-full bg-black border border-white/30 rounded p-2 text-white"
              defaultValue="balanced"
            >
              <option value="easy">Easier Tasks</option>
              <option value="balanced">Balanced</option>
              <option value="challenging">More Challenging</option>
            </select>
          </div>

          <button type="submit" className="menu-button justify-center" disabled={saving}>
            {saving ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <i className="fas fa-save"></i>
                <span>Save Changes</span>
              </>
            )}
          </button>
        </form>
      </div>

      <div className="page-footer">
        <MainMenuButton />
      </div>
    </div>
  )
}