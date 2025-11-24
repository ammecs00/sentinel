import React, { useState } from 'react'
import { useActivities } from '@hooks'
import { Card, Table, LoadingSpinner, Button, Modal } from '@components/common'
import { formatRelativeTime, formatClientType, truncateText } from '@utils'
import { RefreshCw, Eye, Filter } from 'lucide-react'
import ActivityDetails from './ActivityDetails'
import ActivityFilters from './ActivityFilters'

const ActivitiesList = () => {
  const [selectedActivity, setSelectedActivity] = useState(null)
  const [showDetails, setShowDetails] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    client_id: '',
    category: '',
    start_date: null,
    end_date: null
  })
  
  const { activities, loading, error, refetch } = useActivities(true, {
    ...filters,
    limit: 100
  })
  
  const handleViewActivity = (activity) => {
    setSelectedActivity(activity)
    setShowDetails(true)
  }
  
  const handleCloseDetails = () => {
    setShowDetails(false)
    setSelectedActivity(null)
  }
  
  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters)
    setShowFilters(false)
    refetch(newFilters)
  }
  
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
      width: '18%',
      render: (activity) => (
        <span className="font-mono text-sm">{activity.client_id}</span>
      )
    },
    {
      key: 'active_application',
      header: 'Application',
      width: '18%',
      render: (activity) => activity.active_application || 'Unknown'
    },
    {
      key: 'active_window',
      header: 'Window',
      width: '25%',
      render: (activity) => truncateText(activity.active_window || 'No active window', 40)
    },
    {
      key: 'category',
      header: 'Category',
      width: '12%',
      render: (activity) => (
        <span className={`badge badge-${activity.activity_category || 'other'}`}>
          {activity.activity_category || 'other'}
        </span>
      )
    },
    {
      key: 'productivity',
      header: 'Score',
      width: '8%',
      render: (activity) => {
        const score = activity.productivity_score
        if (!score) return 'N/A'
        
        let className = 'text-gray-500'
        if (score >= 70) className = 'text-success'
        else if (score >= 40) className = 'text-warning'
        else className = 'text-error'
        
        return <span className={className}>{score}%</span>
      }
    },
    {
      key: 'actions',
      header: '',
      width: '4%',
      sortable: false,
      render: (activity) => (
        <Button
          variant="secondary"
          size="sm"
          icon={Eye}
          onClick={() => handleViewActivity(activity)}
        >
          View
        </Button>
      )
    }
  ]
  
  const activeFiltersCount = Object.values(filters).filter(v => v && v !== '').length
  
  return (
    <>
      <Card
        title="Activity Log"
        subtitle={`${activities.length} activit${activities.length !== 1 ? 'ies' : 'y'}`}
        actions={
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={Filter}
              onClick={() => setShowFilters(true)}
            >
              Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}
            </Button>
            
            <Button
              variant="secondary"
              size="sm"
              icon={RefreshCw}
              onClick={() => refetch(filters)}
              disabled={loading}
            >
              Refresh
            </Button>
          </div>
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
            emptyMessage="No activities found"
          />
        )}
      </Card>
      
      {showDetails && selectedActivity && (
        <Modal
          isOpen={showDetails}
          onClose={handleCloseDetails}
          title="Activity Details"
          size="xl"
        >
          <ActivityDetails activity={selectedActivity} onClose={handleCloseDetails} />
        </Modal>
      )}
      
      {showFilters && (
        <Modal
          isOpen={showFilters}
          onClose={() => setShowFilters(false)}
          title="Filter Activities"
          size="md"
        >
          <ActivityFilters
            initialFilters={filters}
            onApply={handleApplyFilters}
            onClose={() => setShowFilters(false)}
          />
        </Modal>
      )}
    </>
  )
}

export default ActivitiesList
