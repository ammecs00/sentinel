import React from 'react'
import { Loader2 } from 'lucide-react'

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  icon: Icon,
  className = '',
  ...props
}) => {
  const baseClasses = 'btn'
  const variantClasses = `btn-${variant}`
  const sizeClasses = `btn-${size}`
  const disabledClass = (disabled || loading) ? 'btn-disabled' : ''
  
  return (
    <button
      type={type}
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${disabledClass} ${className}`.trim()}
      onClick={onClick}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 className="btn-icon animate-spin" size={16} />
          <span>Loading...</span>
        </>
      ) : (
        <>
          {Icon && <Icon className="btn-icon" size={16} />}
          <span>{children}</span>
        </>
      )}
    </button>
  )
}

export default Button