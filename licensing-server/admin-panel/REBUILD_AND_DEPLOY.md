# Rebuild and Deploy Admin Panel

## Changes Made
- Added "Never Expires" checkbox to Create License form
- Updated PRO tier model from gpt-5 to gpt-4.1

## Steps to Deploy

### 1. On Your Local Machine

```bash
cd /path/to/licensing-server/admin-panel

# Install dependencies (if needed)
npm install

# Build the production bundle
npm run build

# Output will be in: build/
```

### 2. Copy Build to EC2

**Option A: Using SCP**
```bash
# From your local machine
cd licensing-server/admin-panel
scp -r build/* ubuntu@<EC2_IP>:/home/ubuntu/apps/licensing-server/admin-panel/build/
```

**Option B: Using RSYNC (recommended - faster)**
```bash
# From your local machine
cd licensing-server/admin-panel
rsync -avz --delete build/ ubuntu@<EC2_IP>:/home/ubuntu/apps/licensing-server/admin-panel/build/
```

**Option C: Manual (if SSH access)**
```bash
# On EC2
cd /home/ubuntu/apps/licensing-server/admin-panel
rm -rf build/*

# Then copy files via SFTP or your preferred method
```

### 3. Restart Licensing Server on EC2

```bash
# SSH to EC2
ssh ubuntu@<EC2_IP>

# Restart the service
sudo systemctl restart tradeyoda-licensing

# Or if using supervisor
sudo supervisorctl restart licensing-server

# Check status
sudo systemctl status tradeyoda-licensing
# or
sudo supervisorctl status licensing-server

# Check logs
sudo journalctl -u tradeyoda-licensing -f
# or
tail -f /var/log/supervisor/licensing-server*.log
```

### 4. Clear Browser Cache

**Important!** After deploying, clear browser cache or do hard refresh:

- **Chrome/Edge:** Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- **Firefox:** Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
- **Safari:** Cmd+Option+R (Mac)

Or open in **Incognito/Private** mode to bypass cache.

### 5. Verify Changes

1. Open admin panel: `http://<EC2_IP>:8100/admin`
2. Go to "Licenses" tab
3. Click "Create License" button
4. You should now see:
   - ✅ "Never Expires (Lifetime License)" checkbox
   - ✅ PRO tier dropdown option

## Troubleshooting

### Checkbox Still Not Showing

**Check 1: Files were copied correctly**
```bash
# On EC2
ls -la /home/ubuntu/apps/licensing-server/admin-panel/build/
# Should show recently modified files with today's timestamp
```

**Check 2: Service is serving the correct files**
```bash
# Check licensing server config
cat /home/ubuntu/apps/licensing-server/server.py | grep "static_files"

# Verify it's mounting /admin-panel/build
```

**Check 3: Clear ALL cache**
```bash
# On browser
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
```

**Check 4: Verify build contains changes**
```bash
# On your local machine, after npm run build
grep -r "Never Expires" build/
# Should return matches in the JS bundle
```

### Service Won't Restart

```bash
# Check what's wrong
sudo systemctl status tradeyoda-licensing

# Check logs for errors
sudo journalctl -u tradeyoda-licensing -n 50

# Check if port 8100 is in use
sudo lsof -i :8100
```

### Changes in Code But Not in Browser

This is **always** a caching issue:
1. Hard refresh (Ctrl+Shift+R)
2. Open in Incognito mode
3. Clear browser cache completely
4. Check browser DevTools → Network tab → Disable cache

## File Locations

**Local (Development):**
- Source: `licensing-server/admin-panel/src/pages/Licenses.js`
- Build output: `licensing-server/admin-panel/build/`

**EC2 (Production):**
- Build files: `/home/ubuntu/apps/licensing-server/admin-panel/build/`
- Server script: `/home/ubuntu/apps/licensing-server/server.py`
- Service config: `/etc/systemd/system/tradeyoda-licensing.service`

## Quick Deploy Script

Create this on your local machine:

```bash
#!/bin/bash
# File: deploy-admin.sh

echo "Building admin panel..."
cd licensing-server/admin-panel
npm run build

echo "Copying to EC2..."
rsync -avz --delete build/ ubuntu@YOUR_EC2_IP:/home/ubuntu/apps/licensing-server/admin-panel/build/

echo "Restarting service..."
ssh ubuntu@YOUR_EC2_IP "sudo systemctl restart tradeyoda-licensing"

echo "✅ Deploy complete! Don't forget to hard refresh your browser."
```

Make it executable:
```bash
chmod +x deploy-admin.sh
```

Usage:
```bash
./deploy-admin.sh
```

## Verification Checklist

After deployment:
- [ ] Files copied to EC2 with today's timestamp
- [ ] Licensing service restarted successfully
- [ ] Service is running (`systemctl status` shows active)
- [ ] Port 8100 is accessible
- [ ] Browser cache cleared (hard refresh)
- [ ] Admin panel loads without errors (check browser console)
- [ ] "Create License" modal shows "Never Expires" checkbox
- [ ] PRO tier shows gpt-4.1 in tier info

## Common Mistakes

1. ❌ Forgetting to run `npm run build` before copying
2. ❌ Copying source files instead of build output
3. ❌ Not restarting the service after copying files
4. ❌ Browser cache not cleared (most common!)
5. ❌ Wrong destination path on EC2
6. ❌ File permissions issues (use sudo if needed)

## Need Help?

Check these logs:
```bash
# Licensing server logs
sudo journalctl -u tradeyoda-licensing -f

# Nginx logs (if using reverse proxy)
sudo tail -f /var/log/nginx/error.log

# Browser console (F12 → Console tab)
```
