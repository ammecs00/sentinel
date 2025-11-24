import React from 'react'
import StatsCards from './StatsCards'
import RecentActivity from './RecentActivity'

const Dashboard = () => {
  return (
    <div className="page">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Overview of your monitoring system</p>
      </div>
      
      <div className="dashboard-content">
        <StatsCards />
        <RecentActivity />
      </div>
    </div>
  )
}

export default Dashboard
