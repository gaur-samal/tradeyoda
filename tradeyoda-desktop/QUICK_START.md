# TradeYoda Desktop - Quick Start Guide

## Current Status: Phase 1 Complete ✅

### What's Done
- ✅ Backend desktop configuration
- ✅ Desktop-aware file paths
- ✅ PyInstaller setup
- ✅ Build automation scripts

### What's Next
- [ ] Electron setup (Phase 2)
- [ ] Frontend adaptation (Phase 3)
- [ ] Build installers (Phase 4)

---

## Quick Commands

### Build Backend Executable
```bash
cd /app/tradeyoda
./build_backend.sh
```

### Test Backend in Desktop Mode
```bash
export TRADEYODA_DESKTOP_MODE=true
python backend_entrypoint.py
```

### Test Packaged Backend
```bash
cd /app/tradeyoda/dist/tradeyoda-backend
./tradeyoda-backend
```

---

## File Structure

```
/app/
├── tradeyoda/                      # Original TradeYoda app
│   ├── backend/
│   │   ├── main.py                # FastAPI backend
│   │   └── middleware.py
│   ├── frontend/                  # React frontend
│   ├── src/
│   │   ├── config.py              # ✅ Updated for desktop
│   │   └── utils/
│   │       ├── desktop_config.py  # ✅ NEW: Desktop paths
│   │       ├── licensing_client.py # ✅ Updated
│   │       └── security_master.py  # ✅ Updated
│   ├── backend_entrypoint.py      # ✅ NEW: Desktop startup
│   ├── tradeyoda-backend.spec     # ✅ NEW: PyInstaller config
│   ├── build_backend.sh           # ✅ NEW: Build script
│   └── dist/
│       └── tradeyoda-backend/     # Generated executable
│
├── tradeyoda-desktop/              # Desktop packaging project
│   ├── DESKTOP_PACKAGING_GUIDE.md # Complete guide
│   ├── PHASE1_BACKEND_SETUP.md    # Phase 1 details
│   ├── QUICK_START.md             # This file
│   └── electron/                  # (Phase 2) Electron code
│
└── licensing-server/               # Licensing server
    ├── server.py
    └── admin-panel/
```

---

## Implementation Phases

### Phase 1: Backend Preparation ✅ COMPLETE
**Time:** ~2 hours

**What Was Done:**
1. Created `desktop_config.py` for OS-specific paths
2. Updated all file I/O to use desktop paths
3. Created PyInstaller configuration
4. Created build automation script

**Test:**
```bash
cd /app/tradeyoda
./build_backend.sh
cd dist/tradeyoda-backend
./tradeyoda-backend
# Should start on http://127.0.0.1:8000
```

### Phase 2: Electron Setup (Next)
**Time:** ~2-3 hours

**To Do:**
1. Initialize Electron project
2. Create main process (spawn backend)
3. Create license prompt window
4. Create main app window
5. Set up IPC communication

**Files to Create:**
- `electron/main.js` - Main Electron process
- `electron/preload.js` - IPC bridge
- `electron/license-prompt.html` - First-run UI
- `package.json` - Electron config

### Phase 3: Frontend Adaptation
**Time:** ~1 hour

**To Do:**
1. Update API URL to `localhost:8000`
2. Build production bundle
3. Copy to Electron project

### Phase 4: Packaging & Distribution
**Time:** ~2 hours

**To Do:**
1. Configure electron-builder
2. Build Windows installer (.exe)
3. Build Mac installer (.dmg)
4. Test installations

---

## Desktop Mode Behavior

### App Data Locations

**Windows:**
```
C:\Users\{username}\AppData\Roaming\TradeYoda\
```

**macOS:**
```
~/Library/Application Support/TradeYoda/
```

**Linux:**
```
~/.tradeyoda/
```

### First Run
1. App starts
2. Checks for license key file
3. If not found → Shows license prompt
4. User enters license key
5. Backend validates with licensing server
6. On success → Main app loads

### Subsequent Runs
1. App starts
2. License key found
3. Backend auto-validates (uses cache)
4. Main app loads immediately

---

## Key Features

### Automatic Mode Detection
```python
# Code automatically detects desktop vs web mode
if desktop_config.is_desktop_mode:
    # Use OS app data directory
    DATA_DIR = ~/Library/Application Support/TradeYoda/data
else:
    # Use current directory
    DATA_DIR = /app/tradeyoda/data
```

### Backward Compatibility
- All changes are non-breaking
- Web deployment works as before
- Desktop mode only activates when packaged

### Data Persistence
- User data survives app updates
- Stored in OS-standard locations
- License key persists across sessions

---

## Testing Checklist

### Phase 1 Tests ✅
- [x] Backend builds without errors
- [x] Desktop mode detected when `TRADEYODA_DESKTOP_MODE=true`
- [x] App data directories created correctly
- [x] First run detection works
- [x] Default files copied on first run
- [x] Backend starts on port 8000
- [x] Health endpoint responds

### Phase 2 Tests (Upcoming)
- [ ] Electron app starts
- [ ] Backend process spawns
- [ ] License prompt shows on first run
- [ ] License activation works
- [ ] Main window loads after activation
- [ ] Frontend connects to backend

### Phase 3 Tests (Upcoming)
- [ ] Frontend builds successfully
- [ ] API calls reach backend
- [ ] UI renders correctly
- [ ] All features work

### Phase 4 Tests (Upcoming)
- [ ] Windows installer builds
- [ ] Mac installer builds
- [ ] Installation completes successfully
- [ ] App runs after installation
- [ ] Uninstallation works

---

## Development Workflow

### 1. Continue Backend Development
```bash
# Work in dev mode as usual
cd /app/tradeyoda
python backend/main.py
```

### 2. Test Desktop Mode
```bash
# Set desktop mode flag
export TRADEYODA_DESKTOP_MODE=true
python backend_entrypoint.py
```

### 3. Build for Desktop
```bash
# Build backend
./build_backend.sh

# (Phase 2) Build Electron
cd /app/tradeyoda-desktop
npm run build
```

---

## Troubleshooting

### Build Fails
```bash
# Check Python version (3.8+)
python --version

# Install PyInstaller
pip install pyinstaller

# Install dependencies
pip install -r requirements.txt
```

### Import Errors
```bash
# Add missing module to tradeyoda-backend.spec
# in hiddenimports list
```

### Path Issues
```bash
# Check desktop mode detection
python -c "from src.utils.desktop_config import desktop_config; print(desktop_config.is_desktop_mode)"
```

### First Run Not Working
```bash
# Delete app data
rm -rf ~/Library/Application\ Support/TradeYoda
# or
del /s "C:\Users\{username}\AppData\Roaming\TradeYoda"
```

---

## Resources

### Documentation
- [DESKTOP_PACKAGING_GUIDE.md](./DESKTOP_PACKAGING_GUIDE.md) - Complete implementation guide
- [PHASE1_BACKEND_SETUP.md](./PHASE1_BACKEND_SETUP.md) - Backend setup details

### Code Examples
- All Electron code provided in `DESKTOP_PACKAGING_GUIDE.md`
- Copy-paste ready for Phase 2 implementation

### External Links
- [PyInstaller Docs](https://pyinstaller.org/)
- [Electron Docs](https://www.electronjs.org/docs)
- [electron-builder](https://www.electron.build/)

---

## Support

### Common Questions

**Q: Will the web version still work?**
A: Yes! All changes are backward compatible.

**Q: How do users get updates?**
A: Manual download for v1. Auto-update can be added later.

**Q: What about code signing?**
A: Optional. Windows works without it (with warning). Mac requires user approval.

**Q: Can I test without building?**
A: Yes! Set `TRADEYODA_DESKTOP_MODE=true` and run `backend_entrypoint.py`

**Q: Where are logs stored?**
A: `~/Library/Application Support/TradeYoda/logs/` (or Windows equivalent)

---

## Next Actions

### Immediate (Phase 2)
1. Create `/app/tradeyoda-desktop/electron/` directory
2. Copy Electron code from `DESKTOP_PACKAGING_GUIDE.md`
3. Run `npm install` to install dependencies
4. Test Electron in dev mode

### After Phase 2
1. Adapt frontend for desktop
2. Build production installers
3. Test on clean machines
4. Distribute to users

---

**Ready to start Phase 2?** See [DESKTOP_PACKAGING_GUIDE.md](./DESKTOP_PACKAGING_GUIDE.md#phase-2-electron-setup)
