import React from 'react'
import ChangePassword from '../auth/ChangePassword'

const SecuritySettings = () => {
  return (
    <div className="page">
      <div className="page-header">
        <h2>Security Settings</h2>
        <p>Manage your account security and password</p>
      </div>
      
      <ChangePassword forceChange={false} />
    </div>
  )
}

export default SecuritySettings
