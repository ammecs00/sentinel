import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, NotificationProvider } from '@contexts'
import AppRouter from './router'
import './styles/globals.css'
import './styles/components.css'
import './styles/utilities.css'

function App() {
  return (
    <BrowserRouter>
      <NotificationProvider>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </NotificationProvider>
    </BrowserRouter>
  )
}

export default App
