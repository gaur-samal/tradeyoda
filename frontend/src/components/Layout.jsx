import { Outlet, NavLink } from 'react-router-dom'
import { Activity, BarChart3, TrendingUp, Settings, HelpCircle } from 'lucide-react'
import { motion } from 'framer-motion'
import { useState } from 'react'

export default function Layout() {
  const [showHelp, setShowHelp] = useState(false)
  
  const navItems = [
    { path: '/', icon: Activity, label: 'Dashboard' },
    { path: '/analysis', icon: BarChart3, label: 'Analysis' },
    { path: '/trades', icon: TrendingUp, label: 'Trades' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ]
  
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="glass-panel border-b border-white/10 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="text-4xl">🧙‍♂️</div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
                  Trade Yoda
                </h1>
                <p className="text-xs text-purple-300">The Infamous GenAI Trader</p>
              </div>
            </div>
            
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="btn-secondary py-2 px-4"
            >
              <HelpCircle className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>
      
      {/* Help Panel */}
      {showHelp && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel mx-6 mt-4 p-6"
        >
          <h3 className="text-lg font-bold mb-3">📖 Quick Help</h3>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-purple-300 mb-2">Getting Started</h4>
              <ul className="space-y-1 text-gray-300">
                <li>• Start the system from Dashboard</li>
                <li>• Run zone analysis (15-min cycle)</li>
                <li>• Identify trades (3-min cycle)</li>
                <li>• Monitor active trades</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-purple-300 mb-2">Technical Indicators</h4>
              <ul className="space-y-1 text-gray-300">
                <li>• RSI (Relative Strength Index)</li>
                <li>• Bollinger Bands</li>
                <li>• Candlestick Patterns</li>
                <li>• Chart Patterns</li>
                <li>• Volume Profile & Order Blocks</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-purple-300 mb-2">Safety</h4>
              <ul className="space-y-1 text-gray-300">
                <li>• Always use Sandbox mode first</li>
                <li>• Set appropriate risk limits</li>
                <li>• Monitor trades actively</li>
                <li>• Review LLM analysis carefully</li>
              </ul>
            </div>
          </div>
        </motion.div>
      )}
      
      {/* Navigation */}
      <nav className="glass-panel border-b border-white/10 sticky top-[73px] z-40">
        <div className="container mx-auto px-6">
          <div className="flex gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-6 py-3 transition-all ${
                    isActive
                      ? 'text-purple-400 border-b-2 border-purple-400'
                      : 'text-gray-400 hover:text-white'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
      
      {/* Disclaimer */}
      <div className="bg-yellow-500/10 border-l-4 border-yellow-500 px-6 py-3 mx-6 mt-4 rounded-lg">
        <p className="text-sm text-yellow-200">
          <strong>⚠️ DISCLAIMER:</strong> Trading involves substantial risk. All trading decisions are at user's discretion. 
          NeuralVectors Technologies LLP and Trade Yoda are not liable for any losses. For educational purposes only.
        </p>
      </div>
      
      {/* Main Content */}
      <main className="flex-1 container mx-auto px-6 py-6">
        <Outlet />
      </main>
      
      {/* Footer */}
      <footer className="glass-panel border-t border-white/10 py-4">
        <div className="container mx-auto px-6 text-center text-sm text-gray-400">
          🧙‍♂️ Trade Yoda - Powered by NeuralVectors Technologies LLP
        </div>
      </footer>
    </div>
  )
}

