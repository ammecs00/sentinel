import React, { useState } from 'react'
import { useClients } from '@hooks'
import { Card, Table, LoadingSpinner, Button, Modal } from '@components/common'
import { formatRelativeTime, formatClientType } from '@utils'
import { Monitor, RefreshCw, Eye } from 'lucide-react'
import ClientDetails from './ClientDetails'

const ClientsList = () => {
  const [selectedClient, setSelectedClient] = useState(null)
  const [showDetails, setShowDetails] = useState(false)
  const [filter, setFilter] = useState('all') // all, online, offline
  
  const { clients, loading, error, refetch } = useClients(true, {
    is_active: filter === 'all' ? undefined : true
  })
  
  const handleViewClient = (client) => {
    setSelectedClient(client)
    setShowDetails(true)
  }
  
  const handleCloseDetails = () => {
    setShowDetails(false)
    setSelectedClient(null)
  }
  
  const getStatusBadge = (lastSeen) => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000)
    const isOnline = new Date(lastSeen) > fiveMinutesAgo
    
    return (
      <span className={`status-badge ${isOnline ? 'status-online' : 'status-offline'}`}>
        {isOnline ? 'Online' : 'Offline'}
      </span>
    )
  }
  
  const filteredClients = filter === 'online'
    ? clients.filter(c => new Date(c.last_seen) > new Date(Date.now() - 5 * 60 * 1000))
    : filter === 'offline'
    ? clients.filter(c => new Date(c.last_seen) <= new Date(Date.now() - 5 * 60 * 1000))
    : clients
  
  const columns = [
    {
      key: 'client_id',
      header: 'Client ID',
      width: '25%',
      render: (client) => (
        <span className="font-mono text-sm">{client.client_id}</span>
      )
    },
    {
      key: 'client_type',
      header: 'Type',
      width: '15%',
      render: (client) => formatClientType(client.client_type)
    },
    {
      key: 'hostname',
      header: 'Hostname',
      width: '20%',
      render: (client) => client.hostname || 'Unknown'
    },
    {
      key: 'last_seen',
      header: 'Last Seen',
      width: '20%',
      render: (client) => formatRelativeTime(client.last_seen)
    },
    {
      key: 'status',
      header: 'Status',
      width: '10%',
      render: (client) => getStatusBadge(client.last_seen)
    },
    {
      key: 'actions',
      header: 'Actions',
      width: '10%',
      sortable: false,
      render: (client) => (
        <Button
          variant="secondary"
          size="sm"
          icon={Eye}
          onClick={() => handleViewClient(client)}
        >
          View
        </Button>
      )
    }
  ]
  
  return (
    <>
      <Card
        title="Connected Clients"
        subtitle={`${filteredClients.length} client${filteredClients.length !== 1 ? 's' : ''}`}
        actions={
          <div className="flex gap-2">
            <div className="filter-buttons">
              <button
                className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                All
              </button>
              <button
                className={`filter-btn ${filter === 'online' ? 'active' : ''}`}
                onClick={() => setFilter('online')}
              >
                Online
              </button>
              <button
                className={`filter-btn ${filter === 'offline' ? 'active' : ''}`}
                onClick={() => setFilter('offline')}
              >
                Offline
              </button>
            </div>
            
            <Button
              variant="secondary"
              size="sm"
              icon={RefreshCw}
              onClick={refetch}
              disabled={loading}
            >
              Refresh
            </Button>
          </div>
        }
      >
        {loading ? (
          <LoadingSpinner text="Loading clients..." />
        ) : error ? (
          <div className="error-state">
            <p>Failed to load clients: {error}</p>
          </div>
        ) : (
          <Table
            columns={columns}
            data={filteredClients}
            emptyMessage="No clients found"
          />
        )}
      </Card>
      
      {showDetails && selectedClient && (
        <Modal
          isOpen={showDetails}
          onClose={handleCloseDetails}
          title="Client Details"
          size="xl"
        >
          <ClientDetails client={selectedClient} onClose={handleCloseDetails} />
        </Modal>
      )}
    </>
  )
}

export default ClientsList
