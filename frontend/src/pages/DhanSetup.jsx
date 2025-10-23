import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Key, CheckCircle, AlertCircle, Info, ExternalLink, TestTube } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'
import { getDhanCredentials, updateDhanCredentials, testDhanConnection } from '../utils/api'

export default function DhanSetup() {
  const [credentials, setCredentials] = useState({
    client_id: '',
    access_token: ''
  })
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [showGuide, setShowGuide] = useState(false)

  useEffect(() => {
    fetchStatus()
  }, [])

  const fetchStatus = async () => {
    try {
      const { data } = await getDhanCredentials()
      setStatus(data)
    } catch (error) {
      console.error('Failed to fetch Dhan status:', error)
    }
  }

  const handleSave = async () => {
    if (!credentials.client_id || !credentials.access_token) {
      toast.error('Please enter both Client ID and Access Token')
      return
    }

    setLoading(true)
    const loadingToast = toast.loading('Saving Dhan credentials...')

    try {
      const { data } = await updateDhanCredentials(credentials)
      
      if (data.success) {
        toast.success('✅ Dhan credentials saved successfully!', { id: loadingToast })
        fetchStatus()
        setCredentials({ client_id: '', access_token: '' })
      }
    } catch (error) {
      toast.error('Failed to save credentials: ' + (error.response?.data?.detail || error.message), { id: loadingToast })
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    if (!status?.configured) {
      toast.error('Please save your credentials first')
      return
    }

    setTesting(true)
    const loadingToast = toast.loading('Testing Dhan connection...')

    try {
      const { data } = await testDhanConnection()
      
      if (data.success) {
        toast.success(data.message, { id: loadingToast, duration: 5000 })
      } else {
        toast.error(data.message, { id: loadingToast, duration: 5000 })
      }
    } catch (error) {
      toast.error('Test failed: ' + (error.response?.data?.detail || error.message), { id: loadingToast })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="space-y-6">
      <Toaster position="top-right" />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">🔑 Dhan API Setup</h1>
          <p className="text-gray-400">Configure your Dhan trading credentials</p>
        </div>
        
        {status?.configured && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-semibold">Connected</span>
          </div>
        )}
      </div>

      {/* Setup Guide Button */}
      <button
        onClick={() => setShowGuide(!showGuide)}
        className="w-full flex items-center justify-between p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl hover:bg-blue-500/20 transition-all"
      >
        <div className="flex items-center gap-3">
          <Info className="w-6 h-6 text-blue-400" />
          <div className="text-left">
            <div className="font-semibold text-blue-400">How to get Dhan API credentials?</div>
            <div className="text-sm text-gray-400">Click to view step-by-step guide</div>
          </div>
        </div>
        <div className="text-blue-400">{showGuide ? '▼' : '▶'}</div>
      </button>

      {/* Guide Content */}
      {showGuide && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="card p-6 space-y-4"
        >
          <h3 className="text-xl font-bold mb-4">📚 Step-by-Step Guide</h3>
          
          <div className="space-y-6">
            {/* Step 1 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h4 className="font-semibold mb-2">Login to Dhan Web</h4>
                <p className="text-gray-400 text-sm mb-2">
                  Go to <a href="https://web.dhan.co" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline inline-flex items-center gap-1">
                    web.dhan.co <ExternalLink className="w-3 h-3" />
                  </a> and login to your account
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h4 className="font-semibold mb-2">Navigate to API Section</h4>
                <p className="text-gray-400 text-sm">
                  Click on your <strong>Profile</strong> → <strong>DhanHQ Trading APIs</strong>
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h4 className="font-semibold mb-2">Get Your Client ID</h4>
                <p className="text-gray-400 text-sm">
                  Your <strong>Client ID</strong> is displayed in your profile (usually starts with 1000...)
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center font-bold">
                4
              </div>
              <div>
                <h4 className="font-semibold mb-2">Generate Access Token</h4>
                <p className="text-gray-400 text-sm mb-2">
                  Click <strong>"Generate Access Token"</strong> button
                </p>
                <p className="text-yellow-400 text-xs">
                  ⚠️ Note: Access Token expires after 24 hours. You'll need to regenerate it daily.
                </p>
              </div>
            </div>

            {/* Step 5 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center font-bold">
                5
              </div>
              <div>
                <h4 className="font-semibold mb-2">Subscribe to Data API (Optional but Recommended)</h4>
                <p className="text-gray-400 text-sm mb-2">
                  For historical data and advanced features, subscribe to <strong>DhanHQ Data API</strong>
                </p>
                <p className="text-gray-400 text-sm">
                  Cost: <strong>₹499 + taxes/month</strong> (auto-renews every 30 days)
                </p>
                <a 
                  href="https://knowledge.dhan.co/support/solutions/articles/82000909111" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:underline text-sm inline-flex items-center gap-1 mt-2"
                >
                  Learn more about Data API subscription <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            {/* Step 6 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center font-bold">
                6
              </div>
              <div>
                <h4 className="font-semibold mb-2">Copy and Paste Here</h4>
                <p className="text-gray-400 text-sm">
                  Copy both <strong>Client ID</strong> and <strong>Access Token</strong> and paste them in the form below
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-200">
                <strong>Important:</strong> Keep your credentials secure. Never share them publicly. The Access Token needs to be regenerated daily as it expires after 24 hours.
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Credentials Form */}
      <div className="card p-6">
        <h3 className="text-xl font-bold mb-6">Enter Dhan Credentials</h3>

        {status?.configured && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <span className="font-semibold text-green-400">Current Status</span>
            </div>
            <div className="text-sm text-gray-300 space-y-1">
              <div>Client ID: <code className="bg-white/10 px-2 py-1 rounded">{status.client_id}</code></div>
              <div>Access Token: <code className="bg-white/10 px-2 py-1 rounded">{status.access_token}</code></div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Client ID <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={credentials.client_id}
              onChange={(e) => setCredentials({ ...credentials, client_id: e.target.value })}
              placeholder="Enter your Dhan Client ID (e.g., 1000000123)"
              className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 focus:border-purple-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Access Token <span className="text-red-400">*</span>
            </label>
            <textarea
              value={credentials.access_token}
              onChange={(e) => setCredentials({ ...credentials, access_token: e.target.value })}
              placeholder="Paste your Dhan Access Token here"
              rows={4}
              className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 focus:border-purple-500 focus:outline-none font-mono text-sm"
            />
            <p className="text-xs text-gray-400 mt-1">
              Access Token expires after 24 hours. Update it daily.
            </p>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSave}
              disabled={loading || !credentials.client_id || !credentials.access_token}
              className="flex-1 btn-primary flex items-center justify-center gap-2"
            >
              <Key className="w-5 h-5" />
              {loading ? 'Saving...' : 'Save Credentials'}
            </button>

            <button
              onClick={handleTest}
              disabled={testing || !status?.configured}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <TestTube className="w-5 h-5" />
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="card p-6 bg-purple-500/5 border-purple-500/20">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <Info className="w-5 h-5 text-purple-400" />
          <span>Need Help?</span>
        </h4>
        <div className="text-sm text-gray-300 space-y-2">
          <p>• Dhan API documentation: <a href="https://dhanhq.co/docs/v2/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">dhanhq.co/docs</a></p>
          <p>• For Data API subscription: <a href="https://knowledge.dhan.co/support/solutions/articles/82000909111" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">Subscription Guide</a></p>
          <p>• Dhan support: <a href="https://dhan.co/support" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">dhan.co/support</a></p>
        </div>
      </div>
    </div>
  )
}

