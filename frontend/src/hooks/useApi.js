import { useState, useCallback, useEffect, useRef } from 'react'

export const useApi = (apiFunction) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const isMounted = useRef(true)
  
  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
    }
  }, [])
  
  const execute = useCallback(async (...args) => {
    if (!isMounted.current) return { success: false, error: 'Component unmounted' }
    
    try {
      setLoading(true)
      setError(null)
      
      const result = await apiFunction(...args)
      
      if (isMounted.current) {
        if (result.success) {
          setData(result.data || result)
          return { success: true, data: result.data || result }
        } else {
          setError(result.error)
          return { success: false, error: result.error }
        }
      }
    } catch (err) {
      const errorMessage = err.message || 'An error occurred'
      if (isMounted.current) {
        setError(errorMessage)
      }
      return { success: false, error: errorMessage }
    } finally {
      if (isMounted.current) {
        setLoading(false)
      }
    }
  }, [apiFunction])
  
  const reset = useCallback(() => {
    if (!isMounted.current) return
    setData(null)
    setError(null)
    setLoading(false)
  }, [])
  
  return { data, loading, error, execute, reset }
}