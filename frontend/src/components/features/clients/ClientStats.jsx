import React from 'react'
import { useClientStats } from '@hooks'
import { Card, LoadingSpinner } from '@components/common'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

const ClientStats = () => {
  const { stats, loading, error } = useClientStats()
  
  if (loading) {
    return (
      <Card title="Client Statistics">
        <LoadingSpinner text="Loading statistics..." />
      </Card>
    )
  }
  
  if (error) {
    return (
      <Card title="Client Statistics">
        <div className="error-state">
          <p>Failed to load statistics: {error}</p>
        </div>
      </Card>
    )
  }
  
  const chartData = Object.entries(stats?.clients_by_type || {}).map(([name, value]) => ({
    name: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value
  }))
  
  return (
    <Card title="Client Distribution" subtitle="Clients by type">
      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="empty-state">
          <p>No client data available</p>
        </div>
      )}
    </Card>
  )
}

export default ClientStats
