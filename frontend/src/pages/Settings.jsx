import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Save, RefreshCw, AlertTriangle, Edit } from 'lucide-react'
import useStore from '../store/useStore'
import { getConfig, updateConfig } from '../utils/api'

export default function Settings() {
  const { config, setConfig } = useStore()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editedConfig, setEditedConfig] = useState({})
  
  useEffect(() => {
    fetchConfig()
  }, [])
  
  const fetchConfig = async () => {
    setLoading(true)
    try {
      const { data } = await getConfig()
      setConfig(data)
      setEditedConfig(data)
    } catch (error) {
      console.error('Failed to fetch config:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSave = async () => {
    setSaving(true)
    try {
      await updateConfig(editedConfig)
      setConfig(editedConfig)
      setEditMode(false)
      alert('✅ Configuration updated successfully!')
    } catch (error) {
      console.error('Failed to save config:', error)
      alert('❌ Failed to save configuration')
    } finally {
      setSaving(false)
    }
  }
  
  const handleChange = (field, value) => {
    setEditedConfig(prev => ({ ...prev, [field]: value }))
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    )
  }
  
  const displayConfig = editMode ? editedConfig : config
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">⚙️ System Settings</h1>
        <div className="flex gap-3">
          <button onClick={fetchConfig} className="btn-secondary flex items-center gap-2">
            <RefreshCw className="w-5 h-5" />
            Refresh
          </button>
          
          {!editMode ? (
            <button 
              onClick={() => setEditMode(true)} 
              className="btn-primary flex items-center gap-2"
            >
              <Edit className="w-5 h-5" />
              Edit Settings
            </button>
          ) : (
            <>
              <button 
                onClick={() => {
                  setEditMode(false)
                  setEditedConfig(config)
                }} 
                className="btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={handleSave}
                disabled={saving}
                className="btn-primary flex items-center gap-2"
              >
                <Save className="w-5 h-5" />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          )}
        </div>
      </div>
      
      {editMode && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
          <p className="text-sm text-blue-200">
            📝 <strong>Edit Mode Active:</strong> Make your changes below and click "Save Changes" to apply them immediately.
          </p>
        </div>
      )}
      
      {/* Trading Parameters */}
      <div className="card p-6">
        <h3 className="text-xl font-bold mb-6">📊 Trading Parameters</h3>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Risk:Reward Ratio</label>
            {editMode ? (
              <input
                type="number"
                step="0.5"
                value={displayConfig.risk_reward_ratio}
                onChange={(e) => handleChange('risk_reward_ratio', parseFloat(e.target.value))}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-xl font-bold focus:border-purple-500 focus:outline-none"
              />
            ) : (
              <div className="text-2xl font-bold">{displayConfig.risk_reward_ratio}</div>
            )}
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Max Risk %</label>
            {editMode ? (
              <input
                type="number"
                step="0.5"
                value={displayConfig.max_risk_percentage}
                onChange={(e) => handleChange('max_risk_percentage', parseFloat(e.target.value))}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-xl font-bold focus:border-purple-500 focus:outline-none"
              />
            ) : (
              <div className="text-2xl font-bold">{displayConfig.max_risk_percentage}%</div>
            )}
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Min Probability Threshold</label>
            {editMode ? (
              <input
                type="number"
                step="5"
                value={displayConfig.min_probability_threshold}
                onChange={(e) => handleChange('min_probability_threshold', parseFloat(e.target.value))}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-xl font-bold focus:border-purple-500 focus:outline-none"
              />
            ) : (
              <div className="text-2xl font-bold">{displayConfig.min_probability_threshold}%</div>
            )}
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Zone Timeframe</label>
            <div className="text-2xl font-bold">{displayConfig.zone_timeframe} min</div>
          </div>
        </div>
      </div>
      
      {/* Experimental Features - EDITABLE */}
      <div className="card p-6 border-2 border-yellow-500/30">
        <div className="flex items-center gap-3 mb-6">
          <AlertTriangle className="w-6 h-6 text-yellow-400" />
          <h3 className="text-xl font-bold">🧪 Experimental Features</h3>
        </div>
        
        <div className="space-y-4">
          {/* Backtest Mode */}
          <div className="p-4 bg-white/5 rounded-lg">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="font-semibold mb-1 flex items-center gap-2">
                  <span>Enable Backtest Mode</span>
                </div>
                <p className="text-sm text-gray-400">
                  Load historical data instead of live market data for strategy testing.
                </p>
              </div>
              {editMode ? (
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={displayConfig.use_backtest_mode}
                    onChange={(e) => handleChange('use_backtest_mode', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              ) : (
                <span className={`status-badge ${
                  displayConfig.use_backtest_mode 
                    ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' 
                    : 'bg-gray-500/20 text-gray-400 border-gray-500/30'
                }`}>
                  {displayConfig.use_backtest_mode ? 'Enabled' : 'Disabled'}
                </span>
              )}
            </div>
            
            {displayConfig.use_backtest_mode && editMode && (
              <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-white/10">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">From Date</label>
                  <input
                    type="date"
                    value={displayConfig.backtest_from || '2025-10-01'}
                    onChange={(e) => handleChange('backtest_from', e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 focus:border-purple-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">To Date</label>
                  <input
                    type="date"
                    value={displayConfig.backtest_to || '2025-10-17'}
                    onChange={(e) => handleChange('backtest_to', e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 focus:border-purple-500 focus:outline-none"
                  />
                </div>
              </div>
            )}
          </div>
          
          {/* No Trades on Expiry */}
          <div className="p-4 bg-white/5 rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-semibold mb-1">No Trades on Expiry (Tuesday)</div>
                <p className="text-sm text-gray-400">
                  Skip new positions on weekly expiry day to avoid high volatility.
                </p>
              </div>
              {editMode ? (
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={displayConfig.no_trades_on_expiry}
                    onChange={(e) => handleChange('no_trades_on_expiry', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                </label>
              ) : (
                <span className={`status-badge ${
                  displayConfig.no_trades_on_expiry 
                    ? 'bg-green-500/20 text-green-400 border-green-500/30' 
                    : 'bg-red-500/20 text-red-400 border-red-500/30'
                }`}>
                  {displayConfig.no_trades_on_expiry ? 'Enabled' : 'Disabled'}
                </span>
              )}
            </div>
          </div>
          
          {/* Order Settings */}
          <div className="p-4 bg-white/5 rounded-lg">
            <div className="font-semibold mb-3">Order Execution Settings</div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Order Quantity</label>
                {editMode ? (
                  <input
                    type="number"
                    value={displayConfig.order_quantity}
                    onChange={(e) => handleChange('order_quantity', parseInt(e.target.value))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-xl font-bold focus:border-purple-500 focus:outline-none"
                  />
                ) : (
                  <div className="text-xl font-bold">{displayConfig.order_quantity || 50}</div>
                )}
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Order Type</label>
                {editMode ? (
                  <select
                    value={displayConfig.use_super_order ? 'super' : 'bracket'}
                    onChange={(e) => handleChange('use_super_order', e.target.value === 'super')}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 focus:border-purple-500 focus:outline-none"
                  >
                    <option value="super">Super Order</option>
                    <option value="bracket">Bracket Order</option>
                  </select>
                ) : (
                  <span className={`status-badge ${
                    displayConfig.use_super_order 
                      ? 'bg-purple-500/20 text-purple-400 border-purple-500/30' 
                      : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                  }`}>
                    {displayConfig.use_super_order ? 'Super Order' : 'Bracket Order'}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <p className="text-sm text-yellow-200">
            ⚠️ <strong>Note:</strong> These features are experimental. Changes are applied immediately during this session.
          </p>
        </div>
      </div>
      
      {/* Technical Indicators */}
      <div className="card p-6">
        <h3 className="text-xl font-bold mb-6">📈 Technical Indicators</h3>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-purple-300 mb-4">RSI Settings</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Period</span>
                {editMode ? (
                  <input
                    type="number"
                    value={displayConfig.rsi_period}
                    onChange={(e) => handleChange('rsi_period', parseInt(e.target.value))}
                    className="w-20 bg-white/10 border border-white/20 rounded px-2 py-1 text-center focus:border-purple-500 focus:outline-none"
                  />
                ) : (
                  <span className="font-semibold">{displayConfig.rsi_period}</span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Overbought Level</span>
                {editMode ? (
                  <input
                    type="number"
                    value={displayConfig.rsi_overbought}
                    onChange={(e) => handleChange('rsi_overbought', parseFloat(e.target.value))}
                    className="w-20 bg-white/10 border border-white/20 rounded px-2 py-1 text-center focus:border-purple-500 focus:outline-none"
                  />
                ) : (
                  <span className="font-semibold">{displayConfig.rsi_overbought}</span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Oversold Level</span>
                {editMode ? (
                  <input
                    type="number"
                    value={displayConfig.rsi_oversold}
                    onChange={(e) => handleChange('rsi_oversold', parseFloat(e.target.value))}
                    className="w-20 bg-white/10 border border-white/20 rounded px-2 py-1 text-center focus:border-purple-500 focus:outline-none"
                  />
                ) : (
                  <span className="font-semibold">{displayConfig.rsi_oversold}</span>
                )}
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold text-purple-300 mb-4">Bollinger Bands</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Period</span>
                {editMode ? (
                  <input
                    type="number"
                    value={displayConfig.bb_period}
                    onChange={(e) => handleChange('bb_period', parseInt(e.target.value))}
                    className="w-20 bg-white/10 border border-white/20 rounded px-2 py-1 text-center focus:border-purple-500 focus:outline-none"
                  />
                ) : (
                  <span className="font-semibold">{displayConfig.bb_period}</span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Std Deviation</span>
                {editMode ? (
                  <input
                    type="number"
                    step="0.1"
                    value={displayConfig.bb_std_dev}
                    onChange={(e) => handleChange('bb_std_dev', parseFloat(e.target.value))}
                    className="w-20 bg-white/10 border border-white/20 rounded px-2 py-1 text-center focus:border-purple-500 focus:outline-none"
                  />
                ) : (
                  <span className="font-semibold">{displayConfig.bb_std_dev || 2.0}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Pattern Detection */}
      <div className="card p-6">
        <h3 className="text-xl font-bold mb-6">🕯️ Pattern Detection</h3>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <span>Candlestick Patterns</span>
            {editMode ? (
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={displayConfig.enable_candlestick_patterns}
                  onChange={(e) => handleChange('enable_candlestick_patterns', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
              </label>
            ) : (
              <span className={`px-3 py-1 rounded-full text-sm ${
                displayConfig.enable_candlestick_patterns 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {displayConfig.enable_candlestick_patterns ? 'Enabled' : 'Disabled'}
              </span>
            )}
          </div>
          
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <span>Chart Patterns</span>
            {editMode ? (
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={displayConfig.enable_chart_patterns}
                  onChange={(e) => handleChange('enable_chart_patterns', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
              </label>
            ) : (
              <span className={`px-3 py-1 rounded-full text-sm ${
                displayConfig.enable_chart_patterns 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {displayConfig.enable_chart_patterns ? 'Enabled' : 'Disabled'}
              </span>
            )}
          </div>
        </div>
      </div>
      
      {/* Environment */}
      <div className="card p-6">
        <h3 className="text-xl font-bold mb-6">🧪 Environment</h3>
        
        <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
          <div>
            <div className="font-semibold mb-1">Trading Mode</div>
            <div className="text-sm text-gray-400">
              {displayConfig.use_sandbox ? 'Paper trading - No real money' : 'Live trading - Real money'}
            </div>
          </div>
          {editMode ? (
            <select
              value={displayConfig.use_sandbox ? 'sandbox' : 'live'}
              onChange={(e) => handleChange('use_sandbox', e.target.value === 'sandbox')}
              className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 focus:border-purple-500 focus:outline-none"
            >
              <option value="sandbox">🧪 Sandbox (Paper Trading)</option>
              <option value="live">🔴 Live (Real Money)</option>
            </select>
          ) : (
            <span className={`status-badge ${
              displayConfig.use_sandbox ? 'bg-blue-500/20 text-blue-400' : 'bg-red-500/20 text-red-400'
            }`}>
              {displayConfig.use_sandbox ? '🧪 Sandbox' : '🔴 Live'}
            </span>
          )}
        </div>
      </div>
      
      {/* Info Box */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-6"
      >
        <h4 className="font-semibold mb-2">ℹ️ Configuration Note</h4>
        <p className="text-sm text-gray-300">
          Changes made here are applied <strong>immediately</strong> and persist during this session only. 
          To make permanent changes, update your <code className="bg-white/10 px-2 py-1 rounded">.env</code> file.
        </p>
      </motion.div>
    </div>
  )
}

