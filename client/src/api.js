import axios from 'axios'

// Dynamic API URL based on current host
const getApiUrl = () => {
  const hostname = window.location.hostname
  // If accessing via IP address, use the same IP for backend
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `http://${hostname}:8000`
  }
  return 'http://localhost:8000'
}

const API_URL = getApiUrl()

export const api = {
  // Auth
  async login({ username, password }) {
    const response = await axios.post(`${API_URL}/auth/login`, { username, password })
    const { token } = response.data
    if (token) localStorage.setItem('auth_token', token)
    return response.data
  },

  // Profile endpoints
  async getProfile() {
    const response = await axios.get(`${API_URL}/profile`)
    return response.data
  },

  async updateProfile(data) {
    const response = await axios.patch(`${API_URL}/profile`, data)
    return response.data
  },

  // Task endpoints
  async listTasks(params = {}) {
    // Add cache busting to ensure fresh data
    const cacheParams = { ...params, _t: Date.now() }
    const response = await axios.get(`${API_URL}/tasks`, { params: cacheParams })
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

  // Goal endpoints
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

  async updateGoalProgress(id, data) {
    const response = await axios.patch(`${API_URL}/goals/${id}/progress`, data)
    return response.data
  },

  async deleteGoal(id) {
    const response = await axios.delete(`${API_URL}/goals/${id}`)
    return response.data
  },

  async completeGoal(id) {
    const response = await axios.post(`${API_URL}/goals/${id}/complete`)
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
  },

  // Advanced AI task generation with specialized models
  async generateTasksAdvanced(data) {
    const taskContainer = document.querySelector('.grid')
    if (taskContainer) {
      const loadingElement = document.createElement('div')
      loadingElement.className = 'loading-indicator'
      loadingElement.innerHTML = `
        <div class="spinner"></div>
        <p>Generating specialized quests...</p>
      `
      taskContainer.appendChild(loadingElement)
    }
    
    try {
      const response = await axios.post(`${API_URL}/ai/generate-advanced`, data)
      return response.data
    } catch (error) {
      console.error('Error generating advanced tasks:', error)
      throw error
    } finally {
      const loadingIndicator = document.querySelector('.loading-indicator')
      if (loadingIndicator) {
        loadingIndicator.remove()
      }
    }
  },

  // Submit feedback for AI learning
  async submitTaskFeedback(taskId, rating, completed, completionTime = null) {
    const response = await axios.post(`${API_URL}/ai/feedback`, {
      task_id: taskId,
      rating: rating,
      completed: completed,
      completion_time: completionTime
    })
    return response.data
  },

  // Get AI model statistics
  async getAIModelStats() {
    const response = await axios.get(`${API_URL}/ai/models/stats`)
    return response.data
  },

  // Get available AI models
  async getAvailableModels() {
    const response = await axios.get(`${API_URL}/ai/models/available`)
    return response.data
  }
}