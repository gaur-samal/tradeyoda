const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const isDev = require('electron-is-dev');
const fs = require('fs');

let mainWindow = null;
let backendProcess = null;
let licenseWindow = null;

// App data paths
const appDataPath = app.getPath('userData');
const licenseKeyPath = path.join(appDataPath, 'cache', '.license_key');

/**
 * Check if this is the first run
 */
function isFirstRun() {
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
  
  // Spawn backend process
  const command = isDev ? 'python3' : backendPath;
  const args = isDev ? [backendPath] : [];
  
  backendProcess = spawn(command, args, {
    env: { ...process.env, BACKEND_PORT: '8000' },
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
  
  console.log('✅ Backend started');
}

/**
 * Create License Prompt Window (First Run)
 */
function createLicenseWindow() {
  licenseWindow = new BrowserWindow({
    width: 600,
    height: 400,
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
  const fetch = require('node-fetch');
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch('http://127.0.0.1:8000/health');
      if (response.ok) {
        console.log('✅ Backend is ready');
        return true;
      }
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
 * App Ready Event
 */
app.on('ready', async () => {
  console.log('🚀 TradeYoda Desktop Starting...');
  
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
 * Handle License Activation Success
 */
app.on('license-activated', () => {
  console.log('✅ License activated successfully');
  
  // Close license window
  if (licenseWindow) {
    licenseWindow.close();
  }
  
  // Open main window
  createMainWindow();
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
  if (mainWindow === null) {
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
