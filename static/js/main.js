// Main JavaScript file for Market Management System

// Initialize tooltips and popovers (Bootstrap)
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Utility Functions
const Utils = {
    // Format currency
    formatCurrency: function(amount) {
        return parseFloat(amount).toFixed(2) + ' جنيه';
    },

    // Format date
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('ar-SA');
    },

    // Format date and time
    formatDateTime: function(date) {
        return new Date(date).toLocaleString('ar-SA');
    },

    // Show confirmation dialog
    confirm: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },

    // Show alert message
    showAlert: function(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container') || document.body;
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        if (alertContainer === document.body) {
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.maxWidth = '400px';
        }
        
        alertContainer.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    },

    // Validate form
    validateForm: function(formSelector) {
        const form = document.querySelector(formSelector);
        if (!form) return false;

        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });

        return isValid;
    },

    // Loading spinner
    showLoading: function(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        }
    },

    // Hide loading
    hideLoading: function(element, content) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = content || '';
        }
    }
};

// QR Code Scanner Functionality
const QRScanner = {
    // Simulate QR code scanning (in real implementation, use camera API)
    scanQR: function(callback) {
        // This is a placeholder for QR scanning functionality
        // In a real implementation, you would use libraries like:
        // - QuaggaJS for barcode scanning
        // - ZXing for QR code scanning
        // - Or the browser's camera API
        
        const qrData = prompt('امسح رمز QR أو أدخل البيانات يدوياً:');
        if (qrData) {
            try {
                const productData = JSON.parse(qrData);
                callback(productData);
            } catch (e) {
                // Try to parse as product ID
                const productId = parseInt(qrData);
                if (!isNaN(productId)) {
                    this.getProductById(productId, callback);
                } else {
                    Utils.showAlert('رمز QR غير صحيح', 'error');
                }
            }
        }
    },

    // Get product by ID
    getProductById: function(productId, callback) {
        fetch(`/get_product/${productId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    Utils.showAlert('المنتج غير موجود', 'error');
                } else {
                    callback(data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Utils.showAlert('حدث خطأ في جلب بيانات المنتج', 'error');
            });
    }
};

// Form validation enhancement
document.addEventListener('DOMContentLoaded', function() {
    // Add validation to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (input.checkValidity()) {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                } else {
                    input.classList.remove('is-valid');
                    input.classList.add('is-invalid');
                }
            });
        });
    });
});

// Search functionality enhancement
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="بحث"]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const targetSelector = this.getAttribute('data-search-target') || '.searchable';
            const targets = document.querySelectorAll(targetSelector);
            
            targets.forEach(target => {
                const text = target.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    target.style.display = '';
                } else {
                    target.style.display = 'none';
                }
            });
        });
    });
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeSearch);

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>طباعة</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
                    <style>
                        body { font-family: Arial, sans-serif; direction: rtl; }
                        .no-print { display: none !important; }
                        @media print {
                            .no-print { display: none !important; }
                        }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// Export functionality
const Export = {
    // Export table to CSV
    tableToCSV: function(tableId, filename = 'export.csv') {
        const table = document.getElementById(tableId);
        if (!table) return;

        let csv = [];
        const rows = table.querySelectorAll('tr');

        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const rowData = [];
            cols.forEach(col => {
                rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
            });
            csv.push(rowData.join(','));
        });

        const csvContent = csv.join('\n');
        const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
};

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl + N: New item (on applicable pages)
    if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        const newButton = document.querySelector('a[href*="add"], button[data-action="new"]');
        if (newButton) newButton.click();
    }
    
    // Ctrl + S: Save (on forms)
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const saveButton = document.querySelector('button[type="submit"], button[data-action="save"]');
        if (saveButton) saveButton.click();
    }
    
    // Ctrl + F: Focus search
    if (e.ctrlKey && e.key === 'f') {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="بحث"]');
        if (searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    }
});

// Auto-save for forms (optional feature)
const AutoSave = {
    interval: null,
    
    start: function(formSelector, endpoint, interval = 30000) {
        const form = document.querySelector(formSelector);
        if (!form) return;
        
        this.interval = setInterval(() => {
            this.save(form, endpoint);
        }, interval);
    },
    
    stop: function() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    },
    
    save: function(form, endpoint) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        // Only save if form has data
        if (Object.values(data).some(value => value.trim())) {
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            }).catch(error => {
                console.log('Auto-save failed:', error);
            });
        }
    }
};

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // In production, you might want to send this to a logging service
});

// Performance monitoring
const Performance = {
    start: function(label) {
        if (window.performance && performance.mark) {
            performance.mark(label + '-start');
        }
    },
    
    end: function(label) {
        if (window.performance && performance.mark && performance.measure) {
            performance.mark(label + '-end');
            performance.measure(label, label + '-start', label + '-end');
            const measures = performance.getEntriesByName(label);
            if (measures.length > 0) {
                console.log(`${label}: ${measures[0].duration.toFixed(2)}ms`);
            }
        }
    }
};

// Initialize performance monitoring
document.addEventListener('DOMContentLoaded', function() {
    Performance.start('page-load');
    
    window.addEventListener('load', function() {
        Performance.end('page-load');
    });
});
