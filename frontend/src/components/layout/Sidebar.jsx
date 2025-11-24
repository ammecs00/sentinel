import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '@contexts' 
import {
  LayoutDashboard,
  Monitor,
  Activity,
  Key,
  Settings,
  X,
  PanelLeftClose
} from 'lucide-react'

const Sidebar = ({ isOpen, onClose, onToggle }) => {
  const { user } = useAuth()
  
  const navItems = [
    {
      to: '/dashboard',
      icon: LayoutDashboard,
      label: 'Dashboard'
    },
    {
      to: '/clients',
      icon: Monitor,
      label: 'Clients'
    },
    {
      to: '/activities',
      icon: Activity,
      label: 'Activities'
    },
    // Safe optional chaining handles cases where user is null (not logged in)
    ...(user?.is_admin ? [{
      to: '/api-keys',
      icon: Key,
      label: 'API Keys'
    }] : []),
    {
      to: '/settings',
      icon: Settings,
      label: 'Settings'
    }
  ]
  
  return (
    <>
      <div 
        className={`sidebar-overlay ${isOpen ? 'active' : ''}`}
        onClick={onClose}
      />
      
      <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-title">Navigation</h2>
          
          <button 
            className="sidebar-toggle" 
            onClick={onToggle} 
            title="Collapse Sidebar"
          >
            <PanelLeftClose size={20} />
          </button>

          <button className="sidebar-close-mobile" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => 
                `nav-item ${isActive ? 'active' : ''}`
              }
              onClick={() => {
                if (window.innerWidth <= 1024) onClose()
              }}
            >
              <item.icon className="nav-icon" size={20} />
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        
        <div className="sidebar-footer">
          <div className="sidebar-info">
            <p className="text-sm text-gray-500">Sentinel v2.0.0</p>
            <p className="text-xs text-gray-400">© 2024 All rights reserved</p>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar