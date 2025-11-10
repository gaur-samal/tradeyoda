import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Activity, Clock } from 'lucide-react'
import { getLivePrice, getActiveInstrument } from '../utils/api'

export default function LivePriceCard() {
  const [livePrice, setLivePrice] = useState(null)
  const [instrument, setInstrument] = useState(null)
  const [priceChange, setPriceChange] = useState(0)
  const [priceChangePercent, setPriceChangePercent] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [marketStatus, setMarketStatus] = useState('UNKNOWN')
  const [isCached, setIsCached] = useState(false)

  useEffect(() => {
    // Fetch active instrument
    fetchInstrument()
    
    // Fetch initial price
    fetchLivePrice()
    
    // Set up polling every 5 seconds
    const interval = setInterval(fetchLivePrice, 10000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchInstrument = async () => {
    try {
      const { data } = await getActiveInstrument()
      setInstrument(data)
    } catch (error) {
      console.error('Failed to fetch instrument:', error)
    }
  }

  const fetchLivePrice = async () => {
    try {
      const { data } = await getLivePrice()
      
      if (data.success) {
        const newPrice = data.price
        const prevPrice = livePrice
        
        if (prevPrice && newPrice) {
          const change = newPrice - prevPrice
          const changePercent = ((change / prevPrice) * 100).toFixed(2)
          setPriceChange(change)
          setPriceChangePercent(changePercent)
        }
        
        setLivePrice(newPrice)
        setMarketStatus(data.market_status || 'UNKNOWN')
        setIsCached(data.cached || false)
        setError(null)
      } else {
        setError(data.message || 'No live data available')
        setMarketStatus(data.market_status || 'CLOSED')
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch live price:', error)
      setError('Failed to fetch live price')
      setMarketStatus('ERROR')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-gray-400">Loading live price...</span>
        </div>
      </div>
    )
  }

  if (error && !livePrice) {
    return (
      <div className="card p-6 bg-orange-500/5 border-orange-500/20">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-orange-400" />
          <div>
            <p className="font-semibold text-orange-400">Live Price Unavailable</p>
            <p className="text-sm text-gray-400">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  const isPositive = priceChange >= 0
  const TrendIcon = isPositive ? TrendingUp : TrendingDown
  
  // Market status styling
  const isMarketOpen = marketStatus === 'OPEN'
  const statusColor = isMarketOpen ? 'green' : 'red'
  const statusText = isMarketOpen ? 'Live' : 'Closed'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Activity className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Live Price</p>
                <p className="text-lg font-semibold">
                  {instrument?.name || 'Loading...'}
                </p>
              </div>
            </div>
            
            {/* Market Status Badge */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
              isMarketOpen 
                ? 'bg-green-500/10 border-green-500/30' 
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              <div className={`w-2 h-2 bg-${statusColor}-400 rounded-full ${
                isMarketOpen ? 'animate-pulse' : ''
              }`}></div>
              <span className={`text-sm font-medium text-${statusColor}-400`}>
                {statusText}
              </span>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="flex items-baseline gap-3">
              <span className="text-4xl font-bold">
                ₹{livePrice?.toFixed(2) || '---'}
              </span>
              
              {priceChange !== 0 && (
                <div className={`flex items-center gap-1 ${
                  isPositive ? 'text-green-400' : 'text-red-400'
                }`}>
                  <TrendIcon className="w-5 h-5" />
                  <span className="text-lg font-semibold">
                    {isPositive ? '+' : ''}{priceChange.toFixed(2)}
                  </span>
                  <span className="text-sm">
                    ({isPositive ? '+' : ''}{priceChangePercent}%)
                  </span>
                </div>
              )}
            </div>
            
            <div className="mt-3 flex items-center gap-4 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 bg-${statusColor}-400 rounded-full ${
                  isMarketOpen ? 'animate-pulse' : ''
                }`}></div>
                <span>{statusText}</span>
              </div>
              
              {isCached && (
                <>
                  <span>•</span>
                  <div className="flex items-center gap-1 text-orange-400">
                    <Clock className="w-3 h-3" />
                    <span>Cached</span>
                  </div>
                </>
              )}
              
              <span>•</span>
              <span>Updates every 5s</span>
              <span>•</span>
              <span>Lot Size: {instrument?.lot_size || 'N/A'}</span>
            </div>
            
            {/* Market Hours Info (when closed) */}
            {!isMarketOpen && (
              <div className="mt-3 p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
                <p className="text-sm text-red-400">
                  📅 Market Hours: Monday-Friday, 9:15 AM - 3:30 PM IST
                </p>
              </div>
            )}
          </div>
        </div>
        
        {/* Price Trend Indicator */}
        <div className="hidden lg:block ml-6">
          <div className="w-32 h-20 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-lg flex items-center justify-center">
            <TrendIcon className={`w-12 h-12 ${
              isPositive ? 'text-green-400' : 'text-red-400'
            }`} />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

