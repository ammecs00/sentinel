import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@contexts'
import { Layout } from '@components/layout'
import { Login, ChangePassword } from '@components/features/auth'
import { LoadingSpinner } from '@components/common'

// Lazy load pages
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'))
const ClientsPage = React.lazy(() => import('./pages/ClientsPage'))
const ActivitiesPage = React.lazy(() => import('./pages/ActivitiesPage'))
const ApiKeysPage = React.lazy(() => import('./pages/ApiKeysPage'))
const SettingsPage = React.lazy(() => import('./pages/SettingsPage'))

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  
  console.log('PrivateRoute - isAuthenticated:', isAuthenticated, 'loading:', loading)
  
  if (loading) {
    return (
      <div className="page-loading">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    )
  }
  
  if (!isAuthenticated) {
    console.log('PrivateRoute - Redirecting to login')
    return <Navigate to="/login" replace />
  }
  
  return children
}

const AdminRoute = ({ children }) => {
  const { isAuthenticated, isAdmin, loading, user } = useAuth()
  
  console.log('AdminRoute - isAuthenticated:', isAuthenticated, 'isAdmin:', isAdmin, 'loading:', loading, 'user:', user)
  
  if (loading) {
    return (
      <div className="page-loading">
        <LoadingSpinner size="lg" text="Checking permissions..." />
      </div>
    )
  }
  
  if (!isAuthenticated) {
    console.log('AdminRoute - Not authenticated, redirecting to login')
    return <Navigate to="/login" replace />
  }
  
  if (!isAdmin) {
    console.log('AdminRoute - Not admin, redirecting to dashboard')
    return <Navigate to="/dashboard" replace />
  }
  
  console.log('AdminRoute - Access granted')
  return children
}

const AppRouter = () => {
  const { isAuthenticated, forcePasswordChange, loading } = useAuth()
  
  console.log('AppRouter - isAuthenticated:', isAuthenticated, 'forcePasswordChange:', forcePasswordChange, 'loading:', loading)
  
  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="page-loading">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    )
  }
  
  return (
    <React.Suspense fallback={
      <div className="page-loading">
        <LoadingSpinner size="lg" text="Loading page..." />
      </div>
    }>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              forcePasswordChange ? (
                <Navigate to="/change-password" replace />
              ) : (
                <Navigate to="/dashboard" replace />
              )
            ) : (
              <Login />
            )
          }
        />
        
        {/* Password change route */}
        <Route
          path="/change-password"
          element={
            <PrivateRoute>
              <ChangePassword forceChange={forcePasswordChange} />
            </PrivateRoute>
          }
        />
        
        {/* Protected routes */}
        <Route
          path="/"
          element={
            <PrivateRoute>
              {forcePasswordChange ? (
                <Navigate to="/change-password" replace />
              ) : (
                <Layout />
              )}
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="clients" element={<ClientsPage />} />
          <Route path="activities" element={<ActivitiesPage />} />
          <Route path="settings" element={<SettingsPage />} />
          
          {/* Admin only routes */}
          <Route
            path="api-keys"
            element={
              <AdminRoute>
                <ApiKeysPage />
              </AdminRoute>
            }
          />
        </Route>
        
        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </React.Suspense>
  )
}

export default AppRouter