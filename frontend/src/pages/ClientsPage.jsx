import React from 'react'
import { ClientsList, ClientStats } from '@components/features/clients'

const ClientsPage = () => {
  return (
    <div className="page">
      <div className="page-header">
        <h2>Clients</h2>
        <p>Monitor and manage connected clients</p>
      </div>
      
      <div className="page-content">
        <ClientStats />
        <ClientsList />
      </div>
    </div>
  )
}

export default ClientsPage
