#!/bin/bash
cd /home/ubuntu/apps/tradeyoda

# Update frontend
cd frontend
npm install
npm run build
sudo systemctl restart nginx

echo "✅ Updated!"
