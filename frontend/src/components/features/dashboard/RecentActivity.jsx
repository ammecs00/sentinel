import React from 'react'
import { useActivities } from '@hooks'
import { Card, Table, LoadingSpinner } from '@components/common'
import { formatRelativeTime, formatClientType, truncateText } from '@utils'
import { ExternalLink } from 'lucide-react'

const RecentActivity = () => {
  const { activities, loading, error, refetch } = useActivities(true, { limit: 10 })
  
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
      header: 'Window Title',
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
  
  return (
    <Card
      title="Recent Activity"
      subtitle="Latest activity from all clients"
      actions={
        <button 
          onClick={refetch}
          className="btn btn-secondary btn-sm"
          disabled={loading}
        >
          Refresh
        </button>
      }
    >
      {loading ? (
        <LoadingSpinner text="Loading activities..." />
      ) : error ? (
        <div className="error-state">
          <p>Failed to load activities: {error}</p>
        </div>
      ) : (
        <Table
          columns={columns}
          data={activities}
          emptyMessage="No recent activity"
        />
      )}
    </Card>
  )
}

export default RecentActivity
