import React from 'react'
import { formatDate, formatPercentage, formatProductivityScore } from '@utils'
import { Activity, Monitor, Cpu, HardDrive, Clock } from 'lucide-react'

const ActivityDetails = ({ activity }) => {
  return (
    <div className="activity-details">
      {/* Basic Information */}
      <div className="detail-section">
        <h3 className="detail-section-title">
          <Activity size={20} />
          Activity Information
        </h3>
        <div className="detail-grid">
          <div className="detail-item">
            <label>Client ID</label>
            <span className="font-mono">{activity.client_id}</span>
          </div>
          <div className="detail-item">
            <label>Timestamp</label>
            <span>{formatDate(activity.timestamp, 'PPpp')}</span>
          </div>
          <div className="detail-item">
            <label>Category</label>
            <span className={`badge badge-${activity.activity_category || 'other'}`}>
              {activity.activity_category || 'other'}
            </span>
          </div>
          <div className="detail-item">
            <label>Productivity Score</label>
            <span style={{ color: formatProductivityScore(activity.productivity_score).color }}>
              {formatProductivityScore(activity.productivity_score).text}
            </span>
          </div>
        </div>
      </div>
      
      {/* Application Information */}
      <div className="detail-section">
        <h3 className="detail-section-title">
          <Monitor size={20} />
          Application Activity
        </h3>
        <div className="detail-list">
          <div className="detail-item">
            <label>Application</label>
            <span>{activity.active_application || 'Unknown'}</span>
          </div>
          <div className="detail-item">
            <label>Window Title</label>
            <span className="break-words">{activity.active_window || 'No active window'}</span>
          </div>
          {activity.active_url && (
            <div className="detail-item">
              <label>URL</label>
              <span className="break-all text-blue-600">{activity.active_url}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* System Metrics */}
      {activity.system_metrics && (
        <div className="detail-section">
          <h3 className="detail-section-title">
            <Cpu size={20} />
            System Metrics
          </h3>
          <div className="detail-grid">
            {activity.cpu_percent !== null && (
              <div className="detail-item">
                <label>CPU Usage</label>
                <span>{formatPercentage(activity.cpu_percent)}</span>
              </div>
            )}
            {activity.memory_percent !== null && (
              <div className="detail-item">
                <label>Memory Usage</label>
                <span>{formatPercentage(activity.memory_percent)}</span>
              </div>
            )}
            {activity.disk_percent !== null && (
              <div className="detail-item">
                <label>Disk Usage</label>
                <span>{formatPercentage(activity.disk_percent)}</span>
              </div>
            )}
          </div>
          
          {activity.system_metrics && typeof activity.system_metrics === 'object' && (
            <div className="mt-4">
              <details className="details-expandable">
                <summary className="cursor-pointer font-medium">
                  View Full Metrics
                </summary>
                <pre className="mt-2 p-4 bg-gray-50 rounded text-xs overflow-auto">
                  {JSON.stringify(activity.system_metrics, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      )}
      
      {/* Processes */}
      {activity.processes && activity.processes.length > 0 && (
        <div className="detail-section">
          <h3 className="detail-section-title">
            <HardDrive size={20} />
            Running Processes ({activity.process_count})
          </h3>
          <div className="process-list">
            {activity.processes.slice(0, 20).map((process, index) => (
              <div key={index} className="process-item">
                <div className="process-info">
                  <span className="process-name font-mono text-sm">
                    {typeof process === 'string' ? process : process.name}
                  </span>
                  {typeof process === 'object' && process.pid && (
                    <span className="process-meta text-xs text-gray-500">
                      PID: {process.pid}
                    </span>
                  )}
                </div>
                {typeof process === 'object' && (
                  <div className="process-stats text-xs">
                    {process.cpu_percent !== undefined && (
                      <span className="text-gray-600">CPU: {process.cpu_percent}%</span>
                    )}
                    {process.memory_percent !== undefined && (
                      <span className="text-gray-600 ml-2">MEM: {process.memory_percent}%</span>
                    )}
                  </div>
                )}
              </div>
            ))}
            {activity.processes.length > 20 && (
              <div className="text-sm text-gray-500 mt-2">
                ... and {activity.processes.length - 20} more processes
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ActivityDetails
