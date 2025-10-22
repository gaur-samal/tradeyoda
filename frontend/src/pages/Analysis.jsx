import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, Activity, AlertCircle } from 'lucide-react'
import useStore from '../store/useStore'
import { getAnalysis } from '../utils/api'

export default function Analysis() {
  const { analysis, setAnalysis } = useStore()
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    if (!analysis) {
      fetchAnalysis()
    }
  }, [])
  
  const fetchAnalysis = async () => {
    setLoading(true)
    try {
      const { data } = await getAnalysis()
      setAnalysis(data)
    } catch (error) {
      console.error('Failed to fetch analysis:', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    )
  }
  
  if (!analysis) {
    return (
      <div className="card p-12 text-center">
        <div className="text-6xl mb-4">📊</div>
        <h2 className="text-2xl font-bold mb-2">No Analysis Available</h2>
        <p className="text-gray-400 mb-6">Run zone analysis from the dashboard to see results</p>
        <button onClick={fetchAnalysis} className="btn-primary">
          Refresh Analysis
        </button>
      </div>
    )
  }
  
  const techIndicators = analysis.technical_indicators || {}
  const llmAnalysis = analysis.llm_analysis || {}
  const marketContext = analysis.market_context || {}
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">📈 Market Analysis</h1>
        <button onClick={fetchAnalysis} className="btn-secondary">
          Refresh
        </button>
      </div>
      
      {/* Technical Indicators Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-6 h-6 text-blue-400" />
            <h3 className="font-semibold">RSI</h3>
          </div>
          <div className="text-3xl font-bold mb-2">
            {techIndicators.latest_rsi?.toFixed(2) || 'N/A'}
          </div>
          <div className={`text-sm font-medium ${
            techIndicators.rsi_signal === 'OVERBOUGHT' ? 'text-red-400' :
            techIndicators.rsi_signal === 'OVERSOLD' ? 'text-green-400' :
            'text-gray-400'
          }`}>
            {techIndicators.rsi_signal || 'NEUTRAL'}
          </div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 className="w-6 h-6 text-purple-400" />
            <h3 className="font-semibold">Bollinger Bands</h3>
          </div>
          <div className="text-lg font-bold mb-2">
            {techIndicators.bb_position || 'N/A'}
          </div>
          <div className="text-sm text-gray-400">Position</div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-6 h-6 text-green-400" />
            <h3 className="font-semibold">Candle Patterns</h3>
          </div>
          <div className="text-3xl font-bold mb-2">
            {techIndicators.candlestick_patterns?.length || 0}
          </div>
          <div className="text-sm text-gray-400">Detected</div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="w-6 h-6 text-orange-400" />
            <h3 className="font-semibold">Chart Patterns</h3>
          </div>
          <div className="text-3xl font-bold mb-2">
            {techIndicators.chart_patterns?.length || 0}
          </div>
          <div className="text-sm text-gray-400">Detected</div>
        </motion.div>
      </div>
      
      {/* Market Context & LLM Analysis */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Market Context */}
        <div className="card p-6">
          <h3 className="text-xl font-bold mb-4">📊 Market Context</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Current Price</span>
              <span className="text-xl font-bold">₹{marketContext.current_price?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Trend</span>
              <span className={`font-semibold px-3 py-1 rounded-full ${
                marketContext.trend === 'Bullish' ? 'bg-green-500/20 text-green-400' :
                marketContext.trend === 'Bearish' ? 'bg-red-500/20 text-red-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>
                {marketContext.trend}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Volatility</span>
              <span className="font-semibold">{marketContext.volatility?.toFixed(4)}</span>
            </div>
            {marketContext.rsi && (
              <div className="flex justify-between items-center">
                <span className="text-gray-400">RSI Signal</span>
                <span className="font-semibold text-purple-400">{marketContext.rsi_signal}</span>
              </div>
            )}
          </div>
        </div>
        
        {/* LLM Analysis */}
        <div className="card p-6">
          <h3 className="text-xl font-bold mb-4">🤖 AI Analysis</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Market Bias</span>
              <span className={`font-bold text-lg ${
                llmAnalysis.market_bias === 'Bullish' ? 'text-green-400' :
                llmAnalysis.market_bias === 'Bearish' ? 'text-red-400' :
                'text-yellow-400'
              }`}>
                {llmAnalysis.market_bias === 'Bullish' ? '🟢' :
                 llmAnalysis.market_bias === 'Bearish' ? '🔴' : '🟡'} {llmAnalysis.market_bias}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">RSI Impact</span>
              <span className="font-semibold">{llmAnalysis.rsi_impact || 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">BB Impact</span>
              <span className="font-semibold">{llmAnalysis.bb_impact || 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Pattern Confluence</span>
              <span className="font-semibold text-purple-400">{llmAnalysis.pattern_confluence || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Full Analysis Summary */}
      {llmAnalysis.analysis_summary && (
        <div className="card p-6">
          <h3 className="text-xl font-bold mb-4">📝 Full Analysis Summary</h3>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 leading-relaxed">{llmAnalysis.analysis_summary}</p>
          </div>
        </div>
      )}
      
      {/* Entry Signals */}
      {llmAnalysis.entry_signals?.length > 0 && (
        <div className="card p-6">
          <h3 className="text-xl font-bold mb-4">📍 Entry Signals</h3>
          <div className="space-y-2">
            {llmAnalysis.entry_signals.map((signal, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                <div className="text-green-400 mt-1">✅</div>
                <div className="text-gray-300">{signal}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Risk Factors */}
      {llmAnalysis.risk_factors?.length > 0 && (
        <div className="card p-6">
          <h3 className="text-xl font-bold mb-4">⚠️ Risk Factors</h3>
          <div className="space-y-2">
            {llmAnalysis.risk_factors.map((risk, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                <div className="text-yellow-400 mt-1">•</div>
                <div className="text-gray-300">{risk}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Patterns Details */}
      {(techIndicators.candlestick_patterns?.length > 0 || techIndicators.chart_patterns?.length > 0) && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Candlestick Patterns */}
          {techIndicators.candlestick_patterns?.length > 0 && (
            <div className="card p-6">
              <h3 className="text-xl font-bold mb-4">🕯️ Candlestick Patterns</h3>
              <div className="space-y-3">
                {techIndicators.candlestick_patterns.slice(-5).map((pattern, idx) => (
                  <div key={idx} className="p-3 bg-white/5 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">{pattern.pattern}</span>
                                            <span className={`text-sm ${
                        pattern.signal === 'BULLISH' ? 'text-green-400' :
                        pattern.signal === 'BEARISH' ? 'text-red-400' :
                        'text-yellow-400'
                      }`}>
                        {pattern.signal === 'BULLISH' ? '🟢' :
                         pattern.signal === 'BEARISH' ? '🔴' : '🟡'} {pattern.signal}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">Confidence</span>
                      <span className="font-semibold">{pattern.confidence}%</span>
                    </div>
                    <div className="mt-2 h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-500"
                        style={{ width: `${pattern.confidence}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Chart Patterns */}
          {techIndicators.chart_patterns?.length > 0 && (
            <div className="card p-6">
              <h3 className="text-xl font-bold mb-4">📈 Chart Patterns</h3>
              <div className="space-y-3">
                {techIndicators.chart_patterns.slice(-5).map((pattern, idx) => (
                  <div key={idx} className="p-3 bg-white/5 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">{pattern.pattern}</span>
                      <span className={`text-sm ${
                        pattern.signal === 'BULLISH' ? 'text-green-400' :
                        pattern.signal === 'BEARISH' ? 'text-red-400' :
                        'text-yellow-400'
                      }`}>
                        {pattern.signal === 'BULLISH' ? '🟢' :
                         pattern.signal === 'BEARISH' ? '🔴' : '🟡'} {pattern.signal}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">Confidence</span>
                      <span className="font-semibold">{pattern.confidence}%</span>
                    </div>
                    {pattern.resistance && (
                      <div className="text-xs text-gray-400 mt-2">
                        Resistance: ₹{pattern.resistance.toFixed(2)}
                      </div>
                    )}
                    {pattern.support && (
                      <div className="text-xs text-gray-400 mt-2">
                        Support: ₹{pattern.support.toFixed(2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

