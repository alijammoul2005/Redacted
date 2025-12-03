/**
 * Authentication Helper Functions
 * Handles user authentication, token management, and session handling
 */

/**
 * Get authentication token from storage
 * Checks both localStorage and sessionStorage
 */
function getAuthToken() {
  return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}

/**
 * Set authentication token in storage
 * @param {string} token - JWT access token
 * @param {boolean} remember - Store in localStorage (true) or sessionStorage (false)
 */
function setAuthToken(token, remember = true) {
  if (remember) {
    localStorage.setItem('access_token', token);
  }
  sessionStorage.setItem('access_token', token);
}

/**
 * Clear authentication token from storage
 */
function clearAuthToken() {
  localStorage.removeItem('access_token');
  sessionStorage.removeItem('access_token');
  localStorage.removeItem('userData');
  sessionStorage.removeItem('userData');
}

/**
 * Get user data from storage
 */
function getUserData() {
  const data = localStorage.getItem('userData') || sessionStorage.getItem('userData');
  return data ? JSON.parse(data) : null;
}

/**
 * Set user data in storage
 * @param {object} userData - User data object
 * @param {boolean} remember - Store in localStorage (true) or sessionStorage (false)
 */
function setUserData(userData, remember = true) {
  const dataString = JSON.stringify(userData);
  if (remember) {
    localStorage.setItem('userData', dataString);
  }
  sessionStorage.setItem('userData', dataString);
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
  return !!getAuthToken();
}

/**
 * Require authentication - redirect to login if not authenticated
 * @param {string} redirectUrl - URL to redirect to after login (default: current page)
 */
function requireAuth(redirectUrl = null) {
  if (!isAuthenticated()) {
    const returnUrl = redirectUrl || window.location.pathname + window.location.search;
    sessionStorage.setItem('returnUrl', returnUrl);
    window.location.href = '/frontend/citizen/auth.html';
    return false;
  }
  return true;
}

/**
 * Logout user
 */
function logout() {
  if (confirm('Are you sure you want to logout?')) {
    clearAuthToken();
    window.location.href = '/frontend/citizen/auth.html';
  }
}

/**
 * Handle login
 * @param {string} email - User email
 * @param {string} password - User password
 * @param {boolean} remember - Remember login
 * @returns {Promise<object>} - Login response data
 */
async function login(email, password, remember = true) {
  try {
    const data = await AuthAPI.login(email, password);

    // Store token
    setAuthToken(data.access_token, remember);

    // Store user data
    setUserData({
      user_id: data.user_id,
      email: data.email,
      role: data.role
    }, remember);

    return data;
  } catch (error) {
    throw error;
  }
}

/**
 * Handle registration
 * @param {object} userData - Registration data
 * @returns {Promise<object>} - Registration response data
 */
async function register(userData) {
  try {
    const data = await AuthAPI.register(userData);

    // Auto-login after registration
    setAuthToken(data.access_token, true);
    setUserData({
      user_id: data.user_id,
      email: data.email,
      role: data.role
    }, true);

    return data;
  } catch (error) {
    throw error;
  }
}

/**
 * Get current user information from API
 * @returns {Promise<object>} - User data
 */
async function getCurrentUser() {
  try {
    const data = await AuthAPI.getCurrentUser();

    // Update stored user data
    const userData = {
      user_id: data.user_id,
      email: data.email,
      role: data.role,
      profile: data.profile || {}
    };

    setUserData(userData);
    return userData;
  } catch (error) {
    // If unauthorized, clear token and redirect
    if (error.message.includes('401') || error.message.includes('Session expired')) {
      clearAuthToken();
      window.location.href = '/frontend/citizen/auth.html';
    }
    throw error;
  }
}

/**
 * Check user role
 * @param {string} requiredRole - Required role ('citizen' or 'employee')
 * @returns {boolean} - True if user has required role
 */
function hasRole(requiredRole) {
  const userData = getUserData();
  return userData && userData.role === requiredRole;
}

/**
 * Require specific role - redirect if user doesn't have it
 * @param {string} requiredRole - Required role ('citizen' or 'employee')
 * @param {string} redirectUrl - URL to redirect to if role doesn't match
 */
function requireRole(requiredRole, redirectUrl = '/frontend/citizen/auth.html') {
  if (!requireAuth()) return false;

  if (!hasRole(requiredRole)) {
    alert(`Access denied. This page is for ${requiredRole}s only.`);
    window.location.href = redirectUrl;
    return false;
  }

  return true;
}

/**
 * Initialize authentication on page load
 * Checks if user is already logged in and validates token
 */
async function initAuth() {
  if (isAuthenticated()) {
    try {
      await getCurrentUser();
      return true;
    } catch (error) {
      console.error('Auth initialization failed:', error);
      clearAuthToken();
      return false;
    }
  }
  return false;
}

/**
 * Get redirect URL after login
 */
function getReturnUrl() {
  const returnUrl = sessionStorage.getItem('returnUrl');
  sessionStorage.removeItem('returnUrl');
  return returnUrl || '/frontend/citizen/dashboard.html';
}
