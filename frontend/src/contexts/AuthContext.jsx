import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authService } from '@services'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [forcePasswordChange, setForcePasswordChange] = useState(false)
  const navigate = useNavigate()
  
  const loadUser = useCallback(async () => {
    try {
      const { success, user: userData } = await authService.getCurrentUser()
      if (success) {
        setUser(userData)
        setForcePasswordChange(userData.force_password_change)
      } else {
        setUser(null)
      }
    }
     catch (error) {
      console.error('Failed to load user:', error)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])
  
  useEffect(() => {
    loadUser()
  }, [loadUser])
  
  const login = async (username, password) => {
    try {
      const result = await authService.login(username, password)
      
      if (result.success) {
        await loadUser()
        setForcePasswordChange(result.forcePasswordChange)
        
        if (result.forcePasswordChange) {
          navigate('/change-password')
        } else {
          navigate('/dashboard')
        }
        
        return { success: true }
      }
      
      return { success: false, error: result.error }
    } catch (error) {
      return { success: false, error: 'Login failed' }
    }
  }
  
  const logout = async () => {
    await authService.logout()
    setUser(null)
    navigate('/login')
  }
  
  const changePassword = async (currentPassword, newPassword) => {
    const result = await authService.changePassword(currentPassword, newPassword)
    
    if (result.success) {
      setForcePasswordChange(false)
      await loadUser()
    }
    
    return result
  }
  
  const value = {
    user,
    loading,
    forcePasswordChange,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false,
    login,
    logout,
    changePassword,
    refreshUser: loadUser
  }
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}