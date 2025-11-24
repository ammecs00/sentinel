import React, { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
// Assuming Header is in the same directory and exports correctly
// FIX: Added .jsx extension to resolve import errors
import Header from './Header.jsx' 
import Sidebar from './Sidebar.jsx'

const Layout = () => {
  // Initialize based on screen width: Open on Desktop (>1024px), Closed on Mobile
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 1024)
  
  // Add resize listener to handle responsive changes automatically
  useEffect(() => {
    const handleResize = () => {
      // If resizing to mobile width, ensure it's closed (to prevent trapping the user)
      if (window.innerWidth <= 1024) {
        setSidebarOpen(false)
      } else {
        // If resizing to desktop width, ensure it's open by default
        setSidebarOpen(true)
      }
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }
  
  const closeSidebar = () => {
    setSidebarOpen(false)
  }
  
  return (
    <div className="app-layout">
      {/* The sidebar component */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={closeSidebar} 
        onToggle={toggleSidebar} 
      />
      
      {/* Main content area */}
      <div className="app-main">
        {/* Header needs to know how to toggle the sidebar (for mobile/global menu button) */}
        <Header onMenuClick={toggleSidebar} />
        
        <main className="app-content">
          {/* Renders child routes */}
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout