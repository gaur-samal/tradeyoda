import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Key, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

// Use relative URLs to work with nginx proxy
const API_BASE = '';

const LicenseSettings = () => {
  const [licenseStatus, setLicenseStatus] = useState(null);
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [showActivation, setShowActivation] = useState(false);

  // Fetch current license status
  useEffect(() => {
    fetchLicenseStatus();
  }, []);

  const fetchLicenseStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/license/status`);
      setLicenseStatus(response.data);
      
      // Show activation form if not licensed
      if (!response.data.licensed) {
        setShowActivation(true);
      }
    } catch (error) {
      console.error('Error fetching license status:', error);
      setShowActivation(true);
    }
  };

  const handleActivate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      console.log('Activating license...', licenseKey);
      const response = await axios.post(`${API_BASE}/api/license/activate`, {
        license_key: licenseKey.trim()
      });

      if (response.data.success) {
        setMessage('✅ License activated successfully! Tier: ' + response.data.tier);
        setLicenseKey('');
        setShowActivation(false);
        setTimeout(() => {
          fetchLicenseStatus();
          setMessage('');
        }, 2000);
      } else {
        setMessage(`❌ ${response.data.error}`);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.error || 'Activation failed';
      setMessage(`❌ ${errorMsg}`);
      console.error('Activation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevalidate = async () => {
    setLoading(true);
    setMessage('');
    try {
      const response = await axios.post(`${API_BASE}/api/license/validate`);
      if (response.data.success) {
        setMessage('✅ License revalidated successfully!');
        setTimeout(() => {
          fetchLicenseStatus();
          setMessage('');
        }, 2000);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Validation failed';
      setMessage(`❌ ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const getTierBadgeClass = (tier) => {
    const classes = {
      TRIAL: 'bg-orange-100 text-orange-800 border-orange-300',
      BASIC: 'bg-blue-100 text-blue-800 border-blue-300',
      ADVANCED: 'bg-purple-100 text-purple-800 border-purple-300',
      PRO: 'bg-yellow-100 text-yellow-800 border-yellow-300'
    };
    return classes[tier] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="card p-6 border-2 border-purple-500/30">
      <div className="flex items-center gap-3 mb-6">
        <Shield className="w-6 h-6 text-purple-400" />
        <h3 className="text-xl font-bold">🔐 License Management</h3>
      </div>

      {/* Current License Status */}
      {licenseStatus && (
        <div className={`mb-6 p-4 rounded-lg ${
          licenseStatus.licensed 
            ? 'bg-green-500/10 border border-green-500/30' 
            : 'bg-yellow-500/10 border border-yellow-500/30'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold">Current License Status</h4>
            {licenseStatus.licensed && (
              <span className={`px-4 py-1 rounded-full text-sm font-semibold border-2 ${getTierBadgeClass(licenseStatus.tier)}`}>
                {licenseStatus.tier}
              </span>
            )}
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white/5 p-4 rounded-lg">
              <p className="text-sm text-gray-400">Status</p>
              <p className="text-lg font-semibold">
                {licenseStatus.licensed ? '✅ Active' : '❌ Not Licensed'}
              </p>
            </div>
            
            <div className="bg-white/5 p-4 rounded-lg">
              <p className="text-sm text-gray-400">OpenAI Model</p>
              <p className="text-lg font-semibold">{licenseStatus.openai_model}</p>
            </div>
            
            <div className="bg-white/5 p-4 rounded-lg">
              <p className="text-sm text-gray-400">Manual Trading</p>
              <p className="text-lg font-semibold">
                {licenseStatus.manual_trading_enabled ? '✅ Enabled' : '❌ Disabled'}
              </p>
            </div>
            
            <div className="bg-white/5 p-4 rounded-lg">
              <p className="text-sm text-gray-400">Auto Trading</p>
              <p className="text-lg font-semibold">
                {licenseStatus.auto_trading_enabled ? '✅ Enabled' : '❌ Disabled'}
              </p>
            </div>
          </div>

          {licenseStatus.expires_at && licenseStatus.expires_at !== 'Never' && (
            <div className="bg-white/5 p-4 rounded-lg mb-4">
              <p className="text-sm text-gray-400">Expires On</p>
              <p className="text-lg font-semibold">
                {new Date(licenseStatus.expires_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              onClick={handleRevalidate}
              disabled={loading}
              className="btn btn-primary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Validating...' : 'Revalidate License'}
            </button>
            
            <button
              onClick={() => setShowActivation(!showActivation)}
              className="btn btn-secondary flex items-center gap-2"
            >
              <Key className="w-4 h-4" />
              {showActivation ? 'Cancel' : 'Change License'}
            </button>
          </div>
        </div>
      )}

      {/* Activate New License */}
      {showActivation && (
        <div className="bg-white/5 p-6 rounded-lg border border-gray-700 mb-6">
          <h4 className="font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            {licenseStatus?.licensed ? 'Change License' : 'Activate New License'}
          </h4>
          <form onSubmit={handleActivate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-400">
                License Key
              </label>
              <input
                type="text"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
                placeholder="TYODA-XXXX-XXXX-XXXX-XXXX"
                className="w-full px-4 py-3 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono bg-white/5 border-gray-700"
                required
                pattern="^TYODA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
                title="Format: TYODA-XXXX-XXXX-XXXX-XXXX"
              />
              <p className="text-xs text-gray-500 mt-1">
                Format: TYODA-XXXX-XXXX-XXXX-XXXX (case insensitive)
              </p>
            </div>
            
            <button
              type="submit"
              disabled={loading || !licenseKey.trim()}
              className="btn btn-success w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Activating...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Activate License
                </>
              )}
            </button>
          </form>

          {message && (
            <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 ${
              message.includes('✅') 
                ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                : 'bg-red-500/20 text-red-400 border border-red-500/30'
            }`}>
              {message.includes('✅') ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              {message}
            </div>
          )}
        </div>
      )}

      {/* Feature Matrix */}
      <div className="bg-white/5 p-6 rounded-lg border border-gray-700">
        <h4 className="font-semibold mb-4">📊 Tier Comparison</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-700">
                <th className="text-left py-3 px-2 font-semibold text-gray-400">Feature</th>
                <th className="text-center py-3 px-2">
                  <span className="inline-block px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold">TRIAL</span>
                  <div className="text-xs text-gray-500 mt-1">14 days</div>
                </th>
                <th className="text-center py-3 px-2">
                  <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">BASIC</span>
                  <div className="text-xs text-gray-500 mt-1">3 months</div>
                </th>
                <th className="text-center py-3 px-2">
                  <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold">ADVANCED</span>
                  <div className="text-xs text-gray-500 mt-1">6 months</div>
                </th>
                <th className="text-center py-3 px-2">
                  <span className="inline-block px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-semibold">PRO</span>
                  <div className="text-xs text-gray-500 mt-1">1 year</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-700 hover:bg-white/5">
                <td className="py-3 px-2 font-medium">Zone Analysis</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
              </tr>
              <tr className="border-b border-gray-700 hover:bg-white/5">
                <td className="py-3 px-2 font-medium">Manual Trading</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
                <td className="text-center py-3 px-2 text-2xl">❌</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
              </tr>
              <tr className="border-b border-gray-700 hover:bg-white/5">
                <td className="py-3 px-2 font-medium">Auto Trading</td>
                <td className="text-center py-3 px-2 text-2xl">❌</td>
                <td className="text-center py-3 px-2 text-2xl">❌</td>
                <td className="text-center py-3 px-2 text-2xl">❌</td>
                <td className="text-center py-3 px-2 text-2xl">✅</td>
              </tr>
              <tr className="hover:bg-white/5">
                <td className="py-3 px-2 font-medium">OpenAI Model</td>
                <td className="text-center py-3 px-2">
                  <code className="text-xs bg-gray-800 px-2 py-1 rounded">gpt-4o-mini</code>
                </td>
                <td className="text-center py-3 px-2">
                  <code className="text-xs bg-gray-800 px-2 py-1 rounded">gpt-4o-mini</code>
                </td>
                <td className="text-center py-3 px-2">
                  <code className="text-xs bg-gray-800 px-2 py-1 rounded">gpt-4o</code>
                </td>
                <td className="text-center py-3 px-2">
                  <code className="text-xs bg-gray-800 px-2 py-1 rounded">gpt-4.1</code>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-blue-500/10 p-4 rounded-lg border border-blue-500/30">
        <h4 className="font-semibold text-blue-400 mb-2">ℹ️ Need Help?</h4>
        <ul className="text-sm text-gray-400 space-y-1">
          <li>• License keys are provided after purchase</li>
          <li>• The app works offline for 24 hours with cached validation</li>
          <li>• Contact support if you have activation issues</li>
          <li>• License expires based on your tier (shown above)</li>
        </ul>
      </div>
    </div>
  );
};

export default LicenseSettings;
