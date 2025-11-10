# Pre-Build Checklist for Electron Desktop App

Before running `npm run build`, ensure these are complete:

## ✅ Fixed Issues
- [x] Moved `electron` to `devDependencies` (was causing build error)

## Required Steps Before Building

### 1. Build Backend (Phase 1)
```bash
cd /app/tradeyoda
./build_backend.sh
```

**Verify:**
```bash
ls -la /app/tradeyoda/dist/tradeyoda-backend/
# Should show: tradeyoda-backend executable and _internal/ directory
```

**Status:** ❌ Not done yet

---

### 2. Build Frontend (Phase 3)
```bash
cd /app/tradeyoda/frontend

# Create production environment file
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env.production

# Build
yarn build
```

**Verify:**
```bash
ls -la /app/tradeyoda/frontend/dist/
# Should show: index.html, assets/, etc.
```

**Copy to Electron project:**
```bash
mkdir -p /app/tradeyoda-desktop/build
cp -r /app/tradeyoda/frontend/dist/* /app/tradeyoda-desktop/build/
```

**Status:** ❌ Not done yet

---

### 3. Create App Icons (Optional but Recommended)

**Quick Placeholder Icons:**
```bash
cd /app/tradeyoda-desktop/assets

# Create 512x512 placeholder PNG (for Linux)
convert -size 512x512 xc:purple -pointsize 100 -fill white \
  -gravity center -annotate +0+0 "TY" icon.png

# For Windows .ico (if convert/ImageMagick available)
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico

# For Mac .icns (requires iconutil on Mac)
# Manual: Use online converter or Mac iconutil
```

**Or download a free icon:**
```bash
# Use a temporary icon from a free icon site
# Examples: flaticon.com, icons8.com
```

**Status:** ⚠️ Optional (build will warn but succeed)

---

## Build Commands

### After completing steps 1-3 above:

**Test build (current platform only):**
```bash
cd /app/tradeyoda-desktop
npm run build
```

**Build for specific platform:**
```bash
npm run build:win   # Windows
npm run build:mac   # macOS
npm run build:linux # Linux
```

**Output location:**
```
tradeyoda-desktop/release/
├── TradeYoda Setup 1.0.0.exe    # Windows
├── TradeYoda-1.0.0.dmg          # Mac
└── TradeYoda-1.0.0.AppImage     # Linux
```

---

## Current Status Summary

| Step | Status | Action |
|------|--------|--------|
| 1. Backend built | ❌ | Run `./build_backend.sh` |
| 2. Frontend built | ❌ | Run `yarn build` in frontend/ |
| 3. Frontend copied | ❌ | Copy dist/ to tradeyoda-desktop/build/ |
| 4. Icons created | ⚠️ | Optional but recommended |
| 5. Dependencies correct | ✅ | Fixed in package.json |

---

## Quick Setup Script

Create this script to automate preparation:

```bash
#!/bin/bash
# File: /app/tradeyoda-desktop/prepare-build.sh

set -e

echo "========================================"
echo "TradeYoda Desktop - Build Preparation"
echo "========================================"
echo ""

# Step 1: Build backend
echo "📦 Step 1: Building backend..."
cd /app/tradeyoda
if [ -f "./build_backend.sh" ]; then
    ./build_backend.sh
else
    echo "⚠️  build_backend.sh not found, skipping..."
fi

# Step 2: Build frontend
echo ""
echo "📦 Step 2: Building frontend..."
cd /app/tradeyoda/frontend

# Create production env
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env.production

# Build
yarn build

# Step 3: Copy frontend to Electron
echo ""
echo "📦 Step 3: Copying frontend to Electron..."
mkdir -p /app/tradeyoda-desktop/build
cp -r dist/* /app/tradeyoda-desktop/build/

echo ""
echo "✅ Preparation complete!"
echo ""
echo "Next steps:"
echo "  cd /app/tradeyoda-desktop"
echo "  npm run build"
echo ""
```

Make it executable:
```bash
chmod +x /app/tradeyoda-desktop/prepare-build.sh
```

Run it:
```bash
/app/tradeyoda-desktop/prepare-build.sh
```

---

## Testing Before Building Installer

Before creating the installer, test the app in development mode:

```bash
cd /app/tradeyoda-desktop
npm start
```

**What should happen:**
1. Electron window opens
2. Backend spawns (Python process)
3. License prompt appears (first run)
4. Enter license key
5. Main app loads

**If this works, you're ready to build the installer!**

---

## Common Build Errors

### Error: "Application entry file not found"
**Cause:** Frontend build not copied
**Fix:** Run step 2 and 3 above

### Error: "Cannot find backend executable"
**Cause:** Backend not built
**Fix:** Run step 1 above

### Error: "Icon file not found"
**Cause:** Missing icon files
**Fix:** Either create placeholder icons or remove icon references from package.json

### Error: "ENOENT: no such file or directory"
**Cause:** One of the required paths doesn't exist
**Fix:** Check all paths in package.json "extraResources"

---

## Alternative: Test Without Building

If you just want to test functionality without creating an installer:

```bash
# Start backend manually
cd /app/tradeyoda
export TRADEYODA_DESKTOP_MODE=true
python3 backend_entrypoint.py &

# Start frontend dev server
cd /app/tradeyoda/frontend
yarn dev &

# Start Electron (will connect to dev servers)
cd /app/tradeyoda-desktop
npm start
```

This is faster for testing but doesn't create a distributable installer.

---

## Ready to Build?

**Checklist:**
- [ ] Backend built and exists at `/app/tradeyoda/dist/tradeyoda-backend/`
- [ ] Frontend built and copied to `/app/tradeyoda-desktop/build/`
- [ ] Icons created (or willing to accept warnings)
- [ ] package.json dependencies correct (electron in devDependencies)
- [ ] Tested with `npm start` and it works

**If all checked, run:**
```bash
cd /app/tradeyoda-desktop
npm run build
```

**Build time:** ~2-5 minutes depending on platform and machine speed

**Output size:** ~150-200 MB for Windows, ~180-220 MB for Mac
