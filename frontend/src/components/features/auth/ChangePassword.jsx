import React, { useState } from 'react'
import { useAuth, useNotification } from '@contexts'
import { useNavigate } from 'react-router-dom'
import { Input, Button, Card, Alert } from '@components/common'
import { Lock, Check } from 'lucide-react'
import { validatePassword } from '@utils'

const ChangePassword = ({ forceChange = false }) => {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [passwordStrength, setPasswordStrength] = useState(null)
  
  const { changePassword } = useAuth()
  const { success, error: notifyError } = useNotification()
  const navigate = useNavigate()
  
  const handleNewPasswordChange = (value) => {
    setNewPassword(value)
    
    if (value) {
      const validation = validatePassword(value)
      setPasswordStrength(validation)
    } else {
      setPasswordStrength(null)
    }
  }
  
  const validateForm = () => {
    const newErrors = {}
    
    if (!currentPassword) {
      newErrors.currentPassword = 'Current password is required'
    }
    
    if (!newPassword) {
      newErrors.newPassword = 'New password is required'
    } else {
      const validation = validatePassword(newPassword)
      if (!validation.isValid) {
        newErrors.newPassword = validation.errors[0]
      }
    }
    
    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your new password'
    } else if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setLoading(true)
    
    try {
      const result = await changePassword(currentPassword, newPassword)
      
      if (result.success) {
        success('Password changed successfully!')
        setCurrentPassword('')
        setNewPassword('')
        setConfirmPassword('')
        setPasswordStrength(null)
        
        if (forceChange) {
          navigate('/dashboard')
        }
      } else {
        notifyError(result.error || 'Failed to change password')
        setErrors({ currentPassword: result.error })
      }
    } catch (err) {
      notifyError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="page">
      <div className="page-container max-w-2xl">
        <Card
          title={forceChange ? 'Password Change Required' : 'Change Password'}
          subtitle={forceChange ? 'You must change your password before continuing' : 'Update your account password'}
        >
          {forceChange && (
            <Alert
              type="warning"
              message="For security reasons, you must change your password before accessing the system."
              className="mb-4"
            />
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
              required
              disabled={loading}
              error={errors.currentPassword}
              icon={Lock}
            />
            
            <Input
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => handleNewPasswordChange(e.target.value)}
              placeholder="Enter new password"
              required
              disabled={loading}
              error={errors.newPassword}
              icon={Lock}
            />
            
            {passwordStrength && (
              <div className="password-requirements">
                <h4 className="text-sm font-medium mb-2">Password Requirements:</h4>
                <ul className="space-y-1">
                  <li className={newPassword.length >= 8 ? 'text-success' : 'text-gray-500'}>
                    <Check size={14} className="inline mr-1" />
                    At least 8 characters
                  </li>
                  <li className={/[a-z]/.test(newPassword) ? 'text-success' : 'text-gray-500'}>
                    <Check size={14} className="inline mr-1" />
                    One lowercase letter
                  </li>
                  <li className={/[A-Z]/.test(newPassword) ? 'text-success' : 'text-gray-500'}>
                    <Check size={14} className="inline mr-1" />
                    One uppercase letter
                  </li>
                  <li className={/\d/.test(newPassword) ? 'text-success' : 'text-gray-500'}>
                    <Check size={14} className="inline mr-1" />
                    One number
                  </li>
                  <li className={/[!@#$%^&*(),.?":{}|<>]/.test(newPassword) ? 'text-success' : 'text-gray-500'}>
                    <Check size={14} className="inline mr-1" />
                    One special character
                  </li>
                </ul>
              </div>
            )}
            
            <Input
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              required
              disabled={loading}
              error={errors.confirmPassword}
              icon={Lock}
            />
            
            <div className="form-actions">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={loading}
                disabled={loading}
                className="w-full"
              >
                Change Password
              </Button>
              
              {!forceChange && (
                <Button
                  type="button"
                  variant="secondary"
                  size="lg"
                  onClick={() => navigate('/dashboard')}
                  disabled={loading}
                  className="w-full"
                >
                  Cancel
                </Button>
              )}
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}

export default ChangePassword
