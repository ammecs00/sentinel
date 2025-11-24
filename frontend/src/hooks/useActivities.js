import { useState, useEffect, useCallback, useRef } from 'react'
import { activitiesService } from '@services'

export const useActivities = (autoFetch = true, params = {}) => {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const isMounted = useRef(true)
  const hasFetched = useRef(false)
  
  const fetchActivities = useCallback(async (fetchParams = {}) => {
    if (!isMounted.current) return
    
    try {
      setLoading(true)
      setError(null)
      
      const mergedParams = { ...params, ...fetchParams }
      const result = await activitiesService.getActivities(mergedParams)
      
      if (isMounted.current) {
        if (result.success) {
          setActivities(result.activities)
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
      fetchActivities()
    }
    
    return () => {
      isMounted.current = false
    }
  }, []) // Empty - only run once on mount
  
  return {
    activities,
    loading,
    error,
    refetch: fetchActivities
  }
}

export const useActivity = (activityId) => {
  const [activity, setActivity] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const isMounted = useRef(true)
  const lastFetchedId = useRef(null)
  
  const fetchActivity = useCallback(async () => {
    if (!activityId || !isMounted.current) return
    
    try {
      setLoading(true)
      setError(null)
      
      const result = await activitiesService.getActivity(activityId)
      
      if (isMounted.current) {
        if (result.success) {
          setActivity(result.activity)
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
  }, [activityId])
  
  useEffect(() => {
    isMounted.current = true
    
    // Only fetch if activityId changed
    if (activityId && activityId !== lastFetchedId.current) {
      lastFetchedId.current = activityId
      fetchActivity()
    }
    
    return () => {
      isMounted.current = false
    }
  }, [activityId]) // Only re-run if activityId changes
  
  return {
    activity,
    loading,
    error,
    refetch: fetchActivity
  }
}

export const useActivityStats = (params = {}) => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const isMounted = useRef(true)
  const hasFetched = useRef(false)
  
  const fetchStats = useCallback(async (fetchParams = {}) => {
    if (!isMounted.current) return
    
    try {
      setLoading(true)
      setError(null)
      
      const mergedParams = { ...params, ...fetchParams }
      const result = await activitiesService.getActivityStats(mergedParams)
      
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