#!/bin/bash

# Sora Watermark Remover - Remove Auto-Start

PLIST_NAME="com.local.sora-watermark-remover"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "🎬 Removing Sora Watermark Remover auto-start..."

# Unload and remove the service
launchctl unload "$PLIST_PATH" 2>/dev/null
rm -f "$PLIST_PATH"

echo "✅ Auto-start removed. The app will no longer run automatically."
echo "   You can still run it manually with: ./start.sh"

