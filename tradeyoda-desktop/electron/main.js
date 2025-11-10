const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const isDev = require('electron-is-dev');
const fs = require('fs');

let mainWindow = null;
let backendProcess = null;
let licenseWindow = null;

// App data paths
const appDataPath = app.getPath('userData');
const cacheDir = path.join(appDataPath, 'cache');
const licenseKeyPath = path.join(cacheDir, '.license_key');

/**
 * Ensure cache directory exists
 */
function ensureCacheDir() {
  if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir, { recursive: true });
  }
}

/**
 * Check if this is the first run
 */
function isFirstRun() {
  ensureCacheDir();
  return !fs.existsSync(licenseKeyPath);
}

/**
 * Start Python Backend Process
 */
function startBackend() {
  console.log('🚀 Starting Python backend...');
  
  // Get backend executable path
  const backendPath = isDev
    ? path.join(__dirname, '../../tradeyoda/backend_entrypoint.py')
    : path.join(process.resourcesPath, 'backend', 'tradeyoda-backend');
  
  console.log(`Backend path: ${backendPath}`);
  
  // Spawn backend process
  const command = isDev ? 'python3' : backendPath;
  const args = isDev ? [backendPath] : [];
  
  backendProcess = spawn(command, args, {
    env: { 
      ...process.env, 
      BACKEND_PORT: '8000',
      TRADEYODA_DESKTOP_MODE: 'true'
    },
    stdio: 'inherit' // Show backend logs in console
  });
  
  backendProcess.on('error', (err) => {
    console.error('❌ Backend failed to start:', err);
    dialog.showErrorBox('Backend Error', `Failed to start backend: ${err.message}`);
    app.quit();
  });
  
  backendProcess.on('exit', (code) => {
    console.log(`⚠️ Backend exited with code ${code}`);
    if (code !== 0 && code !== null) {
      dialog.showErrorBox('Backend Crashed', 'The backend process has stopped unexpectedly.');
    }
  });
  
  console.log('✅ Backend process started');
}

/**
 * Create License Prompt Window (First Run)
 */
function createLicenseWindow() {
  licenseWindow = new BrowserWindow({
    width: 600,
    height: 450,
    resizable: false,
    modal: true,
    title: 'TradeYoda - License Activation',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });
  
  // Load license prompt HTML
  licenseWindow.loadFile(path.join(__dirname, 'license-prompt.html'));
  
  // Open DevTools in development
  if (isDev) {
    licenseWindow.webContents.openDevTools();
  }
  
  licenseWindow.on('closed', () => {
    licenseWindow = null;
  });
}

/**
 * Create Main Application Window
 */
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: 'TradeYoda - AI Trading System',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });
  
  // Load React frontend
  const frontendURL = isDev
    ? 'http://localhost:3000'  // Vite dev server
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  console.log(`Loading frontend from: ${frontendURL}`);
  mainWindow.loadURL(frontendURL);
  
  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Wait for Backend to be Ready
 */
async function waitForBackend(maxAttempts = 30) {
  const http = require('http');
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get('http://127.0.0.1:8000/health', (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else {
            reject(new Error(`Status ${res.statusCode}`));
          }
        });
        
        req.on('error', reject);
        req.setTimeout(1000);
      });
      
      console.log('✅ Backend is ready');
      return true;
    } catch (err) {
      // Backend not ready yet
    }
    
    // Wait 1 second before retry
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  console.error('❌ Backend did not start in time');
  return false;
}

/**
 * Handle License Activation from Renderer
 */
ipcMain.handle('activate-license', async (event, licenseKey) => {
  try {
    const http = require('http');
    
    // Call backend to activate license
    const postData = JSON.stringify({ license_key: licenseKey });
    
    const options = {
      hostname: '127.0.0.1',
      port: 8000,
      path: '/api/license/activate',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };
    
    return new Promise((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            const result = JSON.parse(data);
            resolve(result);
          } catch (err) {
            reject(err);
          }
        });
      });
      
      req.on('error', reject);
      req.write(postData);
      req.end();
    });
  } catch (err) {
    return { success: false, error: err.message };
  }
});

/**
 * Handle License Success - Close license window and open main app
 */
ipcMain.on('license-activated', () => {
  console.log('✅ License activated successfully');
  
  // Close license window
  if (licenseWindow) {
    licenseWindow.close();
  }
  
  // Open main window
  createMainWindow();
});

/**
 * Get App Version
 */
ipcMain.handle('get-version', () => {
  return app.getVersion();
});

/**
 * App Ready Event
 */
app.on('ready', async () => {
  console.log('🚀 TradeYoda Desktop Starting...');
  console.log(`App data path: ${appDataPath}`);
  console.log(`Is first run: ${isFirstRun()}`);
  
  // Start backend
  startBackend();
  
  // Wait for backend to be ready
  const backendReady = await waitForBackend();
  if (!backendReady) {
    dialog.showErrorBox('Startup Error', 'Backend failed to start. Please check logs.');
    app.quit();
    return;
  }
  
  // Check first run
  if (isFirstRun()) {
    console.log('🎉 First run detected - showing license prompt');
    createLicenseWindow();
  } else {
    console.log('✅ License found - starting main app');
    createMainWindow();
  }
});

/**
 * Quit when all windows are closed
 */
app.on('window-all-closed', () => {
  // Kill backend process
  if (backendProcess) {
    console.log('🛑 Stopping backend...');
    backendProcess.kill();
  }
  
  // Quit app
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * macOS: Re-create window when dock icon clicked
 */
app.on('activate', () => {
  if (mainWindow === null && !isFirstRun()) {
    createMainWindow();
  }
});

/**
 * Handle app quit
 */
app.on('before-quit', () => {
  // Ensure backend is killed
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
  }
});
