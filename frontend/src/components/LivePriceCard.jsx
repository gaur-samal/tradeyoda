import { TrendingUp, TrendingDown } from 'lucide-react'
import { motion } from 'framer-motion'
import useStore from '../store/useStore'

export default function LivePriceCard() {
  const { livePrice } = useStore()
  
  if (!livePrice) {
    return (
      <div className="card p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-white/10 rounded w-1/3 mb-4"></div>
          <div className="h-8 bg-white/10 rounded w-1/2"></div>
        </div>
      </div>
    )
  }
  
  const isPositive = (livePrice.ltp - livePrice.low) > 0
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-300">📈 Nifty Futures - Live</h3>
        <div className="status-badge status-active">
          <span className="inline-block w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
          Live
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-sm text-gray-400 mb-1">LTP</div>
          <div className={`text-2xl font-bold flex items-center gap-2 ${
            isPositive ? 'text-green-400' : 'text-red-400'
          }`}>
            ₹{livePrice.ltp?.toFixed(2)}
            {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
          </div>
        </div>
        
        <div>
          <div className="text-sm text-gray-400 mb-1">High</div>
          <div className="text-xl font-semibold text-green-400">
            ₹{livePrice.high?.toFixed(2)}
          </div>
        </div>
        
        <div>
          <div className="text-sm text-gray-400 mb-1">Low</div>
          <div className="text-xl font-semibold text-red-400">
            ₹{livePrice.low?.toFixed(2)}
          </div>
        </div>
        
        <div>
          <div className="text-sm text-gray-400 mb-1">Volume</div>
          <div className="text-xl font-semibold">
            {livePrice.volume?.toLocaleString()}
          </div>
        </div>
      </div>
      
      <div className="mt-4 h-2 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-500 to-violet-500"
          initial={{ width: 0 }}
          animate={{ width: '75%' }}
          transition={{ duration: 1 }}
        />
      </div>
    </motion.div>
  )
}

