import React, { useEffect, useState } from 'react'
import { Monitor, Activity, TrendingUp, Clock } from 'lucide-react'
import { useClientStats, useActivityStats } from '@hooks'
import { LoadingSpinner, Card } from '@components/common'
import { formatNumber } from '@utils'

const StatsCards = () => {
  const { stats: clientStats, loading: clientsLoading } = useClientStats()
  const { stats: activityStats, loading: activitiesLoading } = useActivityStats({ days: 7 })
  
  const loading = clientsLoading || activitiesLoading
  
  const stats = [
    {
      title: 'Total Clients',
      value: clientStats?.total_clients || 0,
      icon: Monitor,
      color: 'blue',
      description: 'Registered devices'
    },
    {
      title: 'Online Now',
      value: clientStats?.online_clients || 0,
      icon: Activity,
      color: 'green',
      description: 'Active in last 5 minutes'
    },
    {
      title: 'Activities (7d)',
      value: activityStats?.total_activities || 0,
      icon: TrendingUp,
      color: 'purple',
      description: 'Last 7 days'
    },
    {
      title: 'Avg Productivity',
      value: activityStats?.avg_productivity ? `${formatNumber(activityStats.avg_productivity, 1)}%` : 'N/A',
      icon: Clock,
      color: 'orange',
      description: 'Based on activity analysis'
    }
  ]
  
  if (loading) {
    return (
      <div className="stats-loading">
        <LoadingSpinner text="Loading statistics..." />
      </div>
    )
  }
  
  return (
    <div className="stats-grid">
      {stats.map((stat, index) => (
        <Card key={index} className="stat-card">
          <div className="stat-card-content">
            <div className={`stat-icon stat-icon-${stat.color}`}>
              <stat.icon size={24} />
            </div>
            <div className="stat-info">
              <p className="stat-label">{stat.title}</p>
              <h3 className="stat-value">{stat.value}</h3>
              <p className="stat-description">{stat.description}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}

export default StatsCards
