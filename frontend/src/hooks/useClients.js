import { useState, useEffect, useCallback, useRef } from 'react'
import { clientsService } from '@services'

export const useClients = (autoFetch = true, params = {}) => {
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const isMounted = useRef(true)
  const hasFetched = useRef(false)
  
  const fetchClients = useCallback(async (fetchParams = {}) => {
    if (!isMounted.current) return
    
    try {
      setLoading(true)
      setError(null)
      
      const mergedParams = { ...params, ...fetchParams }
      const result = await clientsService.getClients(mergedParams)
      
      if (isMounted.current) {
        if (result.success) {
          setClients(result.clients)
        } else {
          setError(result.error)
        }
      }
    } catch (err) {
      if (isMounted.current) {
        setError(err.message)
      }
    } finally {
      if (isMounted.current) {
        setLoading(false)
      }
    }
  }, []) // Empty - stable function
  
  useEffect(() => {
    isMounted.current = true
    
    if (autoFetch && !hasFetched.current) {
      hasFetched.current = true
      fetchClients()
    }
    
    return () => {
      isMounted.current = false
    }
  }, []) // Empty - only run once on mount
  
  return {
    clients,
    loading,
    error,
    refetch: fetchClients
  }
}

export const useClient = (clientId) => {
  const [client, setClient] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const isMounted = useRef(true)
  const lastFetchedId = useRef(null)
  
  const fetchClient = useCallback(async () => {
    if (!clientId || !isMounted.current) return
    
    try {
      setLoading(true)
      setError(null)
      
      const result = await clientsService.getClient(clientId)
      
      if (isMounted.current) {
        if (result.success) {
          setClient(result.client)
        } else {
          setError(result.error)
        }
      }
    } catch (err) {
      if (isMounted.current) {
        setError(err.message)
      }
    } finally {
      if (isMounted.current) {
        setLoading(false)
      }
    }
  }, [clientId])
  
  useEffect(() => {
    isMounted.current = true
    
    // Only fetch if clientId changed
    if (clientId && clientId !== lastFetchedId.current) {
      lastFetchedId.current = clientId
      fetchClient()
    }
    
    return () => {
      isMounted.current = false
    }
  }, [clientId]) // Only re-run if clientId changes
  
  return {
    client,
    loading,
    error,
    refetch: fetchClient
  }
}

export const useClientStats = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const isMounted = useRef(true)
  const hasFetched = useRef(false)
  
  const fetchStats = useCallback(async () => {
    if (!isMounted.current) return
    
    try {
      setLoading(true)
      setError(null)
      
      const result = await clientsService.getClientStats()
      
      if (isMounted.current) {
        if (result.success) {
          setStats(result.stats)
        } else {
          setError(result.error)
        }
      }
    } catch (err) {
      if (isMounted.current) {
        setError(err.message)
      }
    } finally {
      if (isMounted.current) {
        setLoading(false)
      }
    }
  }, []) // Empty - stable function
  
  useEffect(() => {
    isMounted.current = true
    
    if (!hasFetched.current) {
      hasFetched.current = true
      fetchStats()
    }
    
    return () => {
      isMounted.current = false
    }
  }, []) // Empty - only run once on mount
  
  return {
    stats,
    loading,
    error,
    refetch: fetchStats
  }
}