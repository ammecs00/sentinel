export const CLIENT_TYPES = {
  linux_desktop: 'Linux Desktop',
  linux_server: 'Linux Server',
  windows_desktop: 'Windows Desktop',
  windows_server: 'Windows Server',
  macos_desktop: 'macOS Desktop'
}

export const CLIENT_TYPE_ICONS = {
  linux_desktop: '🐧',
  linux_server: '🖥️',
  windows_desktop: '🪟',
  windows_server: '🖥️',
  macos_desktop: '🍎'
}

export const ACTIVITY_CATEGORIES = {
  work: 'Work',
  break: 'Break',
  idle: 'Idle',
  other: 'Other'
}

export const ACTIVITY_CATEGORY_COLORS = {
  work: '#10b981',
  break: '#f59e0b',
  idle: '#6b7280',
  other: '#3b82f6'
}

export const STATUS_COLORS = {
  online: '#10b981',
  offline: '#ef4444',
  warning: '#f59e0b'
}

export const PRODUCTIVITY_LEVELS = {
  high: { min: 70, color: '#10b981', label: 'High' },
  medium: { min: 40, color: '#f59e0b', label: 'Medium' },
  low: { min: 0, color: '#ef4444', label: 'Low' }
}

export const DATE_RANGES = {
  today: 'Today',
  yesterday: 'Yesterday',
  last7days: 'Last 7 Days',
  last30days: 'Last 30 Days',
  last90days: 'Last 90 Days',
  custom: 'Custom Range'
}

export const REFRESH_INTERVALS = {
  realtime: 5000,
  normal: 30000,
  slow: 60000
}

export const PAGINATION = {
  defaultPageSize: 50,
  pageSizeOptions: [25, 50, 100, 200]
}