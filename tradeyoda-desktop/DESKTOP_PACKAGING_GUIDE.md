# TradeYoda Desktop Packaging Guide
**Complete Guide to Creating Windows & Mac Executables**

---

## Table of Contents
1. [Overview](#overview)
2. [Phase 1: Backend Preparation](#phase-1-backend-preparation) ✅ COMPLETE
3. [Phase 2: Electron Setup](#phase-2-electron-setup)
4. [Phase 3: Frontend Adaptation](#phase-3-frontend-adaptation)
5. [Phase 4: Packaging & Distribution](#phase-4-packaging--distribution)
6. [Testing Guide](#testing-guide)
7. [Distribution](#distribution)

---

## Overview

### Architecture
```
TradeYoda Desktop App
│
├── Electron (Main Container)
│   ├── Main Process
│   │   ├── Spawns Python Backend (subprocess)
│   │   ├── Creates Application Window
│   │   ├── Handles License Prompt (first run)
│   │   └── IPC Communication
│   │
│   └── Renderer Process
│       └── React Frontend (Vite build)
│
└── Backend (Python/FastAPI)
    ├── Packaged with PyInstaller
    ├── Runs on localhost:8000
    └── Manages Trading Logic
```

### Data Flow
```
User → Electron Window → React Frontend
                ↓
        API Calls (http://localhost:8000)
                ↓
        Python Backend → Dhan API
```

---

## Phase 1: Backend Preparation ✅

### Status: **COMPLETE**

### What Was Done:
1. ✅ Created `src/utils/desktop_config.py` - Desktop path management
2. ✅ Updated `src/config.py` - Desktop-aware BASE_DIR
3. ✅ Updated `src/utils/licensing_client.py` - Desktop cache paths
4. ✅ Updated `src/utils/security_master.py` - Desktop scrip master path
5. ✅ Created `backend_entrypoint.py` - Desktop startup script
6. ✅ Created `tradeyoda-backend.spec` - PyInstaller configuration
7. ✅ Created `build_backend.sh` - Build automation

### Build Backend:
```bash
cd /app/tradeyoda
./build_backend.sh
```

### Output:
```
dist/tradeyoda-backend/
└── tradeyoda-backend(.exe)
```

**See [PHASE1_BACKEND_SETUP.md](./PHASE1_BACKEND_SETUP.md) for details.**

---

## Phase 2: Electron Setup

### 2.1 Initialize Electron Project

```bash
# Create electron directory
mkdir -p /app/tradeyoda-desktop/electron
cd /app/tradeyoda-desktop/electron

# Initialize npm project
npm init -y

# Install Electron dependencies
npm install --save electron
npm install --save electron-builder
npm install --save-dev electron-is-dev
```

### 2.2 Create Main Process (`electron/main.js`)

```javascript
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
```

### 2.3 Create Preload Script (`electron/preload.js`)

```javascript
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
```

### 2.4 Create License Prompt HTML (`electron/license-prompt.html`)

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TradeYoda - License Activation</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      padding: 20px;
    }
    
    .container {
      background: white;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      padding: 40px;
      max-width: 500px;
      width: 100%;
    }
    
    h1 {
      color: #333;
      margin-bottom: 10px;
      font-size: 28px;
    }
    
    .subtitle {
      color: #666;
      margin-bottom: 30px;
      font-size: 14px;
    }
    
    label {
      display: block;
      color: #555;
      font-weight: 600;
      margin-bottom: 8px;
      font-size: 14px;
    }
    
    input {
      width: 100%;
      padding: 12px;
      border: 2px solid #e0e0e0;
      border-radius: 6px;
      font-size: 14px;
      transition: border-color 0.3s;
    }
    
    input:focus {
      outline: none;
      border-color: #667eea;
    }
    
    button {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 20px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    
    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    button:active {
      transform: translateY(0);
    }
    
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }
    
    .error {
      color: #e74c3c;
      margin-top: 12px;
      font-size: 13px;
      display: none;
    }
    
    .success {
      color: #27ae60;
      margin-top: 12px;
      font-size: 13px;
      display: none;
    }
    
    .info {
      background: #f8f9fa;
      border-left: 4px solid #667eea;
      padding: 12px;
      margin-top: 20px;
      border-radius: 4px;
      font-size: 13px;
      color: #555;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🧙‍♂️ Welcome to TradeYoda</h1>
    <p class="subtitle">Enter your license key to get started</p>
    
    <form id="licenseForm">
      <label for="licenseKey">License Key</label>
      <input 
        type="text" 
        id="licenseKey" 
        placeholder="XXXX-XXXX-XXXX-XXXX"
        required
      />
      
      <button type="submit" id="submitBtn">Activate License</button>
      
      <div class="error" id="errorMsg"></div>
      <div class="success" id="successMsg"></div>
    </form>
    
    <div class="info">
      <strong>Don't have a license key?</strong><br>
      Contact us to purchase or request a trial.
    </div>
  </div>

  <script>
    const form = document.getElementById('licenseForm');
    const licenseInput = document.getElementById('licenseKey');
    const submitBtn = document.getElementById('submitBtn');
    const errorMsg = document.getElementById('errorMsg');
    const successMsg = document.getElementById('successMsg');
    
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const licenseKey = licenseInput.value.trim();
      
      if (!licenseKey) {
        showError('Please enter a license key');
        return;
      }
      
      // Disable form
      submitBtn.disabled = true;
      submitBtn.textContent = 'Validating...';
      hideMessages();
      
      try {
        // Call backend API to activate license
        const response = await fetch('http://127.0.0.1:8000/api/license/activate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ license_key: licenseKey })
        });
        
        const data = await response.json();
        
        if (data.success) {
          showSuccess('License activated successfully!');
          
          // Notify Electron main process
          setTimeout(() => {
            window.close();
          }, 1500);
        } else {
          showError(data.error || 'License activation failed');
          submitBtn.disabled = false;
          submitBtn.textContent = 'Activate License';
        }
      } catch (err) {
        console.error('Activation error:', err);
        showError('Failed to connect to licensing server');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Activate License';
      }
    });
    
    function showError(message) {
      errorMsg.textContent = message;
      errorMsg.style.display = 'block';
    }
    
    function showSuccess(message) {
      successMsg.textContent = message;
      successMsg.style.display = 'block';
    }
    
    function hideMessages() {
      errorMsg.style.display = 'none';
      successMsg.style.display = 'none';
    }
  </script>
</body>
</html>
```

### 2.5 Update `package.json`

```json
{
  "name": "tradeyoda-desktop",
  "version": "1.0.0",
  "description": "TradeYoda AI Trading System - Desktop Application",
  "main": "electron/main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux"
  },
  "build": {
    "appId": "com.tradeyoda.app",
    "productName": "TradeYoda",
    "directories": {
      "output": "release"
    },
    "files": [
      "electron/**/*",
      "build/**/*"
    ],
    "extraResources": [
      {
        "from": "../tradeyoda/dist/tradeyoda-backend",
        "to": "backend",
        "filter": ["**/*"]
      }
    ],
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "mac": {
      "target": "dmg",
      "icon": "assets/icon.icns",
      "category": "public.app-category.finance"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    }
  },
  "dependencies": {
    "electron": "^28.0.0",
    "electron-is-dev": "^2.0.0"
  },
  "devDependencies": {
    "electron-builder": "^24.9.1"
  }
}
```

---

## Phase 3: Frontend Adaptation

### 3.1 Update Frontend API URL

Edit `/app/tradeyoda/frontend/.env`:

```env
# Desktop mode - connect to local backend
REACT_APP_BACKEND_URL=http://localhost:8000
```

### 3.2 Build Frontend for Production

```bash
cd /app/tradeyoda/frontend
yarn build
```

### 3.3 Copy Build to Electron

```bash
cp -r /app/tradeyoda/frontend/dist /app/tradeyoda-desktop/build
```

---

## Phase 4: Packaging & Distribution

### 4.1 Build Complete App

```bash
cd /app/tradeyoda-desktop

# Build for Windows
npm run build:win

# Build for Mac
npm run build:mac

# Build for both
npm run build
```

### 4.2 Output

```
tradeyoda-desktop/release/
├── TradeYoda Setup 1.0.0.exe      # Windows installer
└── TradeYoda-1.0.0.dmg             # Mac installer
```

---

## Testing Guide

### Test Backend Standalone
```bash
cd /app/tradeyoda/dist/tradeyoda-backend
./tradeyoda-backend
```

### Test Electron Dev Mode
```bash
cd /app/tradeyoda-desktop
npm start
```

### Test Desktop Package
```bash
# After building
cd release
# Windows
./TradeYoda\ Setup\ 1.0.0.exe

# Mac
open TradeYoda-1.0.0.dmg
```

---

## Distribution

### File Sizes (Approximate)
- **Windows:** ~150-200 MB
- **Mac:** ~180-220 MB

### Distribution Checklist
- [ ] Backend builds successfully
- [ ] Frontend builds successfully
- [ ] Electron packages successfully
- [ ] First-run license prompt works
- [ ] Main app loads after activation
- [ ] Trading features work
- [ ] Data persists after restart
- [ ] Logs are accessible

---

## Troubleshooting

### Backend Not Starting
```bash
# Check backend logs
cat ~/Library/Application\ Support/TradeYoda/logs/*.log
```

### License Prompt Not Showing
```bash
# Delete app data
rm -rf ~/Library/Application\ Support/TradeYoda
```

### Build Errors
```bash
# Clean and rebuild
rm -rf release/ dist/ build/
npm run build
```

---

## Next Steps

1. **Complete Phase 2:** Implement Electron setup as documented
2. **Test Integration:** Ensure backend + frontend communication works
3. **Build Installers:** Package for Windows and Mac
4. **User Testing:** Deploy to test users
5. **Iterate:** Fix issues, improve UX

---

**Status:** Phase 1 Complete ✅ | Ready for Phase 2
