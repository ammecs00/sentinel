import React from 'react'
import { X, AlertCircle, CheckCircle, AlertTriangle, Info } from 'lucide-react'

const icons = {
  error: AlertCircle,
  success: CheckCircle,
  warning: AlertTriangle,
  info: Info
}

const Alert = ({ type = 'info', title, message, onClose, className = '' }) => {
  const Icon = icons[type]
  
  return (
    <div className={`alert alert-${type} ${className}`}>
      <div className="alert-icon">
        <Icon size={20} />
      </div>
      <div className="alert-content">
        {title && <div className="alert-title">{title}</div>}
        {message && <div className="alert-message">{message}</div>}
      </div>
      {onClose && (
        <button className="alert-close" onClick={onClose}>
          <X size={18} />
        </button>
      )}
    </div>
  )
}

export default Alert