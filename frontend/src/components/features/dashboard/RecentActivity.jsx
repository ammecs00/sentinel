import React from 'react'
import { useActivities } from '@hooks'
import { Card, Table, LoadingSpinner } from '@components/common'
import { formatRelativeTime, formatClientType, truncateText } from '@utils'
import { ExternalLink } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const RecentActivity = () => {
  const { activities, loading, error } = useActivities(true, { limit: 10 })
  const navigate = useNavigate()
  
  const columns = [
    {
      key: 'timestamp',
      header: 'Time',
      width: '15%',
      render: (activity) => formatRelativeTime(activity.timestamp)
    },
    {
      key: 'client_id',
      header: 'Client',
      width: '20%',
      render: (activity) => (
        <span className="font-mono text-sm">{activity.client_id}</span>
      )
    },
    {
      key: 'active_application',
      header: 'Application',
      width: '20%',
      render: (activity) => activity.active_application || 'Unknown'
    },
    {
      key: 'active_window',
      header: 'Window',
      width: '30%',
      render: (activity) => truncateText(activity.active_window || 'No active window', 50)
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
    }
  ]

  const handleViewAll = () => {
    navigate('/activities')
  }

  if (loading) {
    return (
      <Card title="Recent Activity" subtitle="Latest client activities">
        <LoadingSpinner text="Loading activities..." />
      </Card>
    )
  }

  if (error) {
    return (
      <Card title="Recent Activity" subtitle="Latest client activities">
        <div className="error-state">
          <p>Failed to load activities: {error}</p>
        </div>
      </Card>
    )
  }

  return (
    <Card 
      title="Recent Activity" 
      subtitle="Latest client activities"
      actions={
        <button 
          className="btn btn-secondary btn-sm"
          onClick={handleViewAll}
        >
          <ExternalLink size={16} />
          View All
        </button>
      }
    >
      <Table
        columns={columns}
        data={activities}
        emptyMessage="No recent activities"
      />
    </Card>
  )
}

export default RecentActivity