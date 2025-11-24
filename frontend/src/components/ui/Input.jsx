import React from 'react'

const Input = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  disabled = false,
  error,
  className = '',
  ...props
}) => {
  return (
    <div className="form-group">
      {label && (
        <label className="form-label">
          {label}
        </label>
      )}
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        className={`form-input ${error ? 'border-error-500' : ''} ${className}`}
        {...props}
      />
      {error && (
        <p className="text-error-500 text-sm mt-1">{error}</p>
      )}
    </div>
  )
}

export default Input