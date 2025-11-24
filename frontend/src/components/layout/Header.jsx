import React from 'react'
import { Menu, LogOut, User, Bell } from 'lucide-react'
import { useAuth } from '@contexts'

const Header = ({ onMenuClick }) => {
  const { user, logout } = useAuth()
  
  return (
    <header className="header">
      <div className="header-left">
        <button className="menu-button" onClick={onMenuClick}>
          <Menu size={24} />
        </button>
        
        <div className="header-brand">
          <div className="brand-logo">S</div>
          <div className="brand-info">
            <h1 className="brand-name">Sentinel</h1>
            <span className="brand-subtitle">Monitoring System</span>
          </div>
        </div>
      </div>
      
      <div className="header-right">
        <button className="header-icon-button">
          <Bell size={20} />
        </button>
        
        <div className="user-menu">
          <div className="user-info">
            <User size={18} />
            <div className="user-details">
              <span className="user-name">{user?.username}</span>
              <span className="user-role">{user?.is_admin ? 'Administrator' : 'User'}</span>
            </div>
          </div>
          
          <button className="logout-button" onClick={logout} title="Logout">
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header