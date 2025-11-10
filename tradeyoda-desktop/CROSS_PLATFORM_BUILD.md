# Cross-Platform Building Guide

## Current Situation

You're building on **Linux (EC2)**, which can only natively create Linux packages.

### What You Can Build

| Your Platform | Can Build | Difficulty |
|---------------|-----------|------------|
| Linux (EC2) | `.AppImage` | ✅ Easy (native) |
| Linux (EC2) | `.exe` (Windows) | ⚠️ Possible (needs wine + setup) |
| Linux (EC2) | `.dmg` (Mac) | ❌ Impossible (Apple restriction) |

---

## Option 1: Build on Native Platforms (Recommended)

### Windows Build (on Windows machine)

**Prerequisites:**
- Windows 10/11
- Node.js installed
- Git installed

**Steps:**
```bash
# Clone repo
git clone <your-repo-url>
cd tradeyoda-desktop

# Install dependencies
npm install

# Build Windows installer
npm run build:win

# Output: release/TradeYoda Setup 1.0.0.exe
```

---

### Mac Build (on macOS machine)

**Prerequisites:**
- macOS 10.13 or later
- Node.js installed
- Git installed
- Xcode Command Line Tools: `xcode-select --install`

**Steps:**
```bash
# Clone repo
git clone <your-repo-url>
cd tradeyoda-desktop

# Install dependencies
npm install

# Build Mac installer
npm run build:mac

# Output: release/TradeYoda-1.0.0.dmg
```

---

### Linux Build (on EC2 - already working)

```bash
# On EC2
cd /app/tradeyoda-desktop
npm run build:linux

# Output: release/TradeYoda-1.0.0.AppImage
```

---

## Option 2: Cross-Compile Windows on Linux (Advanced)

### Install Wine and Dependencies

```bash
# Install wine
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y wine64 wine32

# Install additional build tools
sudo apt install -y mono-devel

# Verify wine installation
wine --version
```

### Update package.json for Cross-Compilation

```json
{
  "build": {
    "win": {
      "target": ["nsis"],
      "icon": "assets/icon.ico"
    }
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-is-dev": "^2.0.0",
    "electron-builder": "^24.9.1",
    "wine": "^1.0.0"
  }
}
```

### Build Windows Installer

```bash
# On Linux
npm run build:win

# electron-builder will use wine to create .exe
```

**Issues you might face:**
- Wine can be unstable
- May fail with signing errors
- Slower than native build
- Complex troubleshooting

---

## Option 3: CI/CD Pipeline (Professional Solution)

Use GitHub Actions or similar CI/CD to build on multiple platforms:

### GitHub Actions Example

Create `.github/workflows/build.yml`:

```yaml
name: Build Desktop Apps

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npm run build:win
      - uses: actions/upload-artifact@v3
        with:
          name: windows-installer
          path: release/*.exe

  build-mac:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npm run build:mac
      - uses: actions/upload-artifact@v3
        with:
          name: mac-installer
          path: release/*.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npm run build:linux
      - uses: actions/upload-artifact@v3
        with:
          name: linux-installer
          path: release/*.AppImage
```

**Benefits:**
- Builds all platforms automatically
- Free for public repos
- Professional workflow
- Consistent builds

---

## Option 4: Cloud Build Services

### Electron Forge Cloud
- Paid service
- Builds on all platforms
- Handles code signing

### CircleCI / Travis CI
- Similar to GitHub Actions
- Supports multi-platform builds

---

## Recommended Workflow

### For Development/Testing
1. Build Linux on EC2
2. Test locally on your development machine

### For Production Release
Choose based on your needs:

**Small Project:**
- Build manually on each platform
- Share installers via download links

**Medium Project:**
- Use GitHub Actions for automated builds
- Release via GitHub Releases

**Large Project:**
- Professional CI/CD pipeline
- Automated testing + building
- Code signing certificates
- Auto-update server

---

## Why Mac Build is Special

**Apple Requirements:**
1. Must build on macOS hardware
2. Requires Apple Developer account ($99/year) for signing
3. Must be notarized for Gatekeeper (macOS security)
4. Cannot cross-compile from Linux/Windows

**Workarounds:**
- Rent macOS VM (MacStadium, AWS EC2 Mac)
- Use GitHub Actions (free macOS runners)
- Find someone with a Mac to build

---

## Testing Without Building Installers

If you just need to test functionality:

```bash
# Start backend manually
cd /app/tradeyoda
python3 backend_entrypoint.py &

# Start frontend dev server  
cd /app/tradeyoda/frontend
yarn dev &

# Test backend API
curl http://localhost:8000/health
```

This doesn't require Electron or GUI, just tests the backend logic.

---

## Summary

### What Works Now
✅ Build Linux `.AppImage` on EC2

### What You Need
❌ Windows `.exe` → Need Windows machine or wine setup
❌ Mac `.dmg` → MUST have macOS machine

### Recommendation
1. **For testing:** Use the Linux `.AppImage` on your local Linux machine
2. **For Windows:** Build on a Windows machine later
3. **For Mac:** Use GitHub Actions or borrow a Mac

### Quick Win
The Linux `.AppImage` you have works! Test it on a Linux desktop to verify everything works, then worry about Windows/Mac builds.

---

## Current Build Status

```
EC2 Linux Build:
  ✅ Backend packaged
  ✅ Frontend built  
  ✅ .AppImage created
  ❌ Cannot test (headless server)

Next Steps:
  1. Download .AppImage to local Linux machine
  2. Make executable: chmod +x TradeYoda-1.0.0.AppImage
  3. Run: ./TradeYoda-1.0.0.AppImage
  4. Test functionality
  5. Plan Windows/Mac builds after Linux works
```
