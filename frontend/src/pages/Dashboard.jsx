import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Play, Square, Activity, TrendingUp, Zap, BarChart, Pause } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'
import useStore from '../store/useStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { 
  getStatus, 
  startTrading, 
  stopTrading, 
  runZoneAnalysis, 
  runTradeIdentification,
  getTradeStatistics,
  startContinuousMonitoring,
  stopContinuousMonitoring,
  getMonitoringStatus
} from '../utils/api'
import MetricCard from '../components/MetricCard'
import LivePriceCard from '../components/LivePriceCard'
import ZoneCard from '../components/ZoneCard'

export default function Dashboard() {
  // Use global state from Zustand (includes continuousMode)
  const { 
    isRunning, 
    setIsRunning, 
    analysis, 
    trades, 
    statistics, 
    setStatistics,
    continuousMode,
    setContinuousMode
  } = useStore()
  
  const [loading, setLoading] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [tradeLoading, setTradeLoading] = useState(false)
  
  // Connect WebSocket
  useWebSocket()
  
  // Fetch initial data
  useEffect(() => {
    fetchStatus()
    fetchStatistics()
    fetchMonitoringStatus()
  }, [])
  
  const fetchStatus = async () => {
    try {
      const { data } = await getStatus()
      setIsRunning(data.running)
    } catch (error) {
      console.error('Failed to fetch status:', error)
      toast.error('Failed to fetch system status')
    }
  }
  
  const fetchStatistics = async () => {
    try {
      const { data } = await getTradeStatistics()
      setStatistics(data)
    } catch (error) {
      console.error('Failed to fetch statistics:', error)
    }
  }
  
  const fetchMonitoringStatus = async () => {
    try {
      const { data } = await getMonitoringStatus()
      setContinuousMode(data.continuous_mode)
    } catch (error) {
      console.error('Failed to fetch monitoring status:', error)
    }
  }
  
  const handleStart = async () => {
    setLoading(true)
    try {
      await startTrading()
      setIsRunning(true)
      toast.success('🚀 Trade Yoda activated!', { duration: 3000 })
    } catch (error) {
      console.error('Failed to start:', error)
      toast.error('Failed to start system: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleStop = async () => {
    setLoading(true)
    try {
      // Stop continuous mode first if active
      if (continuousMode) {
        await stopContinuousMonitoring()
        setContinuousMode(false)
      }
      await stopTrading()
      setIsRunning(false)
      toast.success('⏹️ Trade Yoda stopped', { duration: 3000 })
    } catch (error) {
      console.error('Failed to stop:', error)
      toast.error('Failed to stop system: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleStartContinuous = async () => {
    setLoading(true)
    const loadingToast = toast.loading('Activating continuous auto-trading...')
    
    try {
      await startContinuousMonitoring()
      setContinuousMode(true)
      toast.success(
        '🤖 Continuous auto-trading activated!\n\n' +
        '• Zone analysis every 15 minutes\n' +
        '• Trade identification every 5 minutes\n' +
        '• Auto-exit at 3:25 PM\n' +
        '• No new trades after 3:00 PM',
        { duration: 6000, id: loadingToast }
      )
    } catch (error) {
      console.error('Failed to start continuous monitoring:', error)
      toast.error('Failed to start auto-trading: ' + (error.response?.data?.error || error.message), { id: loadingToast })
    } finally {
      setLoading(false)
    }
  }
  
  const handleStopContinuous = async () => {
    setLoading(true)
    const loadingToast = toast.loading('Stopping continuous auto-trading...')
    
    try {
      await stopContinuousMonitoring()
      setContinuousMode(false)
      toast.success('⏸️ Continuous auto-trading stopped.\n\nManual mode activated.', { duration: 4000, id: loadingToast })
    } catch (error) {
      console.error('Failed to stop continuous monitoring:', error)
      toast.error('Failed to stop auto-trading: ' + (error.response?.data?.error || error.message), { id: loadingToast })
    } finally {
      setLoading(false)
    }
  }
  
  const handleZoneAnalysis = async () => {
    setAnalysisLoading(true)
    const loadingToast = toast.loading('Running zone analysis...')
    
    try {
        const { data } = await runZoneAnalysis()
        
        if (data.success) {
        const demandCount = data.data?.zones?.demand_zones?.length || 0
        const supplyCount = data.data?.zones?.supply_zones?.length || 0
        
        toast.success(
            `✅ Zone analysis complete!\n\nFound:\n• ${demandCount} demand zones\n• ${supplyCount} supply zones`,
            { duration: 5000, id: loadingToast }
        )
        fetchStatistics()
        } else {
        // Use regular toast with custom style for info
        toast(data.message || 'No zones identified', { 
            id: loadingToast,
            icon: 'ℹ️',
            duration: 5000,
            style: {
            background: '#1f2937',
            border: '1px solid #3b82f6',
            color: '#fff',
            }
        })
        }
    } catch (error) {
        console.error('Failed to run analysis:', error)
        
        const errorMsg = error.response?.data?.error || error.message || 'Unknown error'
        
        if (errorMsg.includes('market hours') || errorMsg.includes('Outside market')) {
        toast.error(
            '⏰ Outside Market Hours\n\nZone analysis can only run during:\n• Monday to Friday\n• 9:15 AM to 3:30 PM IST\n\nPlease try again during trading hours.',
            { duration: 6000, id: loadingToast }
        )
        } else {
        toast.error('Analysis failed: ' + errorMsg, { id: loadingToast })
        }
    } finally {
        setAnalysisLoading(false)
    }
  } 
  const handleTradeIdentification = async () => {
    setTradeLoading(true)
    const loadingToast = toast.loading('Identifying trade opportunities...')
    
    try {
        const { data } = await runTradeIdentification()
        
        if (data.success) {
        toast.success(
            '✅ Trade identified and executed!\n\nCheck the Trades page for details.',
            { duration: 5000, id: loadingToast }
        )
        fetchStatistics()
        } else {
        // Use regular toast with custom style for info
        toast(data.message || 'No trade opportunities found at this time.', { 
            id: loadingToast,
            icon: 'ℹ️',
            duration: 5000,
            style: {
            background: '#1f2937',
            border: '1px solid #3b82f6',
            color: '#fff',
            }
        })
        }
    } catch (error) {
        console.error('Failed to identify trade:', error)
        
        const errorMsg = error.response?.data?.error || error.message || 'Unknown error'
        
        if (errorMsg.includes('market hours') || errorMsg.includes('Outside market')) {
        toast.error(
            '⏰ Outside Market Hours\n\nTrade identification can only run during:\n• Monday to Friday\n• 9:15 AM to 3:30 PM IST\n\nPlease try again during trading hours.',
            { duration: 6000, id: loadingToast }
        )
        } else {
        toast.error('Trade identification failed: ' + errorMsg, { id: loadingToast })
        }
    } finally {
        setTradeLoading(false)
    }
  }
 
  const activeTrades = trades.filter(t => t.status === 'ACTIVE').length
  
  return (
    <div className="space-y-6">
      {/* Toast Container */}
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#fff',
            border: '1px solid #374151',
            borderRadius: '12px',
            padding: '16px',
            maxWidth: '500px',
          },
          success: {
            style: {
              background: '#1f2937',
              border: '1px solid #10b981',
            },
          },
          error: {
            style: {
              background: '#1f2937',
              border: '1px solid #ef4444',
            },
          },
          loading: {
            style: {
              background: '#1f2937',
              border: '1px solid #8b5cf6',
            },
          },
        }}
      />

      {/* Control Panel */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">System Control</h2>
            <p className="text-gray-400">Manage Trade Yoda trading system</p>
          </div>
          
          <div className="flex gap-4">
            {!isRunning ? (
              <button
                onClick={handleStart}
                disabled={loading}
                className="btn-primary flex items-center gap-2"
              >
                <Play className="w-5 h-5" />
                {loading ? 'Starting...' : 'Start System'}
              </button>
            ) : (
              <>
                {/* Continuous Monitoring Toggle */}
                {!continuousMode ? (
                  <button
                    onClick={handleStartContinuous}
                    disabled={loading}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-green-500/30 flex items-center gap-2"
                  >
                    <Zap className="w-5 h-5" />
                    {loading ? 'Activating...' : 'Start Auto-Trading'}
                  </button>
                ) : (
                  <button
                    onClick={handleStopContinuous}
                    disabled={loading}
                    className="bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-orange-500/30 flex items-center gap-2"
                  >
                    <Pause className="w-5 h-5" />
                    {loading ? 'Stopping...' : 'Stop Auto-Trading'}
                  </button>
                )}
                
                <button
                  onClick={handleStop}
                  disabled={loading}
                  className="bg-red-500 hover:bg-red-600 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center gap-2"
                >
                  <Square className="w-5 h-5" />
                  {loading ? 'Stopping...' : 'Stop System'}
                </button>
              </>
            )}
          </div>
        </div>
        
        {/* Continuous Mode Status Banner */}
        {continuousMode && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="relative">
                <div className="w-4 h-4 bg-green-400 rounded-full animate-pulse"></div>
                <div className="absolute inset-0 w-4 h-4 bg-green-400 rounded-full animate-ping"></div>
              </div>
              <span className="font-bold text-green-400 text-lg">🤖 Continuous Auto-Trading Active</span>
            </div>
            <div className="grid md:grid-cols-2 gap-3 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-green-400">✅</span>
                <span className="text-gray-300">Zone analysis every 15 minutes</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-400">✅</span>
                <span className="text-gray-300">Trade identification every 5 minutes</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-yellow-400">⏰</span>
                <span className="text-gray-300">Auto-exit all positions at 3:25 PM</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-yellow-400">🚫</span>
                <span className="text-gray-300">No new trades after 3:00 PM</span>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-green-500/20">
              <p className="text-xs text-gray-400">
                💡 <strong>Tip:</strong> System will automatically monitor and execute trades based on your configured parameters. 
                Monitor the "Trades" page for real-time updates.
              </p>
            </div>
          </motion.div>
        )}
      </div>
      
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={Activity}
          label="System Status"
          value={isRunning ? '🟢 Active' : '🔴 Stopped'}
        />
        <MetricCard
          icon={TrendingUp}
          label="Active Trades"
          value={activeTrades}
        />
        <MetricCard
          icon={BarChart}
          label="Total P&L"
          value={`₹${statistics.total_pnl?.toFixed(2) || 0}`}
	  delta={statistics?.total_pnl !== undefined && statistics?.total_pnl !== null ? (statistics.total_pnl > 0 ? `+${statistics.total_pnl.toFixed(2)}` : statistics.total_pnl < 0 ? `${statistics.total_pnl.toFixed(2)}`: undefined) : undefined}
          trend={statistics.total_pnl > 0 ? 'up' : 'down'}
        />
        <MetricCard
          icon={Zap}
          label="Win Rate"
          value={`${statistics.win_rate?.toFixed(1) || 0}%`}
        />
      </div>
      
      {/* Live Price */}
      <LivePriceCard />
      
      {/* Manual Analysis Actions (Only show if continuous mode is OFF) */}
      {!continuousMode && (
        <div className="grid md:grid-cols-2 gap-6">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleZoneAnalysis}
            disabled={analysisLoading || !isRunning}
            className="card p-8 text-left hover:border-purple-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-xl font-bold mb-2">Run Zone Analysis</h3>
            <p className="text-gray-400 mb-4">15-minute cycle for supply/demand zone identification</p>
            <div className="text-purple-400 font-semibold">
              {analysisLoading ? 'Analyzing...' : 'Click to Run →'}
            </div>
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleTradeIdentification}
            disabled={tradeLoading || !isRunning}
            className="card p-8 text-left hover:border-purple-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-bold mb-2">Identify Trades</h3>
            <p className="text-gray-400 mb-4">5-minute cycle for trade opportunity identification</p>
            <div className="text-purple-400 font-semibold">
              {tradeLoading ? 'Identifying...' : 'Click to Run →'}
            </div>
          </motion.button>
        </div>
      )}
      
      {/* Info Banner for Continuous Mode */}
      {continuousMode && (
        <div className="card p-6 bg-blue-500/5 border-blue-500/20">
          <div className="flex items-start gap-4">
            <div className="text-3xl">ℹ️</div>
            <div>
              <h3 className="font-semibold text-lg mb-2">Automatic Mode Active</h3>
              <p className="text-gray-400 text-sm">
                Manual zone analysis and trade identification buttons are disabled while continuous auto-trading is active. 
                The system is automatically running these cycles in the background. Check the Analysis and Trades pages for updates.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Latest Analysis */}
      {analysis && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Latest Analysis</h2>
            <div className="text-sm text-gray-400">
              Updated {new Date(analysis.timestamp).toLocaleTimeString()}
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Demand Zones */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                Demand Zones
              </h3>
              <div className="space-y-3">
                {analysis.zones?.demand_zones?.slice(0, 5).map((zone, idx) => (
                  <ZoneCard key={idx} zone={zone} index={idx} type="demand" />
                ))}
                {!analysis.zones?.demand_zones?.length && (
                  <div className="card p-6 text-center text-gray-400">
                    No demand zones identified
                  </div>
                )}
              </div>
            </div>
            
            {/* Supply Zones */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                Supply Zones
              </h3>
              <div className="space-y-3">
                {analysis.zones?.supply_zones?.slice(0, 5).map((zone, idx) => (
                  <ZoneCard key={idx} zone={zone} index={idx} type="supply" />
                ))}
                {!analysis.zones?.supply_zones?.length && (
                  <div className="card p-6 text-center text-gray-400">
                    No supply zones identified
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

