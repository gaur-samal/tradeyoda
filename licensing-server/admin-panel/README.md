# TradeYoda Licensing Admin Panel

Professional React-based admin panel for managing TradeYoda licenses, OpenAI keys, and scrip master files.

## Features

- 📊 **Dashboard**: Overview with statistics and charts
- 📋 **License Management**: Create, view, search, filter, and revoke licenses
- 🔑 **OpenAI Keys**: Manage encrypted API keys for each tier
- 📄 **Scrip Master**: Upload and manage security master CSV files
- 🔍 **Search & Filter**: Advanced table filtering and search
- 📊 **Statistics**: Real-time licensing statistics
- 📊 **Validation History**: Track license validation attempts

## Tech Stack

- **React 18** - Modern UI framework
- **Ant Design 5** - Professional UI components
- **Ant Design Charts** - Data visualization
- **Axios** - API communication
- **React Router** - Navigation

## Installation

```bash
cd admin-panel
yarn install
```

## Development

1. Start the licensing server (if not already running):
```bash
cd ..
python server.py
```

2. Start the admin panel:
```bash
cd admin-panel
yarn start
```

Admin panel will open at `http://localhost:3000`

## Production Build

```bash
yarn build
```

This creates an optimized production build in the `build/` directory.

### Serving Production Build

The licensing server automatically serves the admin panel at `/admin` when build files are present.

1. Build the admin panel:
```bash
cd admin-panel
yarn build
```

2. Files are built to `admin-panel/build/`

3. Access admin panel at: `http://your-server:8100/admin`

## Configuration

Edit `.env` file:

```bash
REACT_APP_API_URL=http://localhost:8100
```

For production, set to your server URL:
```bash
REACT_APP_API_URL=http://your-ec2-ip:8100
```

## Usage Guide

### Dashboard
- View total licenses, active, expired, and revoked counts
- See validations per day
- View tier distribution chart
- Quick access to recent licenses

### License Management
- **Create**: Click "Create License" button
  - Select tier (TRIAL, BASIC, ADVANCED, PRO)
  - Enter user email and name (optional)
  - Add notes (optional)
- **Search**: Use search bar to filter by license key, email, or name
- **Filter**: Use column filters to filter by tier or status
- **View Details**: Click "Details" to see full license info and validation history
- **Revoke**: Click "Revoke" to deactivate a license
- **Copy**: Click copy icon to copy license key to clipboard

### OpenAI Keys
- **Add/Update**: Click "Add/Update Key"
  - Select tier
  - Enter OpenAI API key (starts with `sk-`)
  - Select model
- Keys are encrypted in database
- One key per tier (updating replaces existing)

### Scrip Master
- Download latest CSV from Dhan
- Enter version identifier (e.g., "2024-11")
- Select CSV file
- Click "Upload"
- Desktop apps will auto-download updates

## API Integration

The admin panel communicates with the licensing server API:

- `GET /api/admin/stats` - Statistics
- `GET /api/admin/licenses` - List licenses
- `POST /api/licenses/create` - Create license
- `GET /api/admin/licenses/{key}` - License details
- `POST /api/admin/licenses/{key}/revoke` - Revoke license
- `GET /api/admin/openai-keys` - List OpenAI keys
- `POST /api/admin/openai-keys` - Add/update key
- `POST /api/admin/scrip-master/upload` - Upload CSV
- `GET /api/scrip-master/version` - Current version

## Troubleshooting

### Cannot connect to API
- Check if licensing server is running: `python server.py`
- Verify API URL in `.env` matches server address
- Check browser console for errors

### Build fails
```bash
rm -rf node_modules yarn.lock
yarn install
yarn build
```

### Port already in use
Edit `package.json` and change port:
```json
"start": "PORT=3001 react-scripts start"
```

## Security Considerations

### Production Deployment

1. **Add Authentication**:
   - Implement login system
   - Use JWT tokens
   - Protect admin routes

2. **Use HTTPS**:
   - Configure SSL certificate
   - Update API URL to https://

3. **Restrict Access**:
   - IP whitelist
   - VPN requirement
   - Admin-only access

4. **Environment Variables**:
   - Don't commit `.env` with production URLs
   - Use environment-specific configs

## Future Enhancements

- [ ] User authentication system
- [ ] Role-based access control
- [ ] Email notifications for license events
- [ ] Bulk license operations
- [ ] Export license data (CSV, JSON)
- [ ] Advanced analytics and reporting
- [ ] License usage graphs
- [ ] Audit log

## Support

For issues or questions, contact: gaur.samal@gmail.com
