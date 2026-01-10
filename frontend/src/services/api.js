import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Simple in-memory cache for API responses
const cache = new Map();
const CACHE_TTL = 60000; // 1 minute default TTL

const getCached = (key) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < cached.ttl) {
    return cached.data;
  }
  cache.delete(key);
  return null;
};

const setCache = (key, data, ttl = CACHE_TTL) => {
  cache.set(key, { data, timestamp: Date.now(), ttl });
};

const clearCache = (pattern) => {
  if (pattern) {
    for (const key of cache.keys()) {
      if (key.includes(pattern)) {
        cache.delete(key);
      }
    }
  } else {
    cache.clear();
  }
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.dispatchEvent(new Event('auth-logout'));
    }
    return Promise.reject(error);
  }
);

// ==================== Authentication ====================

export const register = async (userData) => {
  const response = await api.post('/auth/register', userData);
  return response.data;
};

export const login = async (credentials) => {
  const response = await api.post('/auth/login', credentials);
  const { access_token } = response.data;
  localStorage.setItem('token', access_token);
  return response.data;
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.dispatchEvent(new Event('auth-logout'));
};

export const getMe = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

export const refreshToken = async () => {
  const response = await api.post('/auth/refresh');
  const { access_token } = response.data;
  localStorage.setItem('token', access_token);
  return response.data;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

export const forgotPassword = async (email) => {
  const response = await api.post('/auth/forgot-password', { email });
  return response.data;
};

export const resetPassword = async (token, newPassword) => {
  const response = await api.post('/auth/reset-password', {
    token,
    new_password: newPassword
  });
  return response.data;
};

// ==================== 2FA endpoints ====================

export const setup2FA = async () => {
  const response = await api.post('/auth/2fa/setup');
  return response.data;
};

export const verify2FA = async (code) => {
  const response = await api.post('/auth/2fa/verify', { code });
  return response.data;
};

export const disable2FA = async (password) => {
  const response = await api.post('/auth/2fa/disable', { password });
  return response.data;
};

export const logoutAll = async () => {
  const response = await api.post('/auth/logout-all');
  return response.data;
};

export const changePassword = async (currentPassword, newPassword) => {
  const response = await api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword
  });
  return response.data;
};

export const checkPasswordStrength = async (password) => {
  const response = await api.post('/auth/password-strength', { password });
  return response.data;
};

export const getSessions = async () => {
  const response = await api.get('/auth/sessions');
  return response.data;
};

export const revokeSession = async (sessionId) => {
  const response = await api.delete(`/auth/sessions/${sessionId}`);
  return response.data;
};

export const exportUserData = async () => {
  const response = await api.get('/auth/export-data');
  return response.data;
};

// ==================== Prediction endpoints ====================

export const predictFraud = async (transaction) => {
  const response = await api.post('/predict', transaction);
  return response.data;
};

export const predictBatch = async (transactions) => {
  const response = await api.post('/predict/batch', { transactions });
  return response.data;
};

export const getSampleLegitimate = async () => {
  // Add random parameter to prevent caching
  const response = await api.get(`/predict/sample/legitimate?_=${Date.now()}`);
  return response.data;
};

export const getSampleFraud = async () => {
  // Add random parameter to prevent caching
  const response = await api.get(`/predict/sample/fraud?_=${Date.now()}`);
  return response.data;
};

export const getPredictionHistory = async (limit = 50) => {
  const response = await api.get(`/predict/history?limit=${limit}`);
  return response.data;
};

export const getUserPredictionStats = async () => {
  const response = await api.get('/predict/stats');
  return response.data;
};

// CSV Upload for batch predictions
export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/predict/upload-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob'
  });
  return response;
};

// ==================== Analytics endpoints ====================

export const getStats = async () => {
  const response = await api.get('/analytics/stats');
  return response.data;
};

export const getModelInfo = async () => {
  const cacheKey = 'model-info';
  const cached = getCached(cacheKey);
  if (cached) return cached;

  const response = await api.get('/analytics/model');
  setCache(cacheKey, response.data, 300000); // Cache for 5 minutes
  return response.data;
};

export const getFeatureImportance = async () => {
  const cacheKey = 'feature-importance';
  const cached = getCached(cacheKey);
  if (cached) return cached;

  const response = await api.get('/analytics/features');
  setCache(cacheKey, response.data, 300000); // Cache for 5 minutes
  return response.data;
};

// Time series analytics
export const getTimeSeries = async (period = 'day', days = 30) => {
  const response = await api.get(`/analytics/time-series?period=${period}&days=${days}`);
  return response.data;
};

// Advanced filters
export const filterPredictions = async (filters) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params.append(key, value);
    }
  });
  const response = await api.get(`/analytics/predictions/filter?${params.toString()}`);
  return response.data;
};

// Analytics summary
export const getAnalyticsSummary = async (days = 30) => {
  const response = await api.get(`/analytics/summary?days=${days}`);
  return response.data;
};

// SHAP explanations
export const getShapExplanation = async (predictionId) => {
  const response = await api.get(`/analytics/shap/${predictionId}`);
  return response.data;
};

// ==================== Admin endpoints ====================

export const getSystemStats = async () => {
  const response = await api.get('/admin/stats');
  return response.data;
};

export const getUsers = async (skip = 0, limit = 50) => {
  const response = await api.get(`/admin/users?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const changeUserRole = async (userId, role) => {
  const response = await api.patch(`/admin/users/${userId}/role?role=${role}`);
  return response.data;
};

export const changeUserStatus = async (userId, isActive) => {
  const response = await api.patch(`/admin/users/${userId}/status?is_active=${isActive}`);
  return response.data;
};

export const deleteUser = async (userId) => {
  const response = await api.delete(`/admin/users/${userId}`);
  return response.data;
};

export const getAuditLogs = async (skip = 0, limit = 100) => {
  const response = await api.get(`/admin/audit-logs?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const getModelVersions = async () => {
  const response = await api.get('/admin/models');
  return response.data;
};

export const activateModel = async (modelId) => {
  const response = await api.post(`/admin/models/${modelId}/activate`);
  return response.data;
};

// ==================== Reports endpoints ====================

export const downloadFraudReport = async (days = 30) => {
  const response = await api.get(`/reports/fraud-summary?days=${days}`, {
    responseType: 'blob'
  });
  return response;
};

export const downloadBatchReport = async (batchId) => {
  const response = await api.get(`/reports/batch/${batchId}`, {
    responseType: 'blob'
  });
  return response;
};

export const downloadTrendAnalysisReport = async (days = 30) => {
  const response = await api.get(`/reports/trend-analysis?days=${days}`, {
    responseType: 'blob'
  });
  return response;
};

export const downloadHighRiskReport = async (days = 30, threshold = 50) => {
  const response = await api.get(`/reports/high-risk?days=${days}&threshold=${threshold}`, {
    responseType: 'blob'
  });
  return response;
};

export const downloadModelPerformanceReport = async () => {
  const response = await api.get('/reports/model-performance', {
    responseType: 'blob'
  });
  return response;
};

// Excel exports
export const downloadExcelReport = async (days = 30) => {
  const response = await api.get(`/reports/export/excel?days=${days}`, {
    responseType: 'blob'
  });
  return response;
};

export const downloadExcelFraudOnly = async (days = 30) => {
  const response = await api.get(`/reports/export/excel/fraud-only?days=${days}`, {
    responseType: 'blob'
  });
  return response;
};

export const downloadExcelHighRisk = async (days = 30, threshold = 50) => {
  const response = await api.get(`/reports/export/excel/high-risk?days=${days}&threshold=${threshold}`, {
    responseType: 'blob'
  });
  return response;
};

export const downloadCSVExport = async (days = 30) => {
  const response = await api.get(`/reports/export/csv?days=${days}`, {
    responseType: 'blob'
  });
  return response;
};

// ==================== Alerts endpoints ====================

export const getAlerts = async () => {
  const response = await api.get('/alerts');
  return response.data;
};

export const createAlert = async (alertData) => {
  const params = new URLSearchParams(alertData);
  const response = await api.post(`/alerts?${params.toString()}`);
  return response.data;
};

export const updateAlert = async (alertId, alertData) => {
  const params = new URLSearchParams(alertData);
  const response = await api.patch(`/alerts/${alertId}?${params.toString()}`);
  return response.data;
};

export const deleteAlert = async (alertId) => {
  const response = await api.delete(`/alerts/${alertId}`);
  return response.data;
};

export const testAlert = async (alertId) => {
  const response = await api.post(`/alerts/test/${alertId}`);
  return response.data;
};

// ==================== Teams endpoints ====================

export const getTeams = async () => {
  const response = await api.get('/teams');
  return response.data;
};

export const createTeam = async (name, description) => {
  const response = await api.post(`/teams?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description || '')}`);
  return response.data;
};

export const getTeam = async (teamId) => {
  const response = await api.get(`/teams/${teamId}`);
  return response.data;
};

export const deleteTeam = async (teamId) => {
  const response = await api.delete(`/teams/${teamId}`);
  return response.data;
};

export const addTeamMember = async (teamId, userId) => {
  const response = await api.post(`/teams/${teamId}/members/${userId}`);
  return response.data;
};

export const removeTeamMember = async (teamId, userId) => {
  const response = await api.delete(`/teams/${teamId}/members/${userId}`);
  return response.data;
};

// ==================== Webhooks endpoints ====================

export const getWebhooks = async () => {
  const response = await api.get('/webhooks');
  return response.data;
};

export const getWebhookEvents = async () => {
  const response = await api.get('/webhooks/events');
  return response.data;
};

export const createWebhook = async (webhookData) => {
  const response = await api.post('/webhooks', webhookData);
  return response.data;
};

export const updateWebhook = async (webhookId, webhookData) => {
  const response = await api.patch(`/webhooks/${webhookId}`, webhookData);
  return response.data;
};

export const deleteWebhook = async (webhookId) => {
  const response = await api.delete(`/webhooks/${webhookId}`);
  return response.data;
};

export const testWebhook = async (webhookId) => {
  const response = await api.post(`/webhooks/${webhookId}/test`);
  return response.data;
};

export const toggleWebhook = async (webhookId) => {
  const response = await api.post(`/webhooks/${webhookId}/toggle`);
  return response.data;
};

// ==================== Fraud Network endpoints ====================

export const getFraudNetworkGraph = async (days = 30, minRisk = 30) => {
  const response = await api.get(`/fraud-network/graph?days=${days}&min_risk=${minRisk}`);
  return response.data;
};

export const getFraudNetworkNode = async (nodeId) => {
  const response = await api.get(`/fraud-network/node/${nodeId}`);
  return response.data;
};

export const getFraudNetworkClusters = async (days = 30, minRisk = 30) => {
  const response = await api.get(`/fraud-network/clusters?days=${days}&min_risk=${minRisk}`);
  return response.data;
};

export const getFraudNetworkTimeline = async (days = 30) => {
  const response = await api.get(`/fraud-network/timeline?days=${days}`);
  return response.data;
};

// ==================== Health endpoint ====================

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getRateLimitStatus = async () => {
  const response = await api.get('/rate-limit');
  return response.data;
};

// Helper to extract rate limit headers from any response
export const extractRateLimitHeaders = (response) => {
  return {
    limit: parseInt(response.headers['x-ratelimit-limit'] || '100'),
    remaining: parseInt(response.headers['x-ratelimit-remaining'] || '100'),
    reset: parseInt(response.headers['x-ratelimit-reset'] || '0')
  };
};

// Export cache utilities
export { clearCache };

export default api;
