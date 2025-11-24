import React from 'react'
import { ApiKeys } from '@components/features/settings'

const ApiKeysPage = () => {
  return (
    <div className="page">
      <div className="page-header">
        <h2>API Keys</h2>
        <p>Manage API keys for monitoring clients</p>
      </div>
      
      <ApiKeys />
    </div>
  )
}

export default ApiKeysPage
