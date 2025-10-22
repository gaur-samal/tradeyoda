import { motion } from 'framer-motion'

export default function MetricCard({ icon: Icon, label, value, delta, trend }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="metric-card"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
            {Icon && <Icon className="w-4 h-4" />}
            <span>{label}</span>
          </div>
          <div className="text-3xl font-bold">{value}</div>
          {delta && (
            <div className={`text-sm mt-2 ${
              trend === 'up' ? 'text-green-400' : 
              trend === 'down' ? 'text-red-400' : 
              'text-gray-400'
            }`}>
              {delta}
            </div>
          )}
        </div>
        {Icon && (
          <div className="bg-purple-500/20 p-3 rounded-xl">
            <Icon className="w-6 h-6 text-purple-400" />
          </div>
        )}
      </div>
    </motion.div>
  )
}

