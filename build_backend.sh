#!/bin/bash
# Build script for TradeYoda Backend
# Packages backend into standalone executable using PyInstaller

set -e  # Exit on error

echo "======================================"
echo "TradeYoda Backend - Build Script"
echo "======================================"
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ __pycache__/

# Build backend executable
echo ""
echo "🔨 Building backend executable..."
echo ""

pyinstaller tradeyoda-backend.spec --clean

# Check if build succeeded
if [ -d "dist/tradeyoda-backend" ]; then
    echo ""
    echo "✅ Backend build successful!"
    echo ""
    echo "📦 Output directory: dist/tradeyoda-backend/"
    echo "🚀 Executable: dist/tradeyoda-backend/tradeyoda-backend"
    echo ""
    echo "To test the backend:"
    echo "  cd dist/tradeyoda-backend"
    echo "  ./tradeyoda-backend"
    echo ""
else
    echo ""
    echo "❌ Build failed! Check errors above."
    exit 1
fi

