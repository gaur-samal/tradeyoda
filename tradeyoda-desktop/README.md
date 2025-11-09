# TradeYoda Desktop Packaging Project

Transform TradeYoda web application into standalone Windows & Mac desktop executables.

---

## 📋 Project Overview

**Goal:** Create installable desktop applications for TradeYoda that:
- Run completely offline (except license validation)
- Store data locally in OS-standard locations
- Prompt for license key on first run
- Work on Windows and macOS

**Status:** **Phase 1 Complete** ✅

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Electron Container              │
│  ┌────────────┐      ┌───────────────┐ │
│  │   React    │◄─────┤ Python Backend│ │
│  │  Frontend  │      │   (FastAPI)   │ │
│  │            │      │               │ │
│  │  (Port N/A)│      │  Port: 8000   │ │
│  └────────────┘      └───────────────┘ │
└─────────────────────────────────────────┘
           │
           ▼
    ┌────────────────┐
    │  User's Computer│
    │  ~/AppData/     │
    │  ~/Library/     │
    └────────────────┘
```

---

## 📚 Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| **[README.md](./README.md)** | This file - Project overview | ✅ |
| **[QUICK_START.md](./QUICK_START.md)** | Quick commands & checklist | ✅ |
| **[DESKTOP_PACKAGING_GUIDE.md](./DESKTOP_PACKAGING_GUIDE.md)** | Complete implementation guide with code | ✅ |
| **[PHASE1_BACKEND_SETUP.md](./PHASE1_BACKEND_SETUP.md)** | Phase 1 technical details | ✅ |

---

## 🚀 Quick Start

### Phase 1: Backend (COMPLETE ✅)

```bash
# Build backend executable
cd /app/tradeyoda
./build_backend.sh

# Test it
cd dist/tradeyoda-backend
./tradeyoda-backend
```

**Verification:**
- Backend starts on `http://127.0.0.1:8000`
- Health check: `curl http://127.0.0.1:8000/health`
- App data directory created in OS location

### Phase 2: Electron Setup (NEXT STEP)

**Prerequisites:**
```bash
# Install Node.js dependencies
cd /app/tradeyoda-desktop/electron
npm install
```

**Implementation:**
1. Copy code from [DESKTOP_PACKAGING_GUIDE.md - Phase 2](./DESKTOP_PACKAGING_GUIDE.md#phase-2-electron-setup)
2. Create `electron/main.js`, `electron/preload.js`, `electron/license-prompt.html`
3. Update `package.json` with build configuration
4. Test: `npm start`

### Phase 3: Frontend Adaptation

```bash
# Update API URL
# Edit /app/tradeyoda/frontend/.env
REACT_APP_BACKEND_URL=http://localhost:8000

# Build frontend
cd /app/tradeyoda/frontend
yarn build

# Copy to Electron
cp -r dist /app/tradeyoda-desktop/build
```

### Phase 4: Build Installers

```bash
cd /app/tradeyoda-desktop

# Windows
npm run build:win

# Mac
npm run build:mac

# Both
npm run build
```

**Output:**
```
release/
├── TradeYoda Setup 1.0.0.exe    # Windows installer
└── TradeYoda-1.0.0.dmg          # Mac installer
```

---

## 📁 Project Structure

```
/app/
├── tradeyoda/                      # Original web app
│   ├── backend/                   # FastAPI backend
│   ├── frontend/                  # React frontend
│   ├── src/
│   │   ├── config.py              # ✅ Desktop-aware
│   │   └── utils/
│   │       ├── desktop_config.py  # ✅ NEW
│   │       ├── licensing_client.py # ✅ Updated
│   │       └── security_master.py  # ✅ Updated
│   ├── backend_entrypoint.py      # ✅ NEW
│   ├── tradeyoda-backend.spec     # ✅ NEW
│   ├── build_backend.sh           # ✅ NEW
│   └── dist/
│       └── tradeyoda-backend/     # ✅ Executable
│
├── tradeyoda-desktop/              # NEW: Desktop project
│   ├── README.md                  # This file
│   ├── QUICK_START.md             # Quick reference
│   ├── DESKTOP_PACKAGING_GUIDE.md # Complete guide
│   ├── PHASE1_BACKEND_SETUP.md    # Phase 1 details
│   └── electron/                  # (Phase 2) To create
│       ├── main.js
│       ├── preload.js
│       ├── license-prompt.html
│       └── package.json
│
└── licensing-server/               # Existing licensing system
    ├── server.py
    └── admin-panel/
```

---

## ✨ Key Features

### Desktop-Aware Paths
Automatically uses OS-standard locations:

**Windows:**
```
C:\Users\{username}\AppData\Roaming\TradeYoda\
├── config.json
├── data/
│   ├── api-scrip-master.csv
│   └── credentials.json
├── logs/
└── cache/
    ├── .license_key
    └── .license_cache
```

**macOS:**
```
~/Library/Application Support/TradeYoda/
├── config.json
├── data/
├── logs/
└── cache/
```

### First-Run Experience
1. User installs and launches app
2. License prompt window appears
3. User enters license key
4. Backend validates with licensing server
5. On success, main app window opens
6. License persists for future launches

### Backward Compatibility
- All changes are **non-breaking**
- Web deployment continues to work
- Desktop mode auto-detects when packaged

---

## 🔧 Technical Details

### Mode Detection
```python
# Automatically detects if running as packaged app
if sys.frozen:  # PyInstaller
    desktop_mode = True
```

### Path Resolution
```python
# Desktop mode
DATA_DIR = ~/Library/Application Support/TradeYoda/data

# Web mode
DATA_DIR = /app/tradeyoda/data
```

### Backend Port
- **Desktop:** `127.0.0.1:8000` (localhost only)
- **Web:** `0.0.0.0:8001` (exposed via REACT_APP_BACKEND_URL)

---

## 📊 Progress Tracker

### Phase 1: Backend Preparation ✅
- [x] Create `desktop_config.py`
- [x] Update `src/config.py`
- [x] Update `licensing_client.py`
- [x] Update `security_master.py`
- [x] Create `backend_entrypoint.py`
- [x] Create PyInstaller spec file
- [x] Create build script
- [x] Test backend build
- [x] Verify desktop mode detection
- [x] Verify first-run detection

**Time Taken:** ~2 hours
**Result:** Backend successfully packaged as standalone executable

### Phase 2: Electron Setup (In Progress)
- [ ] Initialize Electron project
- [ ] Create main process
- [ ] Create preload script
- [ ] Create license prompt UI
- [ ] Test backend spawning
- [ ] Test license validation
- [ ] Test main window

**Estimated Time:** 2-3 hours

### Phase 3: Frontend Adaptation
- [ ] Update API URLs
- [ ] Build production bundle
- [ ] Copy to Electron project
- [ ] Test frontend-backend communication

**Estimated Time:** 1 hour

### Phase 4: Build & Distribution
- [ ] Configure electron-builder
- [ ] Build Windows installer
- [ ] Build Mac installer
- [ ] Test installations
- [ ] Create user guide

**Estimated Time:** 2 hours

**Total Estimated Time:** 6-8 hours

---

## 🧪 Testing

### Backend Tests ✅
```bash
# Test desktop mode
export TRADEYODA_DESKTOP_MODE=true
python backend_entrypoint.py

# Test packaged backend
cd dist/tradeyoda-backend
./tradeyoda-backend

# Verify endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/status
```

### Electron Tests (Phase 2)
```bash
# Dev mode
cd /app/tradeyoda-desktop
npm start

# Production build
npm run build:mac
# or
npm run build:win
```

### End-to-End Tests
- [ ] Fresh install
- [ ] License prompt appears
- [ ] License validation works
- [ ] Main app loads
- [ ] Trading features work
- [ ] Data persists after restart
- [ ] App uninstalls cleanly

---

## 🎯 Success Criteria

### Phase 1 ✅
- ✅ Backend builds as standalone executable
- ✅ Desktop mode auto-detected
- ✅ OS-specific paths used correctly
- ✅ First run detected properly
- ✅ Default files copied on first run

### Phase 2 (Upcoming)
- [ ] Electron app starts without errors
- [ ] Backend process spawns successfully
- [ ] License prompt shows on first run
- [ ] Main window loads after activation

### Phase 3 (Upcoming)
- [ ] Frontend builds without errors
- [ ] API calls reach backend
- [ ] All UI features work

### Phase 4 (Upcoming)
- [ ] Installers created for Windows & Mac
- [ ] Installation completes successfully
- [ ] App runs after installation
- [ ] Uninstallation works correctly

---

## 🚨 Known Limitations

### Code Signing
- **Windows:** App works but shows "Unknown Publisher" warning
- **Mac:** Users must manually approve in Security settings
- **Solution:** Purchase code signing certificates (~$300-400/year total)

### Updates
- **Method:** Manual download and reinstall
- **Future:** Can add auto-update with electron-updater

### Platform Support
- **Supported:** Windows 10+, macOS 10.13+
- **Not Supported:** Linux (can be added if needed)

---

## 📦 Distribution

### File Sizes
- **Windows Installer:** ~150-200 MB
- **Mac DMG:** ~180-220 MB

### Installation Flow
1. User downloads installer
2. Runs installer (shows security warnings if not signed)
3. App installs to Applications folder
4. User launches app
5. License prompt appears
6. User enters key and activates
7. Main app loads

---

## 🔗 Resources

### Documentation
- [Electron Documentation](https://www.electronjs.org/docs)
- [PyInstaller Manual](https://pyinstaller.org/)
- [electron-builder](https://www.electron.build/)

### Tools
- **PyInstaller:** Packages Python backend
- **Electron:** Desktop app framework
- **electron-builder:** Creates installers
- **Node.js:** Required for Electron development

---

## 💡 Tips & Best Practices

### Development
1. Test in desktop mode before packaging
2. Use `TRADEYODA_DESKTOP_MODE=true` flag for quick testing
3. Check logs in OS app data directory
4. Use Electron dev mode (`npm start`) for faster iteration

### Building
1. Always clean previous builds: `rm -rf dist/ build/ release/`
2. Test on clean VM or fresh OS install
3. Verify all files included in bundle

### Distribution
1. Test installer on different OS versions
2. Provide clear installation instructions
3. Include troubleshooting guide for users
4. Set up support channel for installation issues

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check logs
cat ~/Library/Application\ Support/TradeYoda/logs/*.log

# Test backend standalone
cd /app/tradeyoda/dist/tradeyoda-backend
./tradeyoda-backend
```

### License Prompt Won't Show
```bash
# Delete app data to reset
rm -rf ~/Library/Application\ Support/TradeYoda
```

### Build Fails
```bash
# Clean everything
rm -rf dist/ build/ release/ node_modules/

# Reinstall dependencies
pip install -r requirements.txt
npm install

# Rebuild
./build_backend.sh
npm run build
```

---

## 📞 Support

For implementation questions, refer to:
- **Quick Start:** [QUICK_START.md](./QUICK_START.md)
- **Complete Guide:** [DESKTOP_PACKAGING_GUIDE.md](./DESKTOP_PACKAGING_GUIDE.md)
- **Phase 1 Details:** [PHASE1_BACKEND_SETUP.md](./PHASE1_BACKEND_SETUP.md)

---

## ✅ Next Steps

1. **Review Phase 1 completion** ✅
   - Backend is packaged and tested
   - Desktop paths working correctly

2. **Start Phase 2 implementation**
   - Follow [DESKTOP_PACKAGING_GUIDE.md](./DESKTOP_PACKAGING_GUIDE.md#phase-2-electron-setup)
   - Copy Electron code examples
   - Test in dev mode

3. **Complete remaining phases**
   - Phase 3: Frontend adaptation
   - Phase 4: Build installers

4. **Distribution**
   - Test on clean machines
   - Create user documentation
   - Release to users

---

**Status:** Phase 1 Complete ✅ | Ready for Phase 2

**Last Updated:** 2025-01-19
