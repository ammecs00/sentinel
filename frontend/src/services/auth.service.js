import api, { setAuthToken } from './api'

class AuthService {
  async login(username, password) {
    try {
      console.log('AuthService.login called for:', username)
      const response = await api.post('/auth/login', {
        username,
        password
      })
      
      console.log('Login response:', response.data)
      
      const { access_token, force_password_change } = response.data
      setAuthToken(access_token)
      
      return {
        success: true,
        token: access_token,
        forcePasswordChange: force_password_change
      }
    } catch (error) {
      console.error('Login error:', error)
      return {
        success: false,
        error: error.message || 'Login failed'
      }
    }
  }
  
  async logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setAuthToken(null)
    }
  }
  
  async getCurrentUser() {
    try {
      console.log('AuthService.getCurrentUser called')
      const response = await api.get('/auth/me')
      console.log('Current user response:', response.data)
      return {
        success: true,
        user: response.data
      }
    } catch (error) {
      console.error('Get current user error:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async changePassword(currentPassword, newPassword) {
    try {
      const response = await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      
      return {
        success: true,
        message: response.data.message
      }
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Failed to change password'
      }
    }
  }
  
  async createApiKey(name, options = {}) {
    try {
      console.log('Creating API key:', name)
      const response = await api.post('/auth/keys', {
        name,
        ...options
      })
      
      console.log('Create API key response:', response.data)
      
      return {
        success: true,
        apiKey: response.data
      }
    } catch (error) {
      console.error('Create API key error:', error)
      return {
        success: false,
        error: error.message || 'Failed to create API key'
      }
    }
  }
  
  async getApiKeys() {
    try {
      console.log('Getting API keys...')
      const response = await api.get('/auth/keys')
      console.log('Get API keys response:', response.data)
      
      // Ensure we always return an array
      const apiKeys = Array.isArray(response.data) ? response.data : []
      
      return {
        success: true,
        apiKeys: apiKeys
      }
    } catch (error) {
      console.error('Get API keys error:', error)
      return {
        success: false,
        error: error.message || 'Failed to load API keys',
        apiKeys: []
      }
    }
  }
  
  async revokeApiKey(keyId) {
    try {
      console.log('Revoking API key:', keyId)
      await api.delete(`/auth/keys/${keyId}`)
      return {
        success: true
      }
    } catch (error) {
      console.error('Revoke API key error:', error)
      return {
        success: false,
        error: error.message || 'Failed to revoke API key'
      }
    }
  }
}

export default new AuthService()