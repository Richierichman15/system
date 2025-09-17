import axios from 'axios'

// Environment-aware API URL
const API_URL = import.meta.env.VITE_API_URL || 
  (window.location.hostname === 'localhost' ? 'http://localhost:8000' : '/api')

// Simple in-memory cache for API responses
const cache = new Map()
const CACHE_DURATION = 30000 // 30 seconds

function getCacheKey(url, params = {}) {
  return `${url}?${JSON.stringify(params)}`
}

function getCached(key) {
  const cached = cache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data
  }
  cache.delete(key)
  return null
}

function setCache(key, data) {
  cache.set(key, { data, timestamp: Date.now() })
}

// Enhanced axios instance with caching
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const api = {
  // Profile endpoints with caching
  async getProfile() {
    const cacheKey = getCacheKey('/profile')
    const cached = getCached(cacheKey)
    if (cached) return cached

    const response = await apiClient.get('/profile')
    setCache(cacheKey, response.data)
    return response.data
  },

  async updateProfile(data) {
    const response = await axios.patch(`${API_URL}/profile`, data)
    return response.data
  },

  // Task endpoints
  async listTasks(params = {}) {
    const response = await axios.get(`${API_URL}/tasks`, { params })
    return response.data
  },

  async createTask(task) {
    const response = await axios.post(`${API_URL}/tasks`, task)
    return response.data
  },

  async updateTask(id, data) {
    const response = await axios.patch(`${API_URL}/tasks/${id}`, data)
    return response.data
  },

  async deleteTask(id) {
    const response = await axios.delete(`${API_URL}/tasks/${id}`)
    return response.data
  },

  async completeTask(id) {
    const response = await axios.post(`${API_URL}/tasks/${id}/complete`)
    return response.data
  },

  async toggleTaskActive(id) {
    const response = await axios.post(`${API_URL}/tasks/${id}/toggle-active`)
    return response.data
  },

  async getTaskCategories() {
    const response = await axios.get(`${API_URL}/tasks/categories`)
    return response.data
  },

  // Achievement endpoints
  async getAchievements() {
    const response = await axios.get(`${API_URL}/achievements`)
    return response.data
  },

  async getUnlockedAchievements() {
    const response = await axios.get(`${API_URL}/achievements/unlocked`)
    return response.data
  },

  async initializeAchievements() {
    const response = await axios.post(`${API_URL}/achievements/initialize`)
    return response.data
  },

  async getAchievementStats() {
    const response = await axios.get(`${API_URL}/achievements/stats`)
    return response.data
  },

  // Goals endpoints
  async getGoals() {
    const response = await axios.get(`${API_URL}/goals`)
    return response.data
  },

  async createGoal(goal) {
    const response = await axios.post(`${API_URL}/goals`, goal)
    return response.data
  },

  async updateGoal(id, data) {
    const response = await axios.patch(`${API_URL}/goals/${id}`, data)
    return response.data
  },

  async deleteGoal(id) {
    const response = await axios.delete(`${API_URL}/goals/${id}`)
    return response.data
  },

  async updateGoalProgress(id, progressData) {
    const response = await axios.post(`${API_URL}/goals/${id}/progress`, progressData)
    return response.data
  },

  async getGoalCategories() {
    const response = await axios.get(`${API_URL}/goals/categories`)
    return response.data
  },

  // AI task generation
  async generateTasks(data) {
    // Add loading state
    const taskContainer = document.querySelector('.grid')
    if (taskContainer) {
      const loadingElement = document.createElement('div')
      loadingElement.className = 'loading-indicator'
      loadingElement.innerHTML = `
        <div class="spinner"></div>
        <p>Generating quests...</p>
      `
      taskContainer.appendChild(loadingElement)
    }
    
    try {
      const response = await axios.post(`${API_URL}/ai/generate`, data)
      return response.data
    } catch (error) {
      console.error('Error generating tasks:', error)
      throw error
    } finally {
      // Remove loading indicator
      const loadingIndicator = document.querySelector('.loading-indicator')
      if (loadingIndicator) {
        loadingIndicator.remove()
      }
    }
  }
}