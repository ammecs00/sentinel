import React, { useState, useEffect } from 'react'
import { authService } from '@services'
import { Card, Table, Button, Modal, Input, Alert } from '@components/common'
import { useNotification } from '@contexts'
import { formatDate, copyToClipboard } from '@utils'
import { Key, Plus, Trash2, Copy, Check } from 'lucide-react'

const ApiKeys = () => {
  const [apiKeys, setApiKeys] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [creating, setCreating] = useState(false)
  const [newKeyData, setNewKeyData] = useState(null)
  const [copiedKey, setCopiedKey] = useState(false)
  
  const { success, error: notifyError } = useNotification()
  
  useEffect(() => {
    console.log('ApiKeys component mounted')
    loadApiKeys()
  }, [])
  
  const loadApiKeys = async () => {
    console.log('Loading API keys...')
    setLoading(true)
    setError(null)
    
    try {
      const result = await authService.getApiKeys()
      console.log('API Keys result:', result)
      
      if (result.success) {
        setApiKeys(result.apiKeys || [])
      } else {
        const errorMsg = result.error || 'Failed to load API keys'
        setError(errorMsg)
        notifyError(errorMsg)
      }
    } catch (err) {
      console.error('Error loading API keys:', err)
      const errorMsg = err.message || 'Failed to load API keys'
      setError(errorMsg)
      notifyError(errorMsg)
    } finally {
      setLoading(false)
    }
  }
  
  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      notifyError('Please enter a name for the API key')
      return
    }
    
    setCreating(true)
    const result = await authService.createApiKey(newKeyName.trim())
    
    if (result.success) {
      setNewKeyData(result.apiKey)
      setNewKeyName('')
      loadApiKeys()
      success('API key created successfully')
    } else {
      notifyError(result.error || 'Failed to create API key')
      setShowCreateModal(false)
    }
    setCreating(false)
  }
  
  const handleCopyKey = async (key) => {
    const result = await copyToClipboard(key)
    if (result.success) {
      setCopiedKey(true)
      success('API key copied to clipboard')
      setTimeout(() => setCopiedKey(false), 2000)
    } else {
      notifyError('Failed to copy API key')
    }
  }
  
  const handleRevokeKey = async (keyId, keyName) => {
    if (!window.confirm(`Are you sure you want to revoke the API key "${keyName}"? This action cannot be undone.`)) {
      return
    }
    
    const result = await authService.revokeApiKey(keyId)
    
    if (result.success) {
      loadApiKeys()
      success('API key revoked successfully')
    } else {
      notifyError(result.error || 'Failed to revoke API key')
    }
  }
  
  const handleCloseNewKeyModal = () => {
    setNewKeyData(null)
    setShowCreateModal(false)
  }
  
  const columns = [
    {
      key: 'name',
      header: 'Name',
      width: '25%'
    },
    {
      key: 'key_prefix',
      header: 'Key Prefix',
      width: '15%',
      render: (apiKey) => (
        <span className="font-mono text-sm">{apiKey.key_prefix}...</span>
      )
    },
    {
      key: 'usage_count',
      header: 'Usage Count',
      width: '15%',
      render: (apiKey) => apiKey.usage_count.toLocaleString()
    },
    {
      key: 'last_used',
      header: 'Last Used',
      width: '20%',
      render: (apiKey) => apiKey.last_used ? formatDate(apiKey.last_used, 'PPp') : 'Never'
    },
    {
      key: 'created_at',
      header: 'Created',
      width: '15%',
      render: (apiKey) => formatDate(apiKey.created_at, 'PP')
    },
    {
      key: 'actions',
      header: '',
      width: '10%',
      sortable: false,
      render: (apiKey) => (
        <Button
          variant="danger"
          size="sm"
          icon={Trash2}
          onClick={() => handleRevokeKey(apiKey.id, apiKey.name)}
        >
          Revoke
        </Button>
      )
    }
  ]
  
  console.log('Render state:', { loading, error, apiKeysCount: apiKeys.length })
  
  if (loading) {
    return (
      <Card title="API Keys">
        <div className="loading-spinner">
          <p>Loading API keys...</p>
        </div>
      </Card>
    )
  }
  
  if (error) {
    return (
      <Card title="API Keys">
        <Alert
          type="error"
          title="Error Loading API Keys"
          message={error}
        />
        <div className="mt-4">
          <Button onClick={loadApiKeys}>
            Retry
          </Button>
        </div>
      </Card>
    )
  }
  
  return (
    <>
      <Card
        title="API Keys"
        subtitle="Manage API keys for monitoring clients"
        actions={
          <Button
            variant="primary"
            icon={Plus}
            onClick={() => setShowCreateModal(true)}
          >
            Create API Key
          </Button>
        }
      >
        <Alert
          type="info"
          message="API keys are used by monitoring clients to authenticate with the server. Keep them secure and never share them publicly."
          className="mb-4"
        />
        
        <Table
          columns={columns}
          data={apiKeys}
          loading={loading}
          emptyMessage="No API keys created yet"
        />
      </Card>
      
      {/* Create API Key Modal */}
      <Modal
        isOpen={showCreateModal && !newKeyData}
        onClose={() => setShowCreateModal(false)}
        title="Create New API Key"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Key Name"
            placeholder="e.g., Production Server 1"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            helperText="Choose a descriptive name to identify this key"
            autoFocus
          />
          
          <div className="form-actions">
            <Button
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
              disabled={creating}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateKey}
              loading={creating}
              disabled={creating || !newKeyName.trim()}
            >
              Create Key
            </Button>
          </div>
        </div>
      </Modal>
      
      {/* New API Key Display Modal */}
      <Modal
        isOpen={!!newKeyData}
        onClose={handleCloseNewKeyModal}
        title="API Key Created"
        size="md"
        closeOnOverlayClick={false}
      >
        <div className="space-y-4">
          <Alert
            type="warning"
            title="Important!"
            message="This is the only time you will see this API key. Make sure to copy it now and store it securely."
          />
          
          <div className="detail-item">
            <label>Key Name</label>
            <span>{newKeyData?.name}</span>
          </div>
          
          <div className="detail-item">
            <label>API Key</label>
            <div className="flex gap-2">
              <code className="flex-1 p-3 bg-gray-100 rounded font-mono text-sm break-all">
                {newKeyData?.key}
              </code>
              <Button
                variant="secondary"
                icon={copiedKey ? Check : Copy}
                onClick={() => handleCopyKey(newKeyData?.key)}
                disabled={copiedKey}
              >
                {copiedKey ? 'Copied' : 'Copy'}
              </Button>
            </div>
          </div>
          
          <div className="detail-item">
            <label>Usage Instructions</label>
            <div className="text-sm text-gray-600 space-y-2">
              <p>Use this API key in your monitoring client configuration:</p>
              <pre className="p-3 bg-gray-100 rounded overflow-auto">
{`{
  "api_key": "${newKeyData?.key}",
  "server_url": "${window.location.origin}"
}`}
              </pre>
            </div>
          </div>
          
          <div className="form-actions">
            <Button
              variant="primary"
              onClick={handleCloseNewKeyModal}
              className="w-full"
            >
              I've Saved the Key
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}

export default ApiKeys