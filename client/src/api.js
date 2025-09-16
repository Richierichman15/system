import axios from 'axios'

const API_URL = 'http://localhost:8000'

export const api = {
  // Profile endpoints
  async getProfile() {
    const response = await axios.get(`${API_URL}/profile`)
    return response.data
  },

  async updateProfile(data) {
    const response = await axios.post(`${API_URL}/profile`, data)
    return response.data
  },

  // Task endpoints
  async listTasks() {
    const response = await axios.get(`${API_URL}/tasks`)
    return response.data
  },

  async completeTask(id) {
    const response = await axios.post(`${API_URL}/tasks/${id}/complete`)
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