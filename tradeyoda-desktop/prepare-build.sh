#!/bin/bash
# Prepare TradeYoda Desktop for building installers

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
    echo "✅ Backend built successfully"
else
    echo "⚠️  build_backend.sh not found"
    exit 1
fi

# Check backend output
if [ ! -f "/app/tradeyoda/dist/tradeyoda-backend/tradeyoda-backend" ]; then
    echo "❌ Backend executable not found after build"
    exit 1
fi

# Step 2: Build frontend
echo ""
echo "📦 Step 2: Building frontend..."
cd /app/tradeyoda/frontend

# Create production env
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env.production

# Build
yarn build
echo "✅ Frontend built successfully"

# Check frontend output
if [ ! -f "/app/tradeyoda/frontend/dist/index.html" ]; then
    echo "❌ Frontend build not found"
    exit 1
fi

# Step 3: Copy frontend to Electron
echo ""
echo "📦 Step 3: Copying frontend to Electron..."
mkdir -p /app/tradeyoda-desktop/build
cp -r /app/tradeyoda/frontend/dist/* /app/tradeyoda-desktop/build/
echo "✅ Frontend copied to Electron project"

# Step 4: Create placeholder icon if missing
echo ""
echo "📦 Step 4: Checking for icons..."
cd /app/tradeyoda-desktop/assets

if [ ! -f "icon.png" ]; then
    echo "⚠️  Icon not found, creating placeholder..."
    # Create a simple placeholder (requires ImageMagick)
    if command -v convert &> /dev/null; then
        convert -size 512x512 xc:purple -pointsize 120 -fill white \
          -gravity center -annotate +0+0 "TY" icon.png
        echo "✅ Placeholder icon created"
    else
        echo "⚠️  ImageMagick not found, skipping icon creation"
        echo "   Build will warn but should succeed"
    fi
else
    echo "✅ Icon found"
fi

echo ""
echo "========================================"
echo "✅ Preparation complete!"
echo "========================================"
echo ""
echo "Files ready:"
echo "  Backend:  /app/tradeyoda/dist/tradeyoda-backend/"
echo "  Frontend: /app/tradeyoda-desktop/build/"
echo ""
echo "Next steps:"
echo "  cd /app/tradeyoda-desktop"
echo "  npm run build          # Build for current platform"
echo "  npm run build:win      # Build for Windows"
echo "  npm run build:mac      # Build for Mac"
echo ""
echo "Output will be in: /app/tradeyoda-desktop/release/"
echo ""
