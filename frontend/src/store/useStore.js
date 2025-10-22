import { create } from 'zustand'

const useStore = create((set, get) => ({
  // System state
  isRunning: false,
  setIsRunning: (value) => set({ isRunning: value }),
  
  // NEW: Continuous monitoring state
  continuousMode: false,
  setContinuousMode: (value) => set({ continuousMode: value }),

  // Live data
  livePrice: null,
  setLivePrice: (data) => set({ livePrice: data }),
  
  // Analysis data
  analysis: null,
  setAnalysis: (data) => set({ analysis: data }),
  
  // Trades
  trades: [],
  setTrades: (trades) => set({ trades }),
  addTrade: (trade) => set((state) => ({ trades: [...state.trades, trade] })),
  
  // Statistics
  statistics: {
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    win_rate: 0,
    total_pnl: 0,
    avg_win: 0,
    avg_loss: 0,
  },
  setStatistics: (stats) => set({ statistics: stats }),
  
  // WebSocket
  ws: null,
  setWs: (ws) => set({ ws }),
  
  // Config
  config: {},
  setConfig: (config) => set({ config }),
}))

export default useStore

