import React from 'react'
import { ActivitiesList } from '@components/features/activities'

const ActivitiesPage = () => {
  return (
    <div className="page">
      <div className="page-header">
        <h2>Activities</h2>
        <p>View and analyze client activities</p>
      </div>
      
      <ActivitiesList />
    </div>
  )
}

export default ActivitiesPage
