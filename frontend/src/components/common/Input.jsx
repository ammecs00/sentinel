import React, { forwardRef } from 'react'

const Input = forwardRef(({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  disabled = false,
  error,
  helperText,
  required = false,
  className = '',
  icon: Icon,
  ...props
}, ref) => {
  return (
    <div className={`form-group ${className}`}>
      {label && (
        <label className="form-label">
          {label}
          {required && <span className="text-error ml-1">*</span>}
        </label>
      )}
      
      <div className="input-wrapper">
        {Icon && (
          <div className="input-icon">
            <Icon size={18} />
          </div>
        )}
        <input
          ref={ref}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={`form-input ${Icon ? 'input-with-icon' : ''} ${error ? 'input-error' : ''}`}
          {...props}
        />
      </div>
      
      {error && (
        <p className="form-error">{error}</p>
      )}
      
      {helperText && !error && (
        <p className="form-helper">{helperText}</p>
      )}
    </div>
  )
})

Input.displayName = 'Input'

export default Input