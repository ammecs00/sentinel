import React, { useState, useEffect } from 'react'
import { useAuth, useNotification } from '@contexts'
import { Input, Button, Alert } from '@components/common'
import { LogIn, User, Lock, Eye, EyeOff } from 'lucide-react'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const { login } = useAuth()
  const { error: notifyError } = useNotification()
  
  useEffect(() => {
    // Clear any existing tokens on login page
    localStorage.removeItem('sentinel_token')
  }, [])
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      const result = await login(username, password)
      
      if (!result.success) {
        setError(result.error || 'Login failed. Please check your credentials.')
        notifyError(result.error || 'Login failed')
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.')
      notifyError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          {/* Logo Section */}
          <div className="login-header">
            <div className="login-logo">S</div>
            <h1 className="login-title">Sentinel</h1>
            <p className="login-subtitle">Employee Monitoring System</p>
          </div>
          
          {/* Login Form */}
          <form onSubmit={handleSubmit} className="login-form">
            {error && (
              <Alert
                type="error"
                message={error}
                onClose={() => setError('')}
              />
            )}
            
            <Input
              label="Username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={loading}
              icon={User}
              autoComplete="username"
            />
            
            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="password-input-wrapper">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  disabled={loading}
                  icon={Lock}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              disabled={loading || !username || !password}
              icon={LogIn}
              className="w-full"
            >
              Sign In
            </Button>
          </form>
          
          {/* Information */}
          <div className="login-footer">
            <div className="login-info">
              <h4>Security Notice</h4>
              <ul className="login-info-list">
                <li>Strong passwords required (8+ chars, uppercase, lowercase, numbers, special chars)</li>
                <li>Your session will expire after 24 hours of inactivity</li>
                <li>All login attempts are logged for security</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login