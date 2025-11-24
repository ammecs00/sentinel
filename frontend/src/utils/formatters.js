import { format, formatDistance, formatRelative, isValid, parseISO } from 'date-fns'

export const formatDate = (date, formatStr = 'PPpp') => {
  if (!date) return 'N/A'
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    if (!isValid(dateObj)) return 'Invalid Date'
    return format(dateObj, formatStr)
  } catch (error) {
    console.error('Date formatting error:', error)
    return 'Invalid Date'
  }
}

export const formatRelativeTime = (date) => {
  if (!date) return 'N/A'
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    if (!isValid(dateObj)) return 'Invalid Date'
    return formatDistance(dateObj, new Date(), { addSuffix: true })
  } catch (error) {
    return 'Invalid Date'
  }
}

export const formatRelativeDate = (date) => {
  if (!date) return 'N/A'
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    if (!isValid(dateObj)) return 'Invalid Date'
    return formatRelative(dateObj, new Date())
  } catch (error) {
    return 'Invalid Date'
  }
}

export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes'
  if (!bytes) return 'N/A'
  
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

export const formatPercentage = (value, decimals = 1) => {
  if (value === null || value === undefined) return 'N/A'
  return `${parseFloat(value).toFixed(decimals)}%`
}

export const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined) return 'N/A'
  return parseFloat(value).toFixed(decimals)
}

export const formatDuration = (seconds) => {
  if (!seconds) return '0s'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  const parts = []
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0) parts.push(`${minutes}m`)
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`)
  
  return parts.join(' ')
}

export const formatClientType = (type) => {
  const types = {
    linux_desktop: 'Linux Desktop',
    linux_server: 'Linux Server',
    windows_desktop: 'Windows Desktop',
    windows_server: 'Windows Server',
    macos_desktop: 'macOS Desktop'
  }
  return types[type] || type || 'Unknown'
}

export const formatActivityCategory = (category) => {
  const categories = {
    work: 'Work',
    break: 'Break',
    idle: 'Idle',
    other: 'Other'
  }
  return categories[category] || category || 'Unknown'
}

export const truncateText = (text, maxLength = 50) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export const formatProductivityScore = (score) => {
  if (score === null || score === undefined) return { text: 'N/A', color: '#6b7280', level: 'unknown' }
  
  if (score >= 70) return { text: `${score}%`, color: '#10b981', level: 'high' }
  if (score >= 40) return { text: `${score}%`, color: '#f59e0b', level: 'medium' }
  return { text: `${score}%`, color: '#ef4444', level: 'low' }
}

export const capitalize = (str) => {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}