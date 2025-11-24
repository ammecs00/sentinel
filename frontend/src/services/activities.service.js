import api from './api'

class ActivitiesService {
  async getActivities(params = {}) {
    try {
      const response = await api.get('/activities/', { params })
      return {
        success: true,
        activities: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async getActivity(activityId) {
    try {
      const response = await api.get(`/activities/${activityId}`)
      return {
        success: true,
        activity: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  async getActivityStats(params = {}) {
    try {
      const response = await api.get('/activities/stats', { params })
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
  
  async cleanupOldActivities(days = 90) {
    try {
      const response = await api.post('/activities/cleanup', null, {
        params: { days }
      })
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }
}

export default new ActivitiesService()