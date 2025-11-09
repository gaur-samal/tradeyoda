import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8100';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== LICENSE ENDPOINTS ====================

export const createLicense = (data) => {
  return api.post('/api/licenses/create', data);
};

export const getAllLicenses = (skip = 0, limit = 100) => {
  return api.get(`/api/admin/licenses?skip=${skip}&limit=${limit}`);
};

export const getLicenseDetails = (licenseKey) => {
  return api.get(`/api/admin/licenses/${licenseKey}`);
};

export const revokeLicense = (licenseKey) => {
  return api.post(`/api/admin/licenses/${licenseKey}/revoke`);
};

export const deleteLicense = (licenseKey) => {
  return api.delete(`/api/admin/licenses/${licenseKey}`);
};

export const bulkDeleteLicenses = (licenseKeys) => {
  return api.post('/api/admin/licenses/bulk-delete', { license_keys: licenseKeys });
};

// ==================== OPENAI KEY ENDPOINTS ====================

export const addOpenAIKey = (data) => {
  return api.post('/api/admin/openai-keys', data);
};

export const getOpenAIKeys = () => {
  return api.get('/api/admin/openai-keys');
};

// ==================== SCRIP MASTER ENDPOINTS ====================

export const uploadScripMaster = (file, version) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return api.post(`/api/admin/scrip-master/upload?version=${version}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getScripMasterVersion = () => {
  return api.get('/api/scrip-master/version');
};

// ==================== STATISTICS ENDPOINTS ====================

export const getStatistics = () => {
  return api.get('/api/admin/stats');
};

// ==================== HEALTH CHECK ====================

export const healthCheck = () => {
  return api.get('/health');
};

export default api;
