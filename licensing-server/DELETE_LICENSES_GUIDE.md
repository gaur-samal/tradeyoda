# Delete Licenses Feature Guide

## Overview

Added functionality to delete test/unwanted licenses from the admin panel.

## Features Added

### 1. **Single License Delete**
- Delete button in the Actions column for each license
- Confirmation popup before deletion
- Permanently removes license and all validation logs

### 2. **Bulk Delete**
- Select multiple licenses using checkboxes
- "Delete Selected (X)" button appears when licenses are selected
- Delete all selected licenses at once

### 3. **API Endpoints**

**Delete Single License:**
```bash
DELETE /api/admin/licenses/{license_key}
```

**Bulk Delete:**
```bash
POST /api/admin/licenses/bulk-delete
Body: { "license_keys": ["TYODA-XXXX-...", "TYODA-YYYY-..."] }
```

## How to Use

### Via Admin Panel UI:

#### **Delete Single License:**
1. Go to `http://YOUR_IP:8100/admin/licenses`
2. Find the license you want to delete
3. Click "Delete" button in the Actions column
4. Confirm deletion in the popup
5. License is permanently deleted

#### **Bulk Delete Multiple Licenses:**
1. Go to `http://YOUR_IP:8100/admin/licenses`
2. Check the boxes next to licenses you want to delete
3. Click "Delete Selected (X)" button at the top
4. Confirm deletion in the popup
5. All selected licenses are deleted

#### **Select All/None:**
1. Use the checkbox in the table header to select all
2. Use "Select Invert" to invert selection
3. Use "Select None" to deselect all

### Via API (curl):

#### **Delete Single License:**
```bash
curl -X DELETE http://localhost:8100/api/admin/licenses/TYODA-XXXX-XXXX-XXXX-XXXX
```

Response:
```json
{
  "success": true,
  "message": "License TYODA-XXXX-XXXX-XXXX-XXXX deleted successfully"
}
```

#### **Bulk Delete:**
```bash
curl -X POST http://localhost:8100/api/admin/licenses/bulk-delete \
  -H "Content-Type: application/json" \
  -d '{
    "license_keys": [
      "TYODA-AAAA-BBBB-CCCC-DDDD",
      "TYODA-1111-2222-3333-4444",
      "TYODA-XXXX-YYYY-ZZZZ-WWWW"
    ]
  }'
```

Response:
```json
{
  "success": true,
  "deleted_count": 3,
  "message": "Deleted 3 license(s)"
}
```

## What Gets Deleted

When you delete a license:
1. ✅ License record from database
2. ✅ All validation logs for that license
3. ✅ Cached validation on user's machine (on next validation attempt)

## Warning

⚠️ **PERMANENT ACTION** - Deleted licenses CANNOT be recovered!

- The license key becomes invalid immediately
- Users with deleted licenses will be unable to validate
- All usage history is removed

## Safety Features

1. **Confirmation Popups** - Must confirm before deletion
2. **Clear Warnings** - "This action cannot be undone!"
3. **Separate from Revoke** - Revoke = soft delete, Delete = hard delete

## Revoke vs Delete

| Feature | Revoke | Delete |
|---------|--------|--------|
| License Status | Status = REVOKED | Completely removed |
| Can Undo | Can reactivate | Cannot undo |
| Validation History | Kept | Deleted |
| Use Case | Temporary suspension | Remove test licenses |

## Deployment Steps

### 1. Update Backend
```bash
cd /home/ubuntu/licensing-server

# Restart service
sudo systemctl restart tradeyoda-licensing
```

### 2. Rebuild Admin Panel
```bash
cd /home/ubuntu/licensing-server/admin-panel

# Rebuild
npm run build

# Or if already built, just refresh browser
```

### 3. Test
```bash
# Health check
curl http://localhost:8100/health

# Try deleting a test license via API
curl -X DELETE http://localhost:8100/api/admin/licenses/YOUR_TEST_LICENSE_KEY
```

## Use Cases

### **Scenario 1: Clean Up Test Licenses**
You created many test licenses during development:
1. Go to admin panel
2. Select all test licenses (use checkboxes)
3. Click "Delete Selected"
4. Confirm deletion
5. Dashboard now shows accurate counts

### **Scenario 2: Remove Invalid License**
A license was created with wrong tier/email:
1. Find the license in the table
2. Click "Delete" button
3. Confirm deletion
4. Create a new correct license

### **Scenario 3: Delete All TRIAL Licenses**
Remove all expired trial licenses:
1. Use the "Tier" filter to show only TRIAL
2. Select all filtered results
3. Click "Delete Selected"
4. Confirm deletion

## Statistics Impact

After deletion:
- Dashboard counts update immediately
- Total licenses count decreases
- Tier distribution chart updates
- Validation logs removed

## Troubleshooting

### **Error: "License not found"**
- License was already deleted
- Check the license key is correct

### **Error: "Failed to delete licenses"**
- Check database connection
- Check logs: `sudo journalctl -u tradeyoda-licensing -n 50`

### **Delete button not showing**
- Rebuild admin panel
- Clear browser cache
- Check console for errors (F12)

## Security Note

In production:
- Add authentication to admin endpoints
- Restrict delete access to super admins only
- Log all delete operations for audit
- Consider soft delete instead of hard delete

## Example Workflow

Clean up after testing:

```bash
# 1. View all licenses
curl http://localhost:8100/api/admin/licenses | jq '.licenses[] | {key: .license_key, tier: .tier, email: .user_email}'

# 2. Delete test licenses
curl -X POST http://localhost:8100/api/admin/licenses/bulk-delete \
  -H "Content-Type: application/json" \
  -d '{
    "license_keys": [
      "TYODA-TEST-1111-2222-3333",
      "TYODA-TEST-4444-5555-6666"
    ]
  }'

# 3. Verify deletion
curl http://localhost:8100/api/admin/stats | jq
```

## FAQ

**Q: Can I recover a deleted license?**
A: No, deletion is permanent. Use "Revoke" if you might need to reactivate later.

**Q: What happens to users with deleted licenses?**
A: They'll get "License not found" error and need to activate a new license.

**Q: Can I delete ACTIVE licenses?**
A: Yes, but this will immediately invalidate them for users.

**Q: Is there a delete limit?**
A: No limit, but bulk operations may take time for large numbers.

**Q: Will this affect backups?**
A: Deleted licenses won't appear in future backups. Restore old backup to recover.
