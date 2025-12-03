/**
 * API Helper Functions
 * Centralized API communication for Municipality Management System
 */

// Use dynamic base URL - works with any origin
const API_BASE_URL = (typeof window !== 'undefined' && window.location.origin) 
  ? `${window.location.origin}/api` 
  : 'http://localhost:8000/api';

/**
 * Make an authenticated API request
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {object} options - Fetch options
 * @returns {Promise} - Response data
 */
async function apiRequest(endpoint, options = {}) {
  const token = getAuthToken();

  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers
    }
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
      // Handle authentication errors
      if (response.status === 401) {
        clearAuthToken();
        window.location.href = '/frontend/citizen/auth.html';
        throw new Error('Session expired. Please login again.');
      }

      // Extract error message
      let errorMessage = 'Request failed';
      if (typeof data.detail === 'string') {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map(err => err.msg || err.message).join(', ');
      } else if (data.message) {
        errorMessage = data.message;
      }

      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    if (error.message === 'Failed to fetch') {
      throw new Error('Cannot connect to server. Please check your connection.');
    }
    throw error;
  }
}

/**
 * GET request
 */
async function apiGet(endpoint) {
  return apiRequest(endpoint, { method: 'GET' });
}

/**
 * POST request
 */
async function apiPost(endpoint, data) {
  return apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

/**
 * PUT request
 */
async function apiPut(endpoint, data) {
  return apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

/**
 * DELETE request
 */
async function apiDelete(endpoint) {
  return apiRequest(endpoint, { method: 'DELETE' });
}

/**
 * Form-encoded POST (for login)
 */
async function apiPostForm(endpoint, formData) {
  return apiRequest(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams(formData)
  });
}

// ============ AUTH API ============
const AuthAPI = {
  login: (email, password) => apiPost('/auth/login', { email, password }),
  register: (userData) => apiPost('/auth/register', userData),
  getCurrentUser: () => apiGet('/auth/me'),
  checkAPIStatus: async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/test`);
      return true;
    } catch {
      return false;
    }
  }
};

// ============ CITIZEN API ============
const CitizenAPI = {
  getProfile: () => apiGet('/citizens/me'),
  updateProfile: (data) => apiPut('/citizens/me', data),
  getById: (id) => apiGet(`/citizens/${id}`)
};

// ============ REQUEST API ============
const RequestAPI = {
  getMyRequests: () => apiGet('/requests/my-requests'),
  getAll: (statusFilter = null, skip = 0, limit = 100) => {
    let url = `/requests/all/requests?skip=${skip}&limit=${limit}`;
    if (statusFilter) url += `&status_filter=${statusFilter}`;
    return apiGet(url);
  },
  getById: (id) => apiGet(`/requests/${id}`),
  create: (data) => apiPost('/requests/', data),
  update: (id, data) => apiPut(`/requests/${id}`, data),
  delete: (id) => apiDelete(`/requests/${id}`),
  assign: (id, employeeId) => apiPut(`/requests/${id}/assign/${employeeId}`, {}),
  updateStatus: (id, newStatus, rejectionReason = null) => {
    let url = `/requests/${id}/status?new_status=${newStatus}`;
    if (rejectionReason) url += `&rejection_reason=${encodeURIComponent(rejectionReason)}`;
    return apiPut(url, {});
  },
  approve: (id) => apiPut(`/requests/${id}/approve`, {}),
  reject: (id, reason) => apiPut(`/requests/${id}/reject`, { reason })
};

// ============ PAYMENT API ============
const PaymentAPI = {
  getMyPayments: () => apiGet('/payments/my-payments'),
  getById: (id) => apiGet(`/payments/${id}`),
  getReceipt: (id) => apiGet(`/payments/${id}/receipt`),
  getAmount: (requestId) => apiGet(`/payments/request/${requestId}/amount`),
  create: (data) => apiPost('/payments/', data)
};

// ============ COMPLAINT API ============
const ComplaintAPI = {
  getMyComplaints: () => apiGet('/complaints/my-complaints'),
  getAll: (statusFilter = null, categoryFilter = null, skip = 0, limit = 100) => {
    let url = `/complaints/all/complaints?skip=${skip}&limit=${limit}`;
    if (statusFilter) url += `&status_filter=${statusFilter}`;
    if (categoryFilter) url += `&category_filter=${categoryFilter}`;
    return apiGet(url);
  },
  getById: (id) => apiGet(`/complaints/${id}`),
  create: (data) => apiPost('/complaints/', data),
  update: (id, data) => apiPut(`/complaints/${id}`, data),
  delete: (id) => apiDelete(`/complaints/${id}`),
  assign: (id, employeeId) => apiPut(`/complaints/${id}/assign/${employeeId}`, {}),
  updateStatus: (id, status, resolutionNotes = null) => {
    const body = { status };
    if (resolutionNotes) body.resolution_notes = resolutionNotes;
    return apiPut(`/complaints/${id}/status`, body);
  },
  respond: (id, message) => apiPost(`/complaints/${id}/respond`, { message }),
  resolve: (id) => apiPut(`/complaints/${id}/resolve`, {})
};

// ============ FEEDBACK API ============
const FeedbackAPI = {
  getMyFeedback: () => apiGet('/feedbacks/my-feedbacks'),
  getById: (id) => apiGet(`/feedbacks/${id}`),
  create: (data) => apiPost('/feedbacks/', data),
  getStatistics: () => apiGet('/feedbacks/statistics')
};

// ============ NOTIFICATION API ============
const NotificationAPI = {
  getMyNotifications: (unreadOnly = false) => apiGet(`/notifications/my-notifications?unread_only=${unreadOnly}`),
  getStats: () => apiGet('/notifications/stats'),
  markAsRead: (id) => apiPut(`/notifications/${id}/read`, {}),
  markAllAsRead: () => apiPut('/notifications/mark-all-read', {}),
  delete: (id) => apiDelete(`/notifications/${id}`),
  create: (data) => apiPost('/notifications/send', data)
};

// ============ ANNOUNCEMENT API ============
const AnnouncementAPI = {
  getAll: () => apiGet('/announcements/'),
  getActive: (limit = 10) => apiGet(`/announcements/active?limit=${limit}`),
  getById: (id) => apiGet(`/announcements/${id}`),
  create: (data) => apiPost('/announcements/', data),
  update: (id, data) => apiPut(`/announcements/${id}`, data),
  delete: (id) => apiDelete(`/announcements/${id}`)
};

// ============ EMPLOYEE API ============
const EmployeeAPI = {
  register: (data) => apiPost('/employees/register', data),
  getProfile: () => apiGet('/employees/me'),
  updateProfile: (data) => apiPut('/employees/me', data),
  getAll: () => apiGet('/employees/'),
  getDepartments: () => apiGet('/employees/departments/all')
};

// ============ FILE API ============
const FileAPI = {
  uploadRequestFile: async (requestId, file) => {
    const token = getAuthToken();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/files/requests/${requestId}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'File upload failed');
    }

    return response.json();
  },

  uploadComplaintFile: async (complaintId, file) => {
    const token = getAuthToken();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/files/complaints/${complaintId}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'File upload failed');
    }

    return response.json();
  },

  download: (fileId) => `${API_BASE_URL}/files/${fileId}`,
  delete: (fileId) => apiDelete(`/files/${fileId}`),
  getRequestFiles: (requestId) => apiGet(`/files/requests/${requestId}`),
  getComplaintFiles: (complaintId) => apiGet(`/files/complaints/${complaintId}`)
};
