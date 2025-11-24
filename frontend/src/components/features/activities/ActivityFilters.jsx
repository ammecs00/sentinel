import React, { useState } from 'react'
import { Input, Button } from '@components/common'
import { useClients } from '@hooks'
import { ACTIVITY_CATEGORIES } from '@utils'

const ActivityFilters = ({ initialFilters, onApply, onClose }) => {
  const [filters, setFilters] = useState(initialFilters)
  const { clients } = useClients()
  
  const handleChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }))
  }
  
  const handleReset = () => {
    const resetFilters = {
      client_id: '',
      category: '',
      start_date: null,
      end_date: null
    }
    setFilters(resetFilters)
  }
  
  const handleApply = () => {
    onApply(filters)
  }
  
  return (
    <div className="filters-form">
      <div className="form-group">
        <label className="form-label">Client</label>
        <select
          className="form-input"
          value={filters.client_id}
          onChange={(e) => handleChange('client_id', e.target.value)}
        >
          <option value="">All Clients</option>
          {clients.map(client => (
            <option key={client.client_id} value={client.client_id}>
              {client.client_id}
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label className="form-label">Category</label>
        <select
          className="form-input"
          value={filters.category}
          onChange={(e) => handleChange('category', e.target.value)}
        >
          <option value="">All Categories</option>
          {Object.entries(ACTIVITY_CATEGORIES).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label className="form-label">Start Date</label>
        <Input
          type="datetime-local"
          value={filters.start_date || ''}
          onChange={(e) => handleChange('start_date', e.target.value)}
        />
      </div>
      
      <div className="form-group">
        <label className="form-label">End Date</label>
        <Input
          type="datetime-local"
          value={filters.end_date || ''}
          onChange={(e) => handleChange('end_date', e.target.value)}
        />
      </div>
      
      <div className="form-actions">
        <Button variant="secondary" onClick={handleReset}>
          Reset
        </Button>
        <Button variant="primary" onClick={handleApply}>
          Apply Filters
        </Button>
      </div>
    </div>
  )
}

export default ActivityFilters
