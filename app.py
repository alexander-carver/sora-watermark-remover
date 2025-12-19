#!/usr/bin/env python3
"""
Sora Watermark Remover - Local Bulk Manual Tool
A simple, free, local tool to manually remove watermarks from videos.
"""

import os
import uuid
import random
import string
import json
import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import cv2
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
PROCESSED_FOLDER = BASE_DIR / 'processed'
FRAMES_FOLDER = BASE_DIR / 'frames'
ALLOWED_EXTENSIONS = {'mp4', 'm4v', 'mov', 'avi', 'mkv', 'webm'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB max

# Create directories
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, FRAMES_FOLDER]:
    folder.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Store processing jobs
jobs = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_random_name(length=12):
    """Generate a random filename that doesn't look AI-generated."""
    prefixes = ['VID', 'MOV', 'clip', 'video', 'recording', 'footage', 'shot', 'take']
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    style = random.choice(['timestamp', 'random', 'prefix'])
    
    if style == 'timestamp':
        return f"{timestamp}_{random_part[:6]}"
    elif style == 'prefix':
        return f"{random.choice(prefixes)}_{random_part}"
    else:
        return random_part


def extract_preview_frame(video_path, frame_number=0):
    """Extract a single frame from video for preview."""
    cap = cv2.VideoCapture(str(video_path))
    
    if frame_number > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        return frame
    return None


def apply_inpainting(frame, mask, method='telea'):
    """Apply inpainting to remove watermark from a frame."""
    if method == 'telea':
        return cv2.inpaint(frame, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    else:
        return cv2.inpaint(frame, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)


def process_video(video_path, mask_data, output_path, callback=None):
    """Process entire video with inpainting to remove watermarks.
    Each mask can have its own method (telea or ns)."""
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        raise Exception("Could not open video file")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Create separate masks for each method
    telea_mask = np.zeros((height, width), dtype=np.uint8)
    ns_mask = np.zeros((height, width), dtype=np.uint8)
    
    for rect in mask_data:
        x1 = int(rect['x'] * width)
        y1 = int(rect['y'] * height)
        x2 = int((rect['x'] + rect['width']) * width)
        y2 = int((rect['y'] + rect['height']) * height)
        
        # Add some padding
        padding = 3
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)
        
        # Add to appropriate mask based on method
        method = rect.get('method', 'telea')
        if method == 'ns':
            cv2.rectangle(ns_mask, (x1, y1), (x2, y2), 255, -1)
        else:
            cv2.rectangle(telea_mask, (x1, y1), (x2, y2), 255, -1)
    
    has_telea = np.any(telea_mask)
    has_ns = np.any(ns_mask)
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_output = str(output_path).replace('.mp4', '_temp.mp4')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        processed_frame = frame
        
        # Apply Telea inpainting first (faster)
        if has_telea:
            processed_frame = cv2.inpaint(processed_frame, telea_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
        
        # Apply Navier-Stokes inpainting (better quality for edges)
        if has_ns:
            processed_frame = cv2.inpaint(processed_frame, ns_mask, inpaintRadius=5, flags=cv2.INPAINT_NS)
        
        out.write(processed_frame)
        frame_count += 1
        
        if callback and frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            callback(progress)
    
    cap.release()
    out.release()
    
    # Re-encode with ffmpeg for better compatibility (if available)
    try:
        import subprocess
        # Check if ffmpeg is available
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            # Use ffmpeg to re-encode for better compatibility
            subprocess.run([
                'ffmpeg', '-y', '-i', temp_output,
                '-c:v', 'libx264', '-preset', 'medium',
                '-crf', '18', '-pix_fmt', 'yuv420p',
                str(output_path)
            ], capture_output=True)
            os.remove(temp_output)
        else:
            shutil.move(temp_output, str(output_path))
    except Exception:
        shutil.move(temp_output, str(output_path))
    
    return True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle video upload."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate unique ID for this job
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_path = UPLOAD_FOLDER / f"{job_id}_{filename}"
    file.save(str(upload_path))
    
    # Extract preview frame
    frame = extract_preview_frame(upload_path)
    if frame is None:
        os.remove(str(upload_path))
        return jsonify({'error': 'Could not read video file'}), 400
    
    # Save preview frame
    preview_path = FRAMES_FOLDER / f"{job_id}_preview.jpg"
    cv2.imwrite(str(preview_path), frame)
    
    # Get video info
    cap = cv2.VideoCapture(str(upload_path))
    info = {
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
    }
    cap.release()
    
    # Store job info
    jobs[job_id] = {
        'id': job_id,
        'original_name': filename,
        'upload_path': str(upload_path),
        'preview_path': str(preview_path),
        'status': 'uploaded',
        'progress': 0,
        'info': info
    }
    
    return jsonify({
        'job_id': job_id,
        'preview_url': f'/preview/{job_id}',
        'info': info
    })


@app.route('/preview/<job_id>')
def get_preview(job_id):
    """Get preview image for a job."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    preview_path = FRAMES_FOLDER / f"{job_id}_preview.jpg"
    return send_file(str(preview_path), mimetype='image/jpeg')


@app.route('/video/<job_id>')
def get_video(job_id):
    """Stream the uploaded video for playback."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    return send_file(job['upload_path'], mimetype='video/mp4')


@app.route('/process', methods=['POST'])
def process():
    """Process video with watermark removal."""
    data = request.json
    job_id = data.get('job_id')
    mask_data = data.get('masks', [])
    custom_name = data.get('custom_name', '')
    
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    if not mask_data:
        return jsonify({'error': 'No watermark areas selected'}), 400
    
    # Generate output filename
    if custom_name:
        output_name = custom_name
    else:
        output_name = generate_random_name()
    
    output_name = output_name.replace('.mp4', '') + '.mp4'
    output_path = PROCESSED_FOLDER / output_name
    
    job['status'] = 'processing'
    job['output_path'] = str(output_path)
    job['output_name'] = output_name
    
    def update_progress(progress):
        job['progress'] = progress
    
    try:
        process_video(
            job['upload_path'],
            mask_data,
            output_path,
            callback=update_progress
        )
        job['status'] = 'completed'
        job['progress'] = 100
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{job_id}',
            'filename': output_name
        })
        
    except Exception as e:
        job['status'] = 'error'
        job['error'] = str(e)
        return jsonify({'error': str(e)}), 500


@app.route('/progress/<job_id>')
def get_progress(job_id):
    """Get processing progress."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    return jsonify({
        'status': job['status'],
        'progress': job['progress']
    })


@app.route('/download/<job_id>')
def download(job_id):
    """Download processed video."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Video not ready'}), 400
    
    return send_file(
        job['output_path'],
        as_attachment=True,
        download_name=job['output_name']
    )


@app.route('/cleanup/<job_id>', methods=['POST'])
def cleanup(job_id):
    """Clean up job files."""
    if job_id in jobs:
        job = jobs[job_id]
        
        # Remove uploaded file
        if os.path.exists(job.get('upload_path', '')):
            os.remove(job['upload_path'])
        
        # Remove preview
        preview_path = FRAMES_FOLDER / f"{job_id}_preview.jpg"
        if preview_path.exists():
            os.remove(str(preview_path))
        
        del jobs[job_id]
    
    return jsonify({'success': True})


@app.route('/cleanup-all', methods=['POST'])
def cleanup_all():
    """Clean up all temporary files including processed videos."""
    deleted_count = 0
    
    # Clear uploads
    for f in UPLOAD_FOLDER.iterdir():
        if f.is_file():
            try:
                f.unlink()
                deleted_count += 1
            except Exception:
                pass
    
    # Clear frames
    for f in FRAMES_FOLDER.iterdir():
        if f.is_file():
            try:
                f.unlink()
                deleted_count += 1
            except Exception:
                pass
    
    # Clear processed videos
    for f in PROCESSED_FOLDER.iterdir():
        if f.is_file():
            try:
                f.unlink()
                deleted_count += 1
            except Exception:
                pass
    
    jobs.clear()
    
    return jsonify({'success': True, 'deleted': deleted_count})


@app.route('/processed')
def list_processed():
    """List all processed videos."""
    files = []
    for f in PROCESSED_FOLDER.iterdir():
        if f.is_file() and f.suffix.lower() in ['.mp4', '.m4v', '.mov']:
            files.append({
                'name': f.name,
                'size': f.stat().st_size,
                'modified': f.stat().st_mtime
            })
    
    return jsonify({'files': files})


@app.route('/processed/<filename>')
def download_processed(filename):
    """Download a specific processed file."""
    return send_from_directory(str(PROCESSED_FOLDER), filename, as_attachment=True)


if __name__ == '__main__':
    import socket
    
    # Get local IP for phone access
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = '127.0.0.1'
    
    port = 5001  # Using 5001 to avoid macOS AirPlay Receiver on 5000
    
    print("\n" + "="*60)
    print("🎬 SORA WATERMARK REMOVER - LOCAL EDITION")
    print("="*60)
    print(f"\n📱 Access from your LAPTOP:  http://localhost:{port}")
    print(f"📱 Access from your PHONE:   http://{local_ip}:{port}")
    print("\n💡 Make sure your phone is on the same WiFi network!")
    print("="*60 + "\n")
    
    # Use debug=False for background service stability
    import sys
    debug_mode = '--debug' in sys.argv or 'FLASK_DEBUG' in os.environ
    app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)

