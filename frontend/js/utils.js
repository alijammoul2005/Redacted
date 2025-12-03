/**
 * Utility Functions
 * Common helper functions used across the application
 */

// ============ DATE & TIME FORMATTING ============

/**
 * Format date to readable string
 * @param {string|Date} dateString - Date to format
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted date
 */
function formatDate(dateString, options = {}) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  };

  return date.toLocaleDateString('en-US', defaultOptions);
}

/**
 * Format date and time
 */
function formatDateTime(dateString) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Format time only
 */
function formatTime(dateString) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Get relative time (e.g., "2 hours ago")
 */
function getRelativeTime(dateString) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;

  return formatDate(dateString);
}

/**
 * Update current date/time display
 */
function updateDateTime(elementId = 'date-display') {
  const element = document.getElementById(elementId);
  if (!element) return;

  const now = new Date();
  const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  element.textContent = now.toLocaleDateString('en-US', dateOptions);
}

// ============ CURRENCY FORMATTING ============

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: USD)
 * @returns {string} - Formatted currency
 */
function formatCurrency(amount, currency = 'USD') {
  if (amount == null || isNaN(amount)) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount);
}

// ============ STATUS FORMATTING ============

/**
 * Format status text
 */
function formatStatus(status) {
  const statusMap = {
    'SUBMITTED': 'Submitted',
    'UNDER_REVIEW': 'Under Review',
    'UNDER_INVESTIGATION': 'Under Investigation',
    'IN_PROGRESS': 'In Progress',
    'APPROVED': 'Approved',
    'REJECTED': 'Rejected',
    'PAID': 'Paid',
    'COMPLETED': 'Completed',
    'RESOLVED': 'Resolved',
    'CLOSED': 'Closed',
    'PENDING': 'Pending',
    'FAILED': 'Failed',
    'REFUNDED': 'Refunded'
  };

  return statusMap[status] || status;
}

/**
 * Get CSS class for status badge
 */
function getStatusClass(status) {
  const classMap = {
    'SUBMITTED': 'submitted',
    'UNDER_REVIEW': 'under-review',
    'UNDER_INVESTIGATION': 'under-review',
    'IN_PROGRESS': 'under-review',
    'APPROVED': 'approved',
    'REJECTED': 'rejected',
    'PAID': 'paid',
    'COMPLETED': 'completed',
    'RESOLVED': 'completed',
    'CLOSED': 'completed',
    'PENDING': 'submitted',
    'FAILED': 'rejected',
    'REFUNDED': 'submitted'
  };

  return classMap[status] || 'submitted';
}

/**
 * Get priority badge class
 */
function getPriorityClass(priority) {
  const classMap = {
    'LOW': 'priority-low',
    'MEDIUM': 'priority-medium',
    'HIGH': 'priority-high',
    'URGENT': 'priority-urgent'
  };

  return classMap[priority] || 'priority-low';
}

// ============ MESSAGES & NOTIFICATIONS ============

/**
 * Show toast message
 * @param {string} text - Message text
 * @param {string} type - Message type (success, error, info, warning)
 * @param {number} duration - Duration in milliseconds (default: 4000)
 */
function showMessage(text, type = 'info', duration = 4000) {
  const messageEl = document.createElement('div');
  messageEl.className = `toast-message toast-${type}`;
  messageEl.textContent = text;
  messageEl.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    max-width: 400px;
    padding: 16px 20px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    animation: slideInRight 0.3s ease;
  `;

  // Set colors based on type
  const colors = {
    success: 'background: rgba(143, 223, 138, 0.15); color: #8fdf8a; border: 1px solid rgba(143, 223, 138, 0.6);',
    error: 'background: rgba(223, 138, 138, 0.15); color: #df8a8a; border: 1px solid rgba(223, 138, 138, 0.6);',
    warning: 'background: rgba(246, 200, 74, 0.15); color: #f6c84a; border: 1px solid rgba(246, 200, 74, 0.6);',
    info: 'background: rgba(100, 150, 255, 0.15); color: #6496ff; border: 1px solid rgba(100, 150, 255, 0.6);'
  };

  messageEl.style.cssText += colors[type] || colors.info;

  document.body.appendChild(messageEl);

  setTimeout(() => {
    messageEl.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => messageEl.remove(), 300);
  }, duration);
}

/**
 * Show message in specific element
 * @param {HTMLElement|string} element - Element or element ID
 * @param {string} text - Message text
 * @param {string} type - Message type
 */
function showElementMessage(element, text, type = 'info') {
  const el = typeof element === 'string' ? document.getElementById(element) : element;
  if (!el) return;

  el.textContent = text;
  el.className = `message ${type}`;
  el.style.display = 'block';
}

/**
 * Hide message in specific element
 */
function hideElementMessage(element) {
  const el = typeof element === 'string' ? document.getElementById(element) : element;
  if (!el) return;

  el.style.display = 'none';
  el.textContent = '';
}

// ============ MODAL MANAGEMENT ============

/**
 * Open modal
 * @param {string} modalId - Modal element ID
 */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;

  // Reset form if present
  const form = modal.querySelector('form');
  if (form) {
    form.reset();
    const messageEl = modal.querySelector('.message');
    if (messageEl) hideElementMessage(messageEl);
  }

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  // Close on backdrop click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal(modalId);
  });
}

/**
 * Close modal
 * @param {string} modalId - Modal element ID
 */
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;

  modal.style.display = 'none';
  document.body.style.overflow = 'auto';
}

// ============ FORM VALIDATION ============

/**
 * Validate email
 */
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Validate phone number
 */
function isValidPhone(phone) {
  // Allow various formats: +1234567890, 123-456-7890, (123) 456-7890
  const re = /^[\d\s\-\+\(\)]+$/;
  return re.test(phone) && phone.replace(/\D/g, '').length >= 7;
}

/**
 * Validate password strength
 * @returns {object} - { valid: boolean, message: string }
 */
function validatePassword(password) {
  if (password.length < 8) {
    return { valid: false, message: 'Password must be at least 8 characters' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter' };
  }
  if (!/\d/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' };
  }

  return { valid: true, message: 'Strong password' };
}

/**
 * Format card number with spaces
 */
function formatCardNumber(cardNumber) {
  let value = cardNumber.replace(/\s/g, '');
  if (value.length > 16) value = value.slice(0, 16);
  return value.match(/.{1,4}/g)?.join(' ') || value;
}

/**
 * Format expiry date as MM/YY
 */
function formatExpiryDate(expiry) {
  let value = expiry.replace(/\D/g, '');
  if (value.length >= 2) {
    value = value.slice(0, 2) + '/' + value.slice(2, 4);
  }
  return value;
}

/**
 * Validate card number using Luhn algorithm
 */
function isValidCardNumber(cardNumber) {
  const cleaned = cardNumber.replace(/\s/g, '');
  if (!/^\d{13,19}$/.test(cleaned)) return false;

  let sum = 0;
  let isEven = false;

  for (let i = cleaned.length - 1; i >= 0; i--) {
    let digit = parseInt(cleaned[i]);

    if (isEven) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }

    sum += digit;
    isEven = !isEven;
  }

  return sum % 10 === 0;
}

// ============ DOM HELPERS ============

/**
 * Scroll to element
 */
function scrollToElement(elementId, behavior = 'smooth') {
  const element = document.getElementById(elementId);
  if (element) {
    element.scrollIntoView({ behavior });
  }
}

/**
 * Toggle element visibility
 */
function toggleElement(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.style.display = element.style.display === 'none' ? 'block' : 'none';
  }
}

/**
 * Show element
 */
function showElement(elementId) {
  const element = document.getElementById(elementId);
  if (element) element.style.display = 'block';
}

/**
 * Hide element
 */
function hideElement(elementId) {
  const element = document.getElementById(elementId);
  if (element) element.style.display = 'none';
}

/**
 * Enable/disable form elements
 */
function setFormEnabled(formId, enabled) {
  const form = document.getElementById(formId);
  if (!form) return;

  const elements = form.querySelectorAll('input, select, textarea, button');
  elements.forEach(el => {
    el.disabled = !enabled;
  });
}

// ============ LOADING STATES ============

/**
 * Show loading spinner
 */
function showLoading(containerId = 'main-content') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const spinner = document.createElement('div');
  spinner.id = 'loading-spinner';
  spinner.className = 'loading-spinner';
  spinner.innerHTML = `
    <div class="spinner"></div>
    <p>Loading...</p>
  `;

  container.appendChild(spinner);
}

/**
 * Hide loading spinner
 */
function hideLoading() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) spinner.remove();
}

// ============ SEARCH & FILTER ============

/**
 * Debounce function
 * @param {function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {function} - Debounced function
 */
function debounce(func, wait = 300) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Filter array by search term
 */
function filterBySearch(items, searchTerm, fields) {
  if (!searchTerm) return items;

  const term = searchTerm.toLowerCase();
  return items.filter(item => {
    return fields.some(field => {
      const value = field.split('.').reduce((obj, key) => obj?.[key], item);
      return value && value.toString().toLowerCase().includes(term);
    });
  });
}

// ============ URL HELPERS ============

/**
 * Get URL parameter
 */
function getUrlParameter(name) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(name);
}

/**
 * Set URL parameter without reload
 */
function setUrlParameter(name, value) {
  const url = new URL(window.location);
  url.searchParams.set(name, value);
  window.history.pushState({}, '', url);
}

/**
 * Remove URL parameter
 */
function removeUrlParameter(name) {
  const url = new URL(window.location);
  url.searchParams.delete(name);
  window.history.pushState({}, '', url);
}

// ============ FILE HELPERS ============

/**
 * Validate file type
 */
function isValidFileType(file, allowedTypes) {
  const fileExtension = file.name.split('.').pop().toLowerCase();
  return allowedTypes.includes(fileExtension);
}

/**
 * Validate file size
 * @param {File} file - File to validate
 * @param {number} maxSizeMB - Maximum size in MB
 */
function isValidFileSize(file, maxSizeMB = 10) {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ============ COPY TO CLIPBOARD ============

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showMessage('Copied to clipboard', 'success');
  } catch (error) {
    showMessage('Failed to copy', 'error');
  }
}

// ============ EMPTY STATE ============

/**
 * Show empty state
 */
function showEmptyState(containerId, message, icon = '📭') {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">${icon}</div>
      <div class="empty-text">${message}</div>
    </div>
  `;
}
