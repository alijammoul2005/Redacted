/**
 * Citizen Dashboard - Main Logic
 * Uses centralized API and utility functions
 */

// State Management
let state = {
  currentTab: 'dashboard',
  requests: [],
  complaints: [],
  payments: [],
  notifications: [],
  profile: null,
  filters: {
    requests: 'all',
    complaints: 'all',
    payments: 'all',
    notifications: 'all'
  }
};

// ============ INITIALIZATION ============

document.addEventListener('DOMContentLoaded', async () => {
  // Allow both citizens and employees (swapped roles) - just check authentication
  if (!isAuthenticated()) {
    window.location.href = '/frontend/citizen/auth.html';
  }

  // Navbar scroll effect
  window.addEventListener('scroll', () => {
    const header = document.querySelector('.top-header');
    if (header) {
      if (window.scrollY > 50) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    }
  });

  // Initialize
  initializeEventListeners();
  await loadDashboardData();

  // Update date/time
  updateDateTime();
  setInterval(() => updateDateTime(), 60000); // Update every minute
});

function initializeEventListeners() {
  // Logout
  document.getElementById('logout-btn').addEventListener('click', logout);

  // Profile
  document.getElementById('user-menu-btn').addEventListener('click', openProfile);

  // Notifications icon
  document.getElementById('notif-icon-btn').addEventListener('click', () => switchTab('notifications'));

  // Search inputs with debounce
  document.getElementById('request-search').addEventListener('input', debounce(renderRequests, 300));
  document.getElementById('complaint-search').addEventListener('input', debounce(renderComplaints, 300));
  document.getElementById('payment-search').addEventListener('input', debounce(renderPayments, 300));

  // Filter buttons
  document.querySelectorAll('#requests-section .filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => filterRequests(e.target.dataset.filter));
  });

  document.querySelectorAll('#complaints-section .filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => filterComplaints(e.target.dataset.filter));
  });

  document.querySelectorAll('#payments-section .filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => filterPayments(e.target.dataset.filter));
  });

  document.querySelectorAll('#notifications-tab .filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => filterNotifications(e.target.dataset.filter));
  });

  // New request form
  document.getElementById('new-request-form').addEventListener('submit', handleNewRequest);

  // Feedback form
  document.getElementById('feedback-form').addEventListener('submit', handleFeedback);
  document.getElementById('feedback-comment').addEventListener('input', updateFeedbackCharCount);

  // Feedback rating
  setupFeedbackRating();

  // Save profile
  document.getElementById('save-profile-btn').addEventListener('click', saveProfile);
}

// ============ DATA LOADING ============

async function loadDashboardData() {
  showLoading('content-container');

  try {
    // Get user data first (works for both citizens and employees due to swapped roles)
    const userData = getUserData();
    let profile = { email: userData?.email || 'User' };
    
    // Try to get profile, but don't fail if it doesn't work (swapped roles)
    try {
      profile = await CitizenAPI.getProfile();
    } catch (error) {
      // Silently fail - user might be an employee accessing citizen dashboard
      console.log('Profile fetch failed (expected for swapped roles):', error.message);
    }
    
    // Load other data in parallel (these should work for both roles)
    const [requests, complaints, payments, notifications] = await Promise.all([
      RequestAPI.getMyRequests().catch(() => []),
      ComplaintAPI.getMyComplaints().catch(() => []),
      PaymentAPI.getMyPayments().catch(() => []),
      NotificationAPI.getMyNotifications().catch(() => [])
    ]);

    // Update state
    state.profile = profile;
    state.requests = requests || [];
    state.complaints = complaints || [];
    state.payments = payments || [];
    state.notifications = notifications || [];

    // Update UI
    updateWelcome();
    updateSummaryCards();
    renderRequests();
    renderComplaints();
    renderPayments();
    renderNotifications();

  } catch (error) {
    console.error('Error loading dashboard data:', error);
    showMessage('Failed to load dashboard data: ' + error.message, 'error');
  } finally {
    hideLoading();
  }
}

// ============ UI UPDATES ============

function updateWelcome() {
  const profile = state.profile;
  if (profile) {
    const name = profile.first_name || profile.email;
    document.getElementById('welcome-name').textContent = `Welcome back, ${name}!`;
  }
}

function updateSummaryCards() {
  // Requests
  const pendingRequests = state.requests.filter(r =>
    r.status === 'SUBMITTED' || r.status === 'UNDER_REVIEW'
  ).length;
  document.getElementById('summary-requests').textContent = state.requests.length;
  document.getElementById('summary-requests-detail').textContent = `${pendingRequests} pending`;

  // Complaints
  const pendingComplaints = state.complaints.filter(c =>
    c.status === 'SUBMITTED' || c.status === 'UNDER_INVESTIGATION'
  ).length;
  document.getElementById('summary-complaints').textContent = state.complaints.length;
  document.getElementById('summary-complaints-detail').textContent = `${pendingComplaints} pending`;

  // Payments
  const completedPayments = state.payments.filter(p => p.status === 'COMPLETED').length;
  document.getElementById('summary-payments').textContent = state.payments.length;
  document.getElementById('summary-payments-detail').textContent =
    completedPayments > 0 ? `${completedPayments} completed` : 'No payments yet';

  // Notifications
  const unreadNotifications = state.notifications.filter(n => !n.is_read).length;
  document.getElementById('summary-notifications').textContent = state.notifications.length;
  document.getElementById('summary-notifications-detail').textContent = `${unreadNotifications} unread`;
  document.getElementById('notif-badge').textContent = unreadNotifications;
}

// ============ RENDER FUNCTIONS ============

function renderRequests() {
  const container = document.getElementById('requests-list');
  const searchTerm = document.getElementById('request-search').value.toLowerCase();

  // Filter
  let filtered = state.requests;
  if (state.filters.requests !== 'all') {
    filtered = filtered.filter(r => r.status === state.filters.requests);
  }

  // Search
  if (searchTerm) {
    filtered = filterBySearch(filtered, searchTerm, ['request_type', 'description', 'status']);
  }

  // Render
  if (filtered.length === 0) {
    showEmptyState('requests-list', 'No requests found', '📋');
    return;
  }

  container.innerHTML = filtered.map(req => `
    <div class="item-row" onclick="viewRequestDetail(${req.request_id})">
      <div class="item-row-info">
        <div class="item-row-title">${req.request_type}</div>
        <div class="item-row-meta">${formatDate(req.submitted_date)}</div>
      </div>
      <span class="status-badge ${getStatusClass(req.status)}">${formatStatus(req.status)}</span>
    </div>
  `).join('');
}

function renderComplaints() {
  const container = document.getElementById('complaints-list');
  const searchTerm = document.getElementById('complaint-search').value.toLowerCase();

  // Filter
  let filtered = state.complaints;
  if (state.filters.complaints !== 'all') {
    filtered = filtered.filter(c => c.status === state.filters.complaints);
  }

  // Search
  if (searchTerm) {
    filtered = filterBySearch(filtered, searchTerm, ['title', 'category', 'description', 'status']);
  }

  // Render
  if (filtered.length === 0) {
    showEmptyState('complaints-list', 'No complaints found', '💬');
    return;
  }

  container.innerHTML = filtered.map(complaint => `
    <div class="item-row" onclick="viewComplaintDetail(${complaint.complaint_id})">
      <div class="item-row-info">
        <div class="item-row-title">${complaint.title}</div>
        <div class="item-row-meta">${complaint.category} • ${formatDate(complaint.submitted_date)}</div>
      </div>
      <span class="status-badge ${getStatusClass(complaint.status)}">${formatStatus(complaint.status)}</span>
    </div>
  `).join('');
}

function renderPayments() {
  const container = document.getElementById('payments-list');
  const searchTerm = document.getElementById('payment-search').value.toLowerCase();

  // Filter
  let filtered = state.payments;
  if (state.filters.payments !== 'all') {
    filtered = filtered.filter(p => p.status === state.filters.payments);
  }

  // Search
  if (searchTerm) {
    filtered = filterBySearch(filtered, searchTerm, ['payment_method', 'status']);
  }

  // Render
  if (filtered.length === 0) {
    showEmptyState('payments-list', 'No payments found', '💳');
    return;
  }

  container.innerHTML = filtered.map(payment => `
    <div class="item-row" onclick="window.location.href='payment-receipt.html?payment_id=${payment.payment_id}'">
      <div class="item-row-info">
        <div class="item-row-title">${payment.payment_method} - ${formatCurrency(payment.amount)}</div>
        <div class="item-row-meta">${formatDate(payment.payment_date)}</div>
      </div>
      <span class="status-badge ${getStatusClass(payment.status)}">${formatStatus(payment.status)}</span>
    </div>
  `).join('');
}

function renderNotifications() {
  const container = document.getElementById('notifications-container');

  // Filter
  let filtered = state.notifications;
  if (state.filters.notifications === 'unread') {
    filtered = filtered.filter(n => !n.is_read);
  } else if (state.filters.notifications === 'read') {
    filtered = filtered.filter(n => n.is_read);
  }

  // Render
  if (filtered.length === 0) {
    showEmptyState('notifications-container', 'No notifications', '🔔');
    return;
  }

  container.innerHTML = filtered.map(notif => `
    <div class="item-row ${notif.is_read ? '' : 'unread'}" onclick="markNotificationRead(${notif.notification_id})">
      <div class="item-row-info">
        <div class="item-row-title">${notif.title}</div>
        <div class="item-row-meta">${notif.message}</div>
        <div class="item-row-meta" style="font-size: 11px; color: #888;">${getRelativeTime(notif.created_at)}</div>
      </div>
      ${!notif.is_read ? '<span class="badge" style="background: #6496ff;">New</span>' : ''}
    </div>
  `).join('');
}

// ============ FILTER FUNCTIONS ============

function filterRequests(status) {
  state.filters.requests = status;
  updateActiveFilter('#requests-section', status);
  renderRequests();
}

function filterComplaints(status) {
  state.filters.complaints = status;
  updateActiveFilter('#complaints-section', status);
  renderComplaints();
}

function filterPayments(status) {
  state.filters.payments = status;
  updateActiveFilter('#payments-section', status);
  renderPayments();
}

function filterNotifications(filter) {
  state.filters.notifications = filter;
  updateActiveFilter('#notifications-tab', filter);
  renderNotifications();
}

function updateActiveFilter(sectionSelector, filter) {
  document.querySelectorAll(`${sectionSelector} .filter-btn`).forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });
}

// ============ VIEW DETAIL FUNCTIONS ============

async function viewRequestDetail(requestId) {
  try {
    const request = await RequestAPI.getById(requestId);
    const content = document.getElementById('request-detail-content');

    content.innerHTML = `
      <div style="display: grid; gap: 16px;">
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Request Type</label>
          <p>${request.request_type}</p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Status</label>
          <p><span class="status-badge ${getStatusClass(request.status)}">${formatStatus(request.status)}</span></p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Description</label>
          <p>${request.description}</p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Submitted Date</label>
          <p>${formatDateTime(request.submitted_date)}</p>
        </div>
        ${request.assigned_employee ? `
          <div>
            <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Assigned To</label>
            <p>Employee #${request.assigned_employee}</p>
          </div>
        ` : ''}
      </div>
    `;

    openModal('request-detail-modal');
  } catch (error) {
    showMessage('Error loading request details: ' + error.message, 'error');
  }
}

async function viewComplaintDetail(complaintId) {
  try {
    const complaint = await ComplaintAPI.getById(complaintId);
    const content = document.getElementById('request-detail-content');

    content.innerHTML = `
      <div style="display: grid; gap: 16px;">
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Title</label>
          <p>${complaint.title}</p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Category</label>
          <p>${complaint.category}</p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Status</label>
          <p><span class="status-badge ${getStatusClass(complaint.status)}">${formatStatus(complaint.status)}</span></p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Description</label>
          <p>${complaint.description}</p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Location</label>
          <p>${complaint.location}</p>
        </div>
        <div>
          <label style="color: #f4d48a; font-size: 12px; font-weight: 600; text-transform: uppercase;">Submitted Date</label>
          <p>${formatDateTime(complaint.submitted_date)}</p>
        </div>
      </div>
    `;

    openModal('request-detail-modal');
  } catch (error) {
    showMessage('Error loading complaint details: ' + error.message, 'error');
  }
}

// ============ FORM SUBMISSIONS ============

async function handleNewRequest(e) {
  e.preventDefault();

  const requestData = {
    request_type: document.getElementById('request-type').value,
    description: document.getElementById('request-description').value
  };

  const submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting...';

  try {
    const newRequest = await RequestAPI.create(requestData);

    // Handle file upload if present
    const fileInput = document.getElementById('request-attachment');
    if (fileInput.files.length > 0) {
      await FileAPI.uploadRequestFile(newRequest.request_id, fileInput.files[0]);
    }

    showElementMessage('request-modal-message', 'Request submitted successfully!', 'success');

    // Reload requests
    setTimeout(async () => {
      closeModal('new-request-modal');
      e.target.reset();
      state.requests = await RequestAPI.getMyRequests();
      updateSummaryCards();
      renderRequests();
      showMessage('Request submitted successfully!', 'success');
    }, 1500);

  } catch (error) {
    showElementMessage('request-modal-message', error.message, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit Request';
  }
}

async function handleFeedback(e) {
  e.preventDefault();

  const rating = parseInt(document.getElementById('feedback-rating-input').value);
  if (rating === 0) {
    showElementMessage('feedback-modal-message', 'Please select a rating', 'error');
    return;
  }

  const feedbackData = {
    rating: rating,
    feedback_type: document.getElementById('feedback-type').value,
    comment: document.getElementById('feedback-comment').value
  };

  const submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting...';

  try {
    await FeedbackAPI.create(feedbackData);

    showElementMessage('feedback-modal-message', 'Thank you for your feedback!', 'success');

    setTimeout(() => {
      closeModal('feedback-modal');
      e.target.reset();
      document.getElementById('feedback-rating-input').value = '0';
      document.querySelectorAll('.rating-star').forEach(star => star.classList.remove('selected'));
      showMessage('Feedback submitted successfully!', 'success');
    }, 1500);

  } catch (error) {
    showElementMessage('feedback-modal-message', error.message, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit Feedback';
  }
}

// ============ PROFILE MANAGEMENT ============

async function openProfile() {
  try {
    const profile = await CitizenAPI.getProfile();

    // Populate form
    document.getElementById('profile-name').textContent = `${profile.first_name || ''} ${profile.last_name || ''}`.trim();
    document.getElementById('profile-email').textContent = profile.email;
    document.getElementById('profile-firstname').value = profile.first_name || '';
    document.getElementById('profile-lastname').value = profile.last_name || '';
    document.getElementById('profile-middlename').value = profile.middle_name || '';
    document.getElementById('profile-nationalid').value = profile.national_id || '';
    document.getElementById('profile-dob').value = profile.date_of_birth || '';
    document.getElementById('profile-email-input').value = profile.email || '';
    document.getElementById('profile-phone').value = profile.phone || '';
    document.getElementById('profile-fathername').value = profile.father_name || '';
    document.getElementById('profile-mothername').value = profile.mother_name || '';
    document.getElementById('profile-maritalstatus').value = profile.marital_status || '';
    document.getElementById('profile-address').value = profile.address || '';

    openModal('profile-modal');
  } catch (error) {
    showMessage('Error loading profile: ' + error.message, 'error');
  }
}

async function saveProfile() {
  const profileData = {
    first_name: document.getElementById('profile-firstname').value,
    last_name: document.getElementById('profile-lastname').value,
    middle_name: document.getElementById('profile-middlename').value || null,
    date_of_birth: document.getElementById('profile-dob').value,
    email: document.getElementById('profile-email-input').value,
    phone: document.getElementById('profile-phone').value || null,
    father_name: document.getElementById('profile-fathername').value || null,
    mother_name: document.getElementById('profile-mothername').value || null,
    marital_status: document.getElementById('profile-maritalstatus').value || null,
    address: document.getElementById('profile-address').value || null
  };

  const btn = document.getElementById('save-profile-btn');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  try {
    await CitizenAPI.updateProfile(profileData);
    showElementMessage('profile-message', 'Profile updated successfully!', 'success');

    setTimeout(() => {
      closeModal('profile-modal');
      loadDashboardData();
    }, 1500);

  } catch (error) {
    showElementMessage('profile-message', error.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Save Changes';
  }
}

// ============ NOTIFICATIONS ============

async function markNotificationRead(notificationId) {
  try {
    await NotificationAPI.markAsRead(notificationId);

    // Update state
    const notif = state.notifications.find(n => n.notification_id === notificationId);
    if (notif) {
      notif.is_read = true;
      updateSummaryCards();
      renderNotifications();
    }
  } catch (error) {
    console.error('Error marking notification as read:', error);
  }
}

// ============ TAB SWITCHING ============

function switchTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));

  // Show selected tab
  document.getElementById(`${tabName}-tab`).classList.add('active');

  state.currentTab = tabName;
}

// ============ UTILITY FUNCTIONS ============

function setupFeedbackRating() {
  const stars = document.querySelectorAll('.rating-star');
  const ratingInput = document.getElementById('feedback-rating-input');

  stars.forEach(star => {
    star.addEventListener('click', function() {
      const rating = this.dataset.rating;
      ratingInput.value = rating;

      stars.forEach(s => {
        s.classList.toggle('selected', s.dataset.rating <= rating);
      });
    });
  });
}

function updateFeedbackCharCount() {
  const comment = document.getElementById('feedback-comment').value;
  document.getElementById('feedback-char-count').textContent = `${comment.length}/500 characters`;
}
