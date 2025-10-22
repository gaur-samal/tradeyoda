import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Clock, Target, AlertTriangle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function TradeCard({ trade, index }) {
  const isCall = trade.direction === 'CALL'
  const isActive = trade.status === 'ACTIVE'
  const isProfitable = trade.pnl > 0
  
  const statusConfig = {
    ACTIVE: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: Clock },
    CLOSED: { color: isProfitable ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30', icon: Target },
    PAPER: { color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: AlertTriangle },
    PENDING: { color: 'bg-gray-500/20 text-gray-400 border-gray-500/30', icon: Clock },
  }
  
  const status = statusConfig[trade.status] || statusConfig.PENDING
  const StatusIcon = status.icon
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="card p-5 card-hover"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isCall ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
            {isCall ? (
              <TrendingUp className="w-5 h-5 text-green-400" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-400" />
            )}
          </div>
          <div>
            <div className="font-bold text-lg">{trade.direction}</div>
            <div className="text-xs text-gray-400">
              {formatDistanceToNow(new Date(trade.timestamp), { addSuffix: true })}
            </div>
          </div>
        </div>
        
        <div className={`status-badge ${status.color} flex items-center gap-2`}>
          <StatusIcon className="w-4 h-4" />
          {trade.status}
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-400 mb-1">Entry Price</div>
          <div className="font-semibold">₹{trade.entry_price?.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">Target</div>
          <div className="font-semibold text-green-400">₹{trade.target_price?.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">Stop Loss</div>
          <div className="font-semibold text-red-400">₹{trade.stop_loss?.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-1">Risk:Reward</div>
          <div className="font-semibold">{trade.risk_reward?.toFixed(2)}</div>
        </div>
      </div>
      
      <div className="flex items-center justify-between pt-4 border-t border-white/10">
        <div>
          <div className="text-xs text-gray-400">Probability</div>
          <div className="font-bold text-purple-400">{trade.probability?.toFixed(0)}%</div>
        </div>
        <div>
          <div className="text-xs text-gray-400">P&L</div>
          <div className={`font-bold ${isProfitable ? 'text-green-400' : 'text-red-400'}`}>
            ₹{trade.pnl?.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-400">Confluence</div>
          <div className="font-bold">{trade.confluence_count || 0}</div>
        </div>
      </div>
    </motion.div>
  )
}

