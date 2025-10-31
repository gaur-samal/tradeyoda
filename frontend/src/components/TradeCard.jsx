import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Clock, CheckCircle, XCircle, FileText } from 'lucide-react'

export default function TradeCard({ trade, index }) {
  // Format expiry date
  const formatExpiry = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-GB', { 
        day: '2-digit', 
        month: 'short' 
      }).toUpperCase()
    } catch {
      return 'N/A'
    }
  }

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'N/A'
    }
  }

  // Status styling
  const getStatusStyle = (status) => {
    switch(status) {
      case 'ACTIVE':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50'
      case 'CLOSED':
        return 'bg-green-500/20 text-green-400 border-green-500/50'
      case 'PAPER':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
      case 'PENDING':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/50'
      case 'CANCELLED':
        return 'bg-red-500/20 text-red-400 border-red-500/50'
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50'
    }
  }

  // Status icon
  const getStatusIcon = (status) => {
    switch(status) {
      case 'ACTIVE':
        return <Clock className="w-4 h-4" />
      case 'CLOSED':
        return <CheckCircle className="w-4 h-4" />
      case 'PAPER':
        return <FileText className="w-4 h-4" />
      case 'CANCELLED':
        return <XCircle className="w-4 h-4" />
      default:
        return null
    }
  }

  // Direction styling
  const directionStyle = trade.option_type === 'CALL' || trade.direction === 'CALL'
    ? 'bg-green-500/20 text-green-400 border-green-500/50'
    : 'bg-red-500/20 text-red-400 border-red-500/50'

  const directionIcon = trade.option_type === 'CALL' || trade.direction === 'CALL'
    ? <TrendingUp className="w-4 h-4" />
    : <TrendingDown className="w-4 h-4" />

  // P&L styling
  const pnlColor = trade.pnl > 0 
    ? 'text-green-400' 
    : trade.pnl < 0 
      ? 'text-red-400' 
      : 'text-gray-400'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="card p-6 hover:border-purple-500/50 transition-all"
    >
      {/* Header: Option Details */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-700">
        <div className="flex items-center gap-3">
          {/* Direction Badge */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${directionStyle} font-semibold`}>
            {directionIcon}
            {trade.option_type || trade.direction}
          </div>
          
          {/* Option Details */}
          <div>
            <div className="font-bold text-lg">
              {trade.symbol || 'NIFTY'} {formatExpiry(trade.expiry)} {trade.strike}
            </div>
            <div className="text-sm text-gray-400">
              {formatTimestamp(trade.timestamp)}
            </div>
          </div>
        </div>
        
        {/* Status Badge */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${getStatusStyle(trade.status)} font-semibold text-sm`}>
          {getStatusIcon(trade.status)}
          {trade.status}
        </div>
      </div>

      {/* Trade Details Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {/* Entry Price */}
        <div>
          <p className="text-xs text-gray-400 mb-1">Entry</p>
          <p className="text-lg font-semibold">₹{trade.entry_price?.toFixed(2) || 'N/A'}</p>
        </div>
        
        {/* Target */}
        <div>
          <p className="text-xs text-gray-400 mb-1">Target</p>
          <p className="text-lg font-semibold text-green-400">
            ₹{trade.target_price?.toFixed(2) || 'N/A'}
          </p>
        </div>
        
        {/* Stop Loss */}
        <div>
          <p className="text-xs text-gray-400 mb-1">Stop Loss</p>
          <p className="text-lg font-semibold text-red-400">
            ₹{trade.stop_loss?.toFixed(2) || 'N/A'}
          </p>
        </div>
        
        {/* R:R */}
        <div>
          <p className="text-xs text-gray-400 mb-1">Risk:Reward</p>
          <p className="text-lg font-semibold text-purple-400">
            {trade.risk_reward_ratio?.toFixed(1) || 'N/A'}:1
          </p>
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {/* Probability */}
        <div>
          <p className="text-xs text-gray-400 mb-1">Probability</p>
          <p className="font-semibold">
            {trade.probability || 0}%
          </p>
        </div>
        
        {/* Confluence */}
        <div>
          <p className="text-xs text-gray-400 mb-1">Confluence</p>
          <p className="font-semibold">
            {trade.confluence || trade.confluence_count || 0} factors
          </p>
          {trade.confluence_score && (
            <p className="text-xs text-gray-400">
              Score: {trade.confluence_score}
            </p>
          )}
        </div>
        
        {/* Quantity */}
        <div>
          <p className="text-xs text-gray-400 mb-1">Quantity</p>
          <p className="font-semibold">{trade.quantity || 0} lots</p>
        </div>
        
        {/* P&L */}
        <div>
          <p className="text-xs text-gray-400 mb-1">P&L</p>
          <p className={`text-lg font-bold ${pnlColor}`}>
            {trade.pnl > 0 ? '+' : ''}₹{trade.pnl?.toFixed(2) || '0.00'}
          </p>
        </div>
      </div>

      {/* Greeks (if available) */}
      {(trade.delta || trade.theta || trade.gamma || trade.vega) && (
        <div className="pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-400 mb-2 font-semibold">Option Greeks</p>
          <div className="grid grid-cols-4 gap-3 text-sm">
            {trade.delta && (
              <div>
                <span className="text-gray-400">Delta (Δ)</span>
                <p className="font-semibold">{trade.delta?.toFixed(3)}</p>
              </div>
            )}
            {trade.theta && (
              <div>
                <span className="text-gray-400">Theta (Θ)</span>
                <p className="font-semibold">{trade.theta?.toFixed(2)}</p>
              </div>
            )}
            {trade.gamma && (
              <div>
                <span className="text-gray-400">Gamma (Γ)</span>
                <p className="font-semibold">{trade.gamma?.toFixed(4)}</p>
              </div>
            )}
            {trade.vega && (
              <div>
                <span className="text-gray-400">Vega (V)</span>
                <p className="font-semibold">{trade.vega?.toFixed(2)}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* LLM Reasoning (collapsible) */}
      {trade.llm_reasoning && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <details className="group">
            <summary className="cursor-pointer text-sm text-gray-400 font-semibold mb-2 hover:text-purple-400 transition-colors">
              📝 LLM Analysis
            </summary>
            <div className="mt-2 p-3 bg-white/5 rounded-lg text-sm text-gray-300 whitespace-pre-wrap">
              {trade.llm_reasoning}
            </div>
          </details>
        </div>
      )}

      {/* Entry Confirmation */}
      {trade.entry_confirmation && (
        <div className="mt-2">
          <p className="text-xs text-gray-400">
            Entry Signal: <span className="text-purple-400 font-semibold">{trade.entry_confirmation}</span>
          </p>
        </div>
      )}
    </motion.div>
  )
}

