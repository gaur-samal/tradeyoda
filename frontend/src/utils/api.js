import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// System endpoints
export const getStatus = () => api.get('/api/status')
export const startTrading = () => api.post('/api/start')
export const stopTrading = () => api.post('/api/stop')
export const getMonitoringStatus = () => api.get('/api/monitoring-status')

// Analysis endpoints
export const runZoneAnalysis = () => api.post('/api/run-zone-analysis')
export const runTradeIdentification = () => api.post('/api/run-trade-identification')
export const getAnalysis = () => api.get('/api/analysis')

// Trading endpoints
export const getTrades = () => api.get('/api/trades')
export const getActiveTrades = () => api.get('/api/trades/active')
export const getTradeStatistics = () => api.get('/api/trades/statistics')

// Market data endpoints
export const getLivePrice = () => api.get('/api/market/live-price')

// Continuous monitoring endpoints
export const startContinuousMonitoring = () => api.post('/api/start-continuous')
export const stopContinuousMonitoring = () => api.post('/api/stop-continuous')


// Config endpoints
export const getConfig = () => api.get('/api/config')
export const updateConfig = (updates) => api.post('/api/config/update', updates)

export default api

