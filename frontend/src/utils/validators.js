export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(String(email).toLowerCase())
}

export const validatePassword = (password) => {
  const errors = []
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long')
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter')
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter')
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number')
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

export const validateUsername = (username) => {
  const errors = []
  
  if (username.length < 3) {
    errors.push('Username must be at least 3 characters long')
  }
  
  if (username.length > 50) {
    errors.push('Username must be less than 50 characters')
  }
  
  if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    errors.push('Username can only contain letters, numbers, underscores, and hyphens')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

export const validateRequired = (value, fieldName = 'Field') => {
  if (!value || (typeof value === 'string' && !value.trim())) {
    return {
      isValid: false,
      error: `${fieldName} is required`
    }
  }
  return { isValid: true }
}

export const validateLength = (value, min, max, fieldName = 'Field') => {
  const length = value ? value.length : 0
  
  if (length < min) {
    return {
      isValid: false,
      error: `${fieldName} must be at least ${min} characters`
    }
  }
  
  if (max && length > max) {
    return {
      isValid: false,
      error: `${fieldName} must be less than ${max} characters`
    }
  }
  
  return { isValid: true }
}