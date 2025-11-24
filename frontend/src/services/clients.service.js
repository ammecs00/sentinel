import api from './api'

class ClientsService {
  async getClients(params = {}) {
    try {
      const response = await api.get('/clients/', { params })
      return {
        success: true,
        clients: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async getClient(clientId) {
    try {
      const response = await api.get(`/clients/${clientId}`)
      return {
        success: true,
        client: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async getOnlineClients(minutes = 5) {
    try {
      const response = await api.get('/clients/online', {
        params: { minutes }
      })
      return {
        success: true,
        clients: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async getClientStats() {
    try {
      const response = await api.get('/clients/stats')
      return {
        success: true,
        stats: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async updateClient(clientId, data) {
    try {
      const response = await api.put(`/clients/${clientId}`, data)
      return {
        success: true,
        client: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async deleteClient(clientId) {
    try {
      await api.delete(`/clients/${clientId}`)
      return {
        success: true
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
}

export default new ClientsService()