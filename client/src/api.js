const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function http(method, path, body) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${method} ${path} failed: ${res.status} ${text}`)
  }
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return res.text()
}

export const api = {
  health: () => http('GET', '/health'),
  getProfile: () => http('GET', '/profile/'),
  updateProfile: (data) => http('PATCH', '/profile/', data),
  listTasks: () => http('GET', '/tasks/'),
  createTask: (task) => http('POST', '/tasks/', task),
  completeTask: (id) => http('PATCH', `/tasks/${id}/complete`),
  generateTasks: (payload) => http('POST', '/ai/generate', payload),
}
