# Sora Watermark Remover - Local Edition

A 100% free, local bulk manual watermark removal tool. No accounts, no uploads to servers, completely private.

## Features

- 🎬 **Bulk Processing** - Handle multiple videos at once
- 🎯 **Manual Selection** - Draw rectangles to select watermark areas
- 📋 **Apply to All** - Use the same mask across all videos
- 🔄 **Random Renaming** - Auto-generates natural filenames to avoid AI detection
- 📱 **Phone Access** - Access from your phone via local network
- 🔒 **100% Local** - Nothing leaves your computer

## Quick Start

### Option 1: Double-Click App (Easiest)
Double-click **"Sora WM Remover.app"** in the folder - it will start the server and open your browser automatically!

### Option 2: Always Running (Recommended)
Run this once to make the app always available in the background:
```bash
cd "/Users/alexandercarver/Documents/Sora Watermark Remover"
./install-autostart.sh
```

The app will now:
- Start automatically when you log in
- Restart automatically if it crashes
- Always be available at http://localhost:5001

### Option 3: Manual Start
```bash
cd "/Users/alexandercarver/Documents/Sora Watermark Remover"
./start.sh
```

## Accessing the App

Once running, you'll see:

```
🎬 SORA WATERMARK REMOVER - LOCAL EDITION
============================================================

📱 Access from your LAPTOP:  http://localhost:5001
📱 Access from your PHONE:   http://192.168.x.x:5001

💡 Make sure your phone is on the same WiFi network!
```

**On your laptop:** Open http://localhost:5001 in your browser

**On your phone:** 
1. Make sure your phone is on the same WiFi as your laptop
2. Open the IP address shown (e.g., http://192.168.0.53:5001)

## How to Use

1. **Upload Videos**
   - Drag & drop or click to upload multiple videos
   - Supports MP4, MOV, M4V, AVI, MKV, WebM

2. **Find the Watermark**
   - Click on a video in the queue to load it
   - **Use the video player** to scrub through and find where the watermark appears
   - Click **"📸 Capture This Frame"** to freeze on that frame

3. **Select Watermark Areas**
   - Draw rectangles around the Sora watermark on the captured frame
   - The watermark is usually in the bottom-right corner
   - You can draw multiple rectangles if needed

4. **Apply to All (Optional)**
   - If all videos have the watermark in the same spot, click "Apply to All"

5. **Process**
   - Enter a custom filename or leave blank for random name
   - Choose inpainting method (Telea is faster, NS is better for edges)
   - Click "Remove Watermark" for single video or "Process All" for batch

6. **Download**
   - Processed videos appear in the "Processed Videos" section
   - Click Download to save each video

## Output Location

Processed videos are saved to:
```
/Users/alexandercarver/Documents/Sora Watermark Remover/processed/
```

## Tips for Best Results

- **Sora watermark location**: Usually bottom-right corner with "Sora" text
- **Draw slightly larger**: Include a small margin around the watermark
- **Use Telea** for faster processing on solid backgrounds
- **Use Navier-Stokes** for better results on complex textures

## Optional: Install FFmpeg for Better Quality

For better video quality and compatibility:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows - Download from https://ffmpeg.org/download.html
```

## Managing the Background Service

If you installed auto-start, here's how to manage it:

```bash
# Stop the service
launchctl unload ~/Library/LaunchAgents/com.local.sora-watermark-remover.plist

# Start the service  
launchctl load ~/Library/LaunchAgents/com.local.sora-watermark-remover.plist

# View logs
tail -f "/Users/alexandercarver/Documents/Sora Watermark Remover/logs/output.log"

# Completely remove auto-start
./uninstall-autostart.sh
```

## Troubleshooting

**Port already in use:**
```bash
# Kill existing process on port 5001
lsof -ti:5001 | xargs kill -9
```

**Can't access from phone:**
1. Check both devices are on the same WiFi network
2. Check your firewall settings
3. Try the alternative IP shown in terminal

## License

This tool is for personal use only. Always respect content ownership and platform terms of service.

