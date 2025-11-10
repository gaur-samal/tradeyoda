# Testing Guide - Electron Desktop App

## Current Situation

You've successfully:
✅ Created Electron project structure
✅ Installed dependencies (`npm install`)

But `npm start` won't work yet because:
❌ Frontend not built
❌ Backend not packaged for desktop

---

## Testing Options

### Option 1: Full Integration Test (Recommended)

Test the complete desktop app flow:

#### Step 1: Build Backend (if not done)
```bash
cd /app/tradeyoda
./build_backend.sh
# Output: dist/tradeyoda-backend/tradeyoda-backend
```

#### Step 2: Build Frontend
```bash
cd /app/tradeyoda/frontend
yarn build
# Output: dist/
```

#### Step 3: Copy Frontend to Electron
```bash
cp -r /app/tradeyoda/frontend/dist /app/tradeyoda-desktop/build
```

#### Step 4: Update Frontend API URL
Edit `/app/tradeyoda/frontend/.env` (or `dist/assets/index.*.js` after build):
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

Or create a new `.env.production`:
```bash
cd /app/tradeyoda/frontend
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env.production
yarn build
```

#### Step 5: Start Electron
```bash
cd /app/tradeyoda-desktop
npm start
```

**What happens:**
1. Electron window opens
2. Backend spawns (Python process)
3. First run → License prompt appears
4. Enter license key → Validates
5. Main app opens → React frontend loads

---

### Option 2: Development Mode Test (Easier)

Test without building everything:

#### Step 1: Start Backend Manually
```bash
# Terminal 1
cd /app/tradeyoda
python3 backend_entrypoint.py
# Backend runs on http://localhost:8000
```

#### Step 2: Start Frontend Dev Server
```bash
# Terminal 2
cd /app/tradeyoda/frontend
yarn dev
# Frontend runs on http://localhost:3000
```

#### Step 3: Test Backend
```bash
# Terminal 3
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

#### Step 4: Test License Prompt HTML
```bash
cd /app/tradeyoda-desktop
# Open in browser
open electron/license-prompt.html  # Mac
# or
xdg-open electron/license-prompt.html  # Linux
# or manually open in browser
```

---

### Option 3: Mock Testing (Quick)

Test Electron without backend/frontend:

#### Create a simple test HTML:
```bash
cd /app/tradeyoda-desktop
cat > electron/test.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <title>Test</title>
</head>
<body>
  <h1>Electron Test</h1>
  <p>If you see this, Electron is working!</p>
  <button onclick="alert('Electron works!')">Test</button>
</body>
</html>
EOF
```

#### Modify electron/main.js temporarily:
Change line that loads frontend:
```javascript
// Instead of:
mainWindow.loadURL(frontendURL);

// Use:
mainWindow.loadFile(path.join(__dirname, 'test.html'));
```

#### Run:
```bash
npm start
```

---

## Troubleshooting

### Error: "electron: not found"
**Solution:** Run `npm install` first

### Error: "Backend failed to start"
**Cause:** PyInstaller executable not found or Python backend has errors

**Solution:**
1. Check backend was built: `ls -la /app/tradeyoda/dist/tradeyoda-backend/`
2. Test backend manually: `cd /app/tradeyoda && python3 backend_entrypoint.py`

### Error: "Cannot load frontend"
**Cause:** Frontend build doesn't exist at expected path

**Solution:**
1. Build frontend: `cd /app/tradeyoda/frontend && yarn build`
2. Copy to Electron: `cp -r dist /app/tradeyoda-desktop/build`

### License prompt appears but activation fails
**Cause:** Backend not running or wrong URL

**Check:**
1. Backend is running: `curl http://localhost:8000/health`
2. License endpoint works: `curl http://localhost:8000/api/license/status`

### Window opens but is blank
**Cause:** Frontend build not found or CORS issues

**Solution:**
1. Check build exists: `ls /app/tradeyoda-desktop/build/index.html`
2. Check DevTools console for errors (open with Cmd+Option+I or Ctrl+Shift+I)

---

## Quick Test Checklist

Before `npm start`:
- [ ] Dependencies installed (`node_modules/` exists)
- [ ] Backend built (`/app/tradeyoda/dist/tradeyoda-backend/` exists)
- [ ] Frontend built and copied (`/app/tradeyoda-desktop/build/index.html` exists)
- [ ] Frontend API URL points to `localhost:8000`

---

## Recommended Testing Flow

### For Initial Testing (Development Mode):
```bash
# Start backend manually
cd /app/tradeyoda
export TRADEYODA_DESKTOP_MODE=true
python3 backend_entrypoint.py &

# Wait for backend to start (check logs)

# Test Electron (will show license prompt or error)
cd /app/tradeyoda-desktop
npm start
```

### For Full Desktop App Testing:
```bash
# Build everything first
cd /app/tradeyoda
./build_backend.sh

cd /app/tradeyoda/frontend
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env.production
yarn build

# Copy frontend
cp -r dist /app/tradeyoda-desktop/build

# Test desktop app
cd /app/tradeyoda-desktop
npm start
```

---

## What Should Happen (Success Flow)

### First Run:
1. Electron window opens (600x450)
2. Purple gradient background with license form
3. Enter license key
4. Click "Activate License"
5. Shows "Validating..."
6. On success: "License activated successfully!"
7. License window closes
8. Main app window opens (1280x800)
9. React frontend loads
10. Trading dashboard appears

### Subsequent Runs:
1. Electron window opens
2. Backend spawns in background
3. Main app window appears directly (no license prompt)
4. React frontend loads
5. Ready to use

---

## Development Tips

### Enable DevTools:
In `electron/main.js`, DevTools are auto-opened in dev mode:
```javascript
if (isDev) {
  mainWindow.webContents.openDevTools();
}
```

### Check Logs:
- **Electron console:** Cmd+Option+I (Mac) or Ctrl+Shift+I (Windows/Linux)
- **Backend logs:** Check terminal where backend is running
- **Desktop mode logs:** `~/Library/Application Support/TradeYoda/logs/` (Mac)

### Kill Processes:
If backend doesn't stop:
```bash
# Find and kill
ps aux | grep tradeyoda
kill <PID>

# Or kill all Python processes
pkill -f tradeyoda
```

---

## Next Steps

After testing works:
1. Build installers: `npm run build:win` or `npm run build:mac`
2. Test installer on clean machine
3. Distribute to users

See `DESKTOP_PACKAGING_GUIDE.md` for Phase 4 details.
