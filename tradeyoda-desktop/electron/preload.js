const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose safe APIs to renderer process
 */
contextBridge.exposeInMainWorld('electron', {
  // License activation
  activateLicense: (licenseKey) => {
    return ipcRenderer.invoke('activate-license', licenseKey);
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
