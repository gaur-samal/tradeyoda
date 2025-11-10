const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose safe APIs to renderer process
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // License activation
  activateLicense: (licenseKey) => {
    return ipcRenderer.invoke('activate-license', licenseKey);
  },
  
  // Notify main process of successful activation
  notifyLicenseActivated: () => {
    ipcRenderer.send('license-activated');
  },
  
  // App info
  getVersion: () => {
    return ipcRenderer.invoke('get-version');
  },
  
  // Platform info
  getPlatform: () => {
    return process.platform;
  }
});
