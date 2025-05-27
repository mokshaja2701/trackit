
let qrScanner = null;
let isScanning = false;
let currentStream = null;
let scanningInterval = null;

function initializeQRScanner() {
    console.log('Initializing Real QR Scanner...');
    const video = document.getElementById('qrVideo');
    const canvas = document.getElementById('qrCanvas');
    const status = document.getElementById('scannerStatus');
    
    if (!video || !canvas) {
        console.error('Video or canvas element not found');
        return;
    }
    
    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        status.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Camera not supported on this device';
        status.className = 'alert alert-danger';
        return;
    }
}

function startQRScanner() {
    const video = document.getElementById('qrVideo');
    const status = document.getElementById('scannerStatus');
    
    if (isScanning) return;
    
    status.innerHTML = '<i class="fas fa-camera me-2"></i>Starting camera...';
    status.className = 'alert alert-info';
    
    navigator.mediaDevices.getUserMedia({ 
        video: { 
            facingMode: 'environment',
            width: { ideal: 1920, min: 640 },
            height: { ideal: 1080, min: 480 }
        } 
    })
    .then(stream => {
        currentStream = stream;
        video.srcObject = stream;
        video.play();
        isScanning = true;
        
        status.innerHTML = '<i class="fas fa-qrcode me-2"></i>Scanner active - Fast scanning enabled';
        status.className = 'alert alert-success';
        
        // Start rapid scanning loop for instant detection
        startRapidScanLoop();
    })
    .catch(err => {
        console.error('Error accessing camera:', err);
        status.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Camera access denied or not available';
        status.className = 'alert alert-danger';
    });
}

function stopQRScanner() {
    const video = document.getElementById('qrVideo');
    const status = document.getElementById('scannerStatus');
    
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    
    if (video.srcObject) {
        video.srcObject = null;
    }
    
    if (scanningInterval) {
        clearInterval(scanningInterval);
        scanningInterval = null;
    }
    
    isScanning = false;
    status.innerHTML = '<i class="fas fa-stop me-2"></i>Scanner stopped';
    status.className = 'alert alert-warning';
}

function startRapidScanLoop() {
    if (scanningInterval) {
        clearInterval(scanningInterval);
    }
    
    // High-frequency scanning for instant detection (Google Pay style)
    scanningInterval = setInterval(() => {
        if (isScanning) {
            scanForQRCodeReal();
        }
    }, 100); // Scan every 100ms for instant detection
}

function scanForQRCodeReal() {
    if (!isScanning) return;
    
    const video = document.getElementById('qrVideo');
    const canvas = document.getElementById('qrCanvas');
    const context = canvas.getContext('2d');
    
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.height = video.videoHeight;
        canvas.width = video.videoWidth;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Get image data for processing
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        
        // Send to backend for real QR processing
        processImageForQR(imageData);
    }
}

function processImageForQR(imageData) {
    // Convert imageData to base64 for backend processing
    const canvas = document.getElementById('qrCanvas');
    const dataURL = canvas.toDataURL('image/jpeg', 0.8);
    
    // Send to backend for OpenCV/ZBar processing
    fetch('/process_qr_image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            image_data: dataURL.split(',')[1], // Remove data:image/jpeg;base64, prefix
            scan_timestamp: Date.now()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.qr_detected && data.qr_data) {
            console.log('QR Code detected:', data.qr_data);
            // Temporarily stop scanning to process
            isScanning = false;
            processQRCode(data.qr_data);
        }
    })
    .catch(error => {
        // Silently handle errors to avoid spam during continuous scanning
        if (error.message !== 'Failed to fetch') {
            console.log('QR scan error:', error);
        }
    });
}

function processQRCode(qrData) {
    if (!qrData || qrData.trim() === '') {
        showScanResult(false, 'Invalid QR code data');
        resumeScanning();
        return;
    }
    
    console.log('Processing QR code:', qrData);
    
    // Update status
    const status = document.getElementById('scannerStatus');
    status.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing QR code...';
    status.className = 'alert alert-info';
    
    // Send to server for processing
    fetch('/scan_qr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({ qr_data: qrData })
    })
    .then(response => {
        console.log('Server response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Server response data:', data);
        
        if (data.success) {
            showScanResult(true, data.message || 'QR code scanned successfully!', data);
            addToScanHistory(qrData, true, data.message);
            
            // Update status
            status.innerHTML = '<i class="fas fa-check me-2"></i>QR code processed successfully!';
            status.className = 'alert alert-success';
            
            // Emit WebSocket event for real-time update
            if (window.socket) {
                window.socket.emit('qr_scanned', {
                    order_id: data.order?.id,
                    scan_type: data.scan_type,
                    timestamp: new Date().toISOString()
                });
            }
        } else {
            showScanResult(false, data.error || 'Failed to process QR code');
            addToScanHistory(qrData, false, data.error);
            
            // Update status
            status.innerHTML = '<i class="fas fa-times me-2"></i>Failed to process QR code';
            status.className = 'alert alert-danger';
        }
        
        // Resume scanning after 2 seconds
        setTimeout(resumeScanning, 2000);
    })
    .catch(error => {
        console.error('Error processing QR:', error);
        showScanResult(false, 'Network error - please try again');
        addToScanHistory(qrData, false, 'Network error');
        
        // Update status
        status.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Network error occurred';
        status.className = 'alert alert-danger';
        
        // Resume scanning after 2 seconds
        setTimeout(resumeScanning, 2000);
    });
}

function resumeScanning() {
    if (currentStream && !isScanning) {
        isScanning = true;
        const status = document.getElementById('scannerStatus');
        status.innerHTML = '<i class="fas fa-qrcode me-2"></i>Scanner active - Fast scanning enabled';
        status.className = 'alert alert-success';
    }
}

function showScanResult(success, message, data = null) {
    const modal = document.getElementById('scanResultModal');
    const modalHeader = document.getElementById('modalHeader');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    if (success) {
        modalHeader.className = 'modal-header bg-success text-white';
        modalTitle.innerHTML = '<i class="fas fa-check-circle me-2"></i>Scan Successful';
    } else {
        modalHeader.className = 'modal-header bg-danger text-white';
        modalTitle.innerHTML = '<i class="fas fa-times-circle me-2"></i>Scan Failed';
    }
    
    let content = `<div class="alert alert-${success ? 'success' : 'danger'}">${message}</div>`;
    
    if (success && data) {
        content += `
            <div class="mt-3">
                <h6><i class="fas fa-info-circle me-2"></i>Order Information</h6>
                <div class="bg-light p-3 rounded">
                    <p><strong>Order ID:</strong> #TK${data.order?.id || 'N/A'}</p>
                    <p><strong>Status:</strong> ${data.new_status || 'N/A'}</p>
                    ${data.scan_count ? `<p><strong>Scan Count:</strong> ${data.scan_count}/3</p>` : ''}
                    ${data.delivery_qr_generated ? '<p class="text-success"><strong>✓ Customer delivery QR generated!</strong></p>' : ''}
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = content;
    new bootstrap.Modal(modal).show();
}

function addToScanHistory(qrData, success, message) {
    const historyContainer = document.getElementById('scanHistory');
    const timestamp = new Date().toLocaleString();
    
    const historyItem = document.createElement('div');
    historyItem.className = `alert alert-${success ? 'success' : 'danger'} alert-dismissible fade show`;
    historyItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <strong>${success ? 'Success' : 'Failed'}:</strong> ${message}
                <br><small class="text-muted">${timestamp}</small>
                <br><small class="font-monospace">${qrData.substring(0, 50)}...</small>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Remove the "no history" message if it exists
    const noHistory = historyContainer.querySelector('.text-muted');
    if (noHistory && noHistory.textContent.includes('No scan history')) {
        noHistory.remove();
    }
    
    historyContainer.insertBefore(historyItem, historyContainer.firstChild);
    
    // Keep only last 5 entries
    const items = historyContainer.querySelectorAll('.alert');
    if (items.length > 5) {
        items[items.length - 1].remove();
    }
}

// Event handlers
document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startCamera');
    const stopBtn = document.getElementById('stopCamera');
    const switchBtn = document.getElementById('switchCamera');
    
    if (startBtn) startBtn.addEventListener('click', startQRScanner);
    if (stopBtn) stopBtn.addEventListener('click', stopQRScanner);
    if (switchBtn) switchBtn.addEventListener('click', switchCamera);
    
    // Initialize WebSocket for real-time updates
    initializeWebSocket();
});

function switchCamera() {
    // Stop current camera
    stopQRScanner();
    
    // Start with different facing mode
    setTimeout(() => {
        const video = document.getElementById('qrVideo');
        const currentFacingMode = video.getAttribute('data-facing-mode') || 'environment';
        const newFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
        video.setAttribute('data-facing-mode', newFacingMode);
        
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: newFacingMode,
                width: { ideal: 1920, min: 640 },
                height: { ideal: 1080, min: 480 }
            } 
        })
        .then(stream => {
            currentStream = stream;
            video.srcObject = stream;
            video.play();
            isScanning = true;
            startRapidScanLoop();
        })
        .catch(err => {
            console.error('Error switching camera:', err);
            // Fall back to original camera
            startQRScanner();
        });
    }, 500);
}

function initializeWebSocket() {
    if (typeof io !== 'undefined') {
        window.socket = io();
        
        window.socket.on('connect', function() {
            console.log('Connected to WebSocket');
            window.socket.emit('join_room', {});
        });
        
        window.socket.on('order_status_update', function(data) {
            console.log('Real-time order update:', data);
            // Handle real-time updates
        });
        
        window.socket.on('qr_scan_update', function(data) {
            console.log('Real-time QR scan update:', data);
            // Handle real-time QR scan updates
        });
    }
}

function updateProcessButton() {
    const input = document.getElementById('qrInput');
    const button = document.getElementById('processManualQR');
    button.disabled = !input.value.trim();
}

function processManualQR() {
    const input = document.getElementById('qrInput');
    const qrData = input.value.trim();

    if (qrData) {
        processQRCode(qrData);
        input.value = '';
        updateProcessButton();
    }
}

function testQR(type) {
    const input = document.getElementById('qrInput');
    
    if (type === 'package') {
        // Use a test package QR for order ID 1
        input.value = 'TRACKIT_PACKAGE_1_test123';
    } else if (type === 'delivery') {
        // Use a test delivery QR for order ID 1
        input.value = 'TRACKIT_DELIVERY_1_test456';
    }
    
    updateProcessButton();
}
