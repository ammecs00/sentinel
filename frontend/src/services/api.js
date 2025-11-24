import axios from 'axios'

// In production with nginx proxy, we use /api which proxies to backend:8000/api/
// In development, we use the full backend URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1'
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000')

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/${API_VERSION}`,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('sentinel_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add request timestamp
    config.metadata = { startTime: new Date() }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Calculate request duration
    const duration = new Date() - response.config.metadata.startTime
    if (import.meta.env.VITE_ENABLE_DEBUG === 'true') {
      console.log(`API Request: ${response.config.url} - ${duration}ms`)
    }
    
    return response
  },
  (error) => {
    // Handle errors
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('sentinel_token')
          // Prevent redirect loop if already on login page
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          break
          
        case 403:
          // Forbidden
          console.error('Access forbidden:', data.detail)
          break
          
        case 404:
          // Not found
          console.error('Resource not found:', data.detail)
          break
          
        case 429:
          // Rate limited
          console.error('Rate limit exceeded. Please try again later.')
          break
          
        case 500:
          // Server error
          console.error('Server error:', data.detail)
          break
          
        default:
          console.error('API Error:', data.detail || error.message)
      }
      
      return Promise.reject({
        status,
        message: data?.detail || 'An error occurred',
        data
      })
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.message)
      return Promise.reject({
        status: 0,
        message: 'Network error. Please check your connection.',
        data: null
      })
    } else {
      // Other errors
      console.error('Error:', error.message)
      return Promise.reject({
        status: 0,
        message: error.message,
        data: null
      })
    }
  }
)

// Helper functions
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('sentinel_token', token)
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    localStorage.removeItem('sentinel_token')
    delete api.defaults.headers.common['Authorization']
  }
}

export const getAuthToken = () => {
  return localStorage.getItem('sentinel_token')
}

export const isAuthenticated = () => {
  return !!getAuthToken()
}

export default api