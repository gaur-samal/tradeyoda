import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Filter, Download } from 'lucide-react'
import useStore from '../store/useStore'
import { getTrades, getTradeStatistics } from '../utils/api'
import TradeCard from '../components/TradeCard'
import MetricCard from '../components/MetricCard'

export default function Trades() {
  const { trades, setTrades, statistics, setStatistics } = useStore()
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState(['ACTIVE', 'PENDING'])
  const [directionFilter, setDirectionFilter] = useState(['CALL', 'PUT'])
  
  useEffect(() => {
    fetchTrades()
    fetchStatistics()
  }, [])
  
  const fetchTrades = async () => {
    setLoading(true)
    try {
      const { data } = await getTrades()
      setTrades(data.trades)
    } catch (error) {
      console.error('Failed to fetch trades:', error)
    } finally {
      setLoading(false)
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
  
  const filteredTrades = trades.filter(trade => {
    const statusMatch = statusFilter.includes(trade.status)
    const directionMatch = directionFilter.includes(trade.direction)
    return statusMatch && directionMatch
  })
  
  const handleExport = () => {
    const csv = [
      ['Timestamp', 'Direction', 'Entry', 'Target', 'Stop Loss', 'Status', 'P&L', 'Probability'].join(','),
      ...filteredTrades.map(t => [
        new Date(t.timestamp).toISOString(),
        t.direction,
        t.entry_price,
        t.target_price,
        t.stop_loss,
        t.status,
        t.pnl,
        t.probability
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trades_${new Date().toISOString()}.csv`
    a.click()
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">🎯 Active Trades Monitor</h1>
        <button onClick={handleExport} className="btn-secondary flex items-center gap-2">
          <Download className="w-5 h-5" />
          Export CSV
        </button>
      </div>
      
      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <MetricCard
          label="Total Trades"
          value={statistics.total_trades || 0}
        />
        <MetricCard
          label="Win Rate"
          value={`${statistics.win_rate?.toFixed(1) || 0}%`}
        />
        <MetricCard
          label="Total P&L"
          value={`₹${statistics.total_pnl?.toFixed(2) || 0}`}
          delta={statistics.total_pnl > 0 ? `+${statistics.total_pnl?.toFixed(2)}` : ''}
          trend={statistics.total_pnl > 0 ? 'up' : 'down'}
        />
        <MetricCard
          label="Profit Factor"
          value={statistics.profit_factor?.toFixed(2) || 0}
        />
      </div>
      
      {/* Filters */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold">Filters</h3>
        </div>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Status</label>
            <div className="flex flex-wrap gap-2">
              {['ACTIVE', 'PENDING', 'CLOSED', 'PAPER'].map(status => (
                <button
                  key={status}
                  onClick={() => {
                    if (statusFilter.includes(status)) {
                      setStatusFilter(statusFilter.filter(s => s !== status))
                    } else {
                      setStatusFilter([...statusFilter, status])
                    }
                  }}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    statusFilter.includes(status)
                      ? 'bg-purple-500 text-white'
                      : 'bg-white/5 text-gray-400 hover:bg-white/10'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Direction</label>
            <div className="flex flex-wrap gap-2">
              {['CALL', 'PUT'].map(direction => (
                <button
                  key={direction}
                  onClick={() => {
                    if (directionFilter.includes(direction)) {
                      setDirectionFilter(directionFilter.filter(d => d !== direction))
                    } else {
                      setDirectionFilter([...directionFilter, direction])
                    }
                  }}
                  className={`px-4 py-2 rounded-lg transition-all ${
                    directionFilter.includes(direction)
                      ? 'bg-purple-500 text-white'
                      : 'bg-white/5 text-gray-400 hover:bg-white/10'
                  }`}
                >
                  {direction}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* Trade History */}
      <div>
        <h2 className="text-xl font-bold mb-4">
          Trade History ({filteredTrades.length})
        </h2>
        
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
          </div>
        ) : filteredTrades.length === 0 ? (
          <div className="card p-12 text-center">
            <div className="text-6xl mb-4">📭</div>
            <h3 className="text-xl font-bold mb-2">No Trades Found</h3>
            <p className="text-gray-400">
              {trades.length === 0 
                ? 'No trades executed yet. Run trade identification from dashboard.'
                : 'No trades match the selected filters.'}
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredTrades.map((trade, idx) => (
              <TradeCard key={idx} trade={trade} index={idx} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

