import { useEffect, useRef } from 'react'
import useStore from '../store/useStore'

const WS_URL = import.meta.env.VITE_API_URL 
  ? import.meta.env.VITE_API_URL.replace('http', 'ws') + '/ws'
  : 'ws://localhost:8000/ws'


export const useWebSocket = () => {
  const wsRef = useRef(null)
  const { setLivePrice, setAnalysis, addTrade, setIsRunning } = useStore()
  
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(WS_URL)
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected')
        wsRef.current = ws
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          switch (message.type) {
            case 'connection_established':
              console.log('🔌 Connection established:', message.data.message)
              break
              
            case 'live_price_update':
              setLivePrice(message.data)
              break
              
            case 'zone_analysis_complete':
              setAnalysis(message.data)
              break
              
            case 'trade_identified':
              addTrade(message.data)
              break
              
            case 'system_status':
              setIsRunning(message.data.running)
              break

            case 'continuous_monitoring':
              // NEW: Handle continuous mode updates
              setContinuousMode(message.data.active)
              break
            
            case 'config_updated':
              console.log('⚙️ Config updated:', message.data.updated_fields)
              break
              
            default:
              console.log('Unknown message type:', message.type)
          }
        } catch (error) {
          console.error('WebSocket message error:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
      }
      
      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected. Reconnecting...')
        setTimeout(connectWebSocket, 3000)
      }
      
      return ws
    }
    
    const ws = connectWebSocket()
    
    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [setLivePrice, setAnalysis, addTrade, setIsRunning])
  
  return wsRef.current
}

