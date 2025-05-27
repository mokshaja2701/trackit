
let qrScanner = null;
let isScanning = false;
let currentStream = null;

function initializeQRScanner() {
    console.log('Initializing QR Scanner...');
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
            width: { ideal: 1280 },
            height: { ideal: 720 }
        } 
    })
    .then(stream => {
        currentStream = stream;
        video.srcObject = stream;
        video.play();
        isScanning = true;
        
        status.innerHTML = '<i class="fas fa-qrcode me-2"></i>Scanner active - Hold QR code in view';
        status.className = 'alert alert-success';
        
        // Start scanning loop
        scanForQRCode();
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
    
    isScanning = false;
    status.innerHTML = '<i class="fas fa-stop me-2"></i>Scanner stopped';
    status.className = 'alert alert-warning';
}

function scanForQRCode() {
    if (!isScanning) return;
    
    const video = document.getElementById('qrVideo');
    const canvas = document.getElementById('qrCanvas');
    const context = canvas.getContext('2d');
    
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.height = video.videoHeight;
        canvas.width = video.videoWidth;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        
        try {
            // Simple QR detection - in a real app you'd use a proper QR library
            // For now, we'll simulate QR detection
            detectQRInImageData(imageData);
        } catch (err) {
            console.log('QR detection error:', err);
        }
    }
    
    if (isScanning) {
        requestAnimationFrame(scanForQRCode);
    }
}

function detectQRInImageData(imageData) {
    // Placeholder for QR detection
    // In a real implementation, you would use a QR code detection library
    // For testing, we'll detect based on manual input
}

function processQRCode(qrData) {
    if (!qrData || qrData.trim() === '') {
        showScanResult(false, 'Invalid QR code data');
        return;
    }
    
    // Stop scanning temporarily
    const wasScanning = isScanning;
    if (wasScanning) {
        isScanning = false;
    }
    
    // Send to server for processing
    fetch('/scan_qr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ qr_data: qrData })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showScanResult(true, data.message || 'QR code scanned successfully!', data);
            addToScanHistory(qrData, true, data.message);
        } else {
            showScanResult(false, data.error || 'Failed to process QR code');
            addToScanHistory(qrData, false, data.error);
        }
    })
    .catch(error => {
        console.error('Error processing QR:', error);
        showScanResult(false, 'Network error - please try again');
        addToScanHistory(qrData, false, 'Network error');
    });
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
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        })
        .then(stream => {
            video.srcObject = stream;
            video.play();
            isScanning = true;
            scanForQRCode();
        })
        .catch(err => {
            console.error('Error switching camera:', err);
            // Fall back to original camera
            startQRScanner();
        });
    }, 500);
}
