import React from 'react'
import { Loader2 } from 'lucide-react'

const LoadingSpinner = ({ size = 'md', text, className = '' }) => {
  const sizes = {
    sm: 16,
    md: 24,
    lg: 32,
    xl: 48
  }
  
  return (
    <div className={`loading-spinner ${className}`}>
      <Loader2 className="animate-spin" size={sizes[size]} />
      {text && <p className="loading-text">{text}</p>}
    </div>
  )
}

export default LoadingSpinner