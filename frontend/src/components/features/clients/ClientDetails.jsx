import React from 'react'
import { useActivities } from '@hooks'
import { Table, LoadingSpinner } from '@components/common'
import { formatDate, formatClientType, formatRelativeTime } from '@utils'
import { Monitor, HardDrive, Cpu, Calendar } from 'lucide-react'

const ClientDetails = ({ client, onClose }) => {
  const { activities, loading } = useActivities(true, {
    client_id: client.client_id,
    limit: 20
  })
  
  const activityColumns = [
    {
      key: 'timestamp',
      header: 'Time',
      width: '20%',
      render: (activity) => formatRelativeTime(activity.timestamp)
    },
    {
      key: 'active_application',
      header: 'Application',
      width: '25%',
      render: (activity) => activity.active_application || 'Unknown'
    },
    {
      key: 'category',
      header: 'Category',
      width: '15%',
      render: (activity) => (
        <span className={`badge badge-${activity.activity_category || 'other'}`}>
          {activity.activity_category || 'other'}
        </span>
      )
    },
    {
      key: 'productivity',
      header: 'Productivity',
      width: '15%',
      render: (activity) => 
        activity.productivity_score ? `${activity.productivity_score}%` : 'N/A'
    },
    {
      key: 'processes',
      header: 'Processes',
      width: '15%',
      render: (activity) => `${activity.process_count || 0}`
    }
  ]
  
  return (
    <div className="client-details">
      {/* Client Information */}
      <div className="detail-section">
        <h3 className="detail-section-title">
          <Monitor size={20} />
          Client Information
        </h3>
        <div className="detail-grid">
          <div className="detail-item">
            <label>Client ID</label>
            <span className="font-mono">{client.client_id}</span>
          </div>
          <div className="detail-item">
            <label>Type</label>
            <span>{formatClientType(client.client_type)}</span>
          </div>
          <div className="detail-item">
            <label>Hostname</label>
            <span>{client.hostname || 'Unknown'}</span>
          </div>
          <div className="detail-item">
            <label>IP Address</label>
            <span>{client.ip_address || 'Unknown'}</span>
          </div>
          <div className="detail-item">
            <label>Last Seen</label>
            <span>{formatRelativeTime(client.last_seen)}</span>
          </div>
          <div className="detail-item">
            <label>Created</label>
            <span>{formatDate(client.created_at, 'PP')}</span>
          </div>
          <div className="detail-item">
            <label>Status</label>
            <span className={new Date(client.last_seen) > new Date(Date.now() - 5 * 60 * 1000) 
              ? 'text-success' 
              : 'text-error'
            }>
              {new Date(client.last_seen) > new Date(Date.now() - 5 * 60 * 1000) 
                ? 'Online' 
                : 'Offline'}
            </span>
          </div>
          <div className="detail-item">
            <label>Consent</label>
            <span className={client.employee_consent ? 'text-success' : 'text-warning'}>
              {client.employee_consent ? 'Granted' : 'Not granted'}
            </span>
          </div>
        </div>
      </div>
      
      {/* Platform Information */}
      {client.platform_info && (
        <div className="detail-section">
          <h3 className="detail-section-title">
            <HardDrive size={20} />
            Platform Information
          </h3>
          <div className="detail-grid">
            <div className="detail-item">
              <label>System</label>
              <span>{client.platform_info.system || 'Unknown'}</span>
            </div>
            <div className="detail-item">
              <label>Release</label>
              <span>{client.platform_info.release || 'Unknown'}</span>
            </div>
            <div className="detail-item">
              <label>Architecture</label>
              <span>{client.platform_info.architecture || 'Unknown'}</span>
            </div>
            <div className="detail-item">
              <label>Processor</label>
              <span>{client.platform_info.processor || 'Unknown'}</span>
            </div>
            {client.platform_info.memory_total_gb && (
              <div className="detail-item">
                <label>Total Memory</label>
                <span>{client.platform_info.memory_total_gb} GB</span>
              </div>
            )}
            {client.platform_info.disk_total_gb && (
              <div className="detail-item">
                <label>Total Disk</label>
                <span>{client.platform_info.disk_total_gb} GB</span>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Recent Activities */}
      <div className="detail-section">
        <h3 className="detail-section-title">
          <Calendar size={20} />
          Recent Activities
        </h3>
        {loading ? (
          <LoadingSpinner text="Loading activities..." />
        ) : (
          <Table
            columns={activityColumns}
            data={activities}
            emptyMessage="No recent activities"
          />
        )}
      </div>
    </div>
  )
}

export default ClientDetails
