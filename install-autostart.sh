#!/bin/bash

# Sora Watermark Remover - Auto-Start Installer for macOS
# This script sets up the app to run automatically in the background

APP_DIR="/Users/alexandercarver/Documents/Sora Watermark Remover"
PLIST_NAME="com.local.sora-watermark-remover"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "🎬 Sora Watermark Remover - Auto-Start Setup"
echo "============================================="
echo ""

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create the plist file
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${APP_DIR}/venv/bin/python</string>
        <string>${APP_DIR}/app.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${APP_DIR}</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>${APP_DIR}/logs/output.log</string>
    
    <key>StandardErrorPath</key>
    <string>${APP_DIR}/logs/error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

# Create logs directory
mkdir -p "$APP_DIR/logs"

# Load the service
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo "✅ Auto-start installed successfully!"
echo ""
echo "The app will now:"
echo "  • Start automatically when you log in"
echo "  • Restart automatically if it crashes"
echo "  • Run in the background"
echo ""
echo "📱 Access it anytime at: http://localhost:5001"
echo "📱 Or on your phone at:  http://$(ipconfig getifaddr en0 2>/dev/null || echo "YOUR_IP"):5001"
echo ""
echo "To manage the service:"
echo "  Stop:    launchctl unload $PLIST_PATH"
echo "  Start:   launchctl load $PLIST_PATH"
echo "  Logs:    tail -f $APP_DIR/logs/output.log"
echo ""

