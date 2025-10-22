import { motion } from 'framer-motion'

export default function ZoneCard({ zone, index, type }) {
  const isSupply = type === 'supply'
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="card p-4 card-hover"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            isSupply ? 'bg-red-500' : 'bg-green-500'
          }`} />
          <span className="font-semibold">Zone #{index + 1}</span>
        </div>
        <div className="text-sm font-medium text-purple-400">
          {zone.confidence?.toFixed(0)}% Confidence
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Top:</span>
          <span className="font-semibold">₹{zone.zone_top?.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Bottom:</span>
          <span className="font-semibold">₹{zone.zone_bottom?.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Distance:</span>
          <span className="font-semibold">{zone.distance_from_price?.toFixed(2)}%</span>
        </div>
      </div>
      
      <div className="mt-3">
        <div className="flex flex-wrap gap-1">
          {zone.factors?.map((factor, i) => (
            <span
              key={i}
              className="px-2 py-1 bg-purple-500/20 rounded text-xs text-purple-300"
            >
              {factor}
            </span>
          ))}
        </div>
      </div>
      
      <div className="mt-3">
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            className={`h-full ${isSupply ? 'bg-red-500' : 'bg-green-500'}`}
            initial={{ width: 0 }}
            animate={{ width: `${zone.confidence}%` }}
            transition={{ duration: 1, delay: index * 0.1 }}
          />
        </div>
      </div>
    </motion.div>
  )
}

