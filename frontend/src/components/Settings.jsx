import { useState, useEffect } from 'react';
import {
  Shield,
  Key,
  Bell,
  LogOut,
  Smartphone,
  Check,
  X,
  AlertTriangle,
  Mail,
  Trash2,
  Plus,
  TestTube,
  Webhook,
  Link,
  Power,
  Edit2,
  Loader2
} from 'lucide-react';
import {
  setup2FA,
  verify2FA,
  disable2FA,
  logoutAll,
  getAlerts,
  createAlert,
  deleteAlert,
  testAlert,
  getMe,
  getWebhooks,
  createWebhook,
  deleteWebhook,
  testWebhook,
  toggleWebhook,
  getWebhookEvents
} from '../services/api';
import { useI18n } from '../i18n/index.jsx';

export default function Settings({ user, onUserUpdate }) {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState('security');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  // 2FA State
  const [twoFASetup, setTwoFASetup] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [disablePassword, setDisablePassword] = useState('');

  // Alerts State
  const [alerts, setAlerts] = useState([]);
  const [newAlert, setNewAlert] = useState({
    email: user?.email || '',
    alert_type: 'fraud_detected',
    threshold: 0.7
  });

  // Webhooks State
  const [webhooks, setWebhooks] = useState([]);
  const [webhookEvents, setWebhookEvents] = useState([]);
  const [newWebhook, setNewWebhook] = useState({
    name: '',
    url: '',
    event_types: ['fraud_detected'],
    secret: ''
  });
  const [testingWebhook, setTestingWebhook] = useState(null);

  useEffect(() => {
    if (activeTab === 'alerts') {
      loadAlerts();
    }
    if (activeTab === 'webhooks') {
      loadWebhooks();
      loadWebhookEvents();
    }
  }, [activeTab]);

  const loadAlerts = async () => {
    try {
      const data = await getAlerts();
      setAlerts(data);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    }
  };

  const loadWebhooks = async () => {
    try {
      const data = await getWebhooks();
      setWebhooks(data);
    } catch (error) {
      console.error('Failed to load webhooks:', error);
    }
  };

  const loadWebhookEvents = async () => {
    try {
      const data = await getWebhookEvents();
      setWebhookEvents(data.events || []);
    } catch (error) {
      console.error('Failed to load webhook events:', error);
    }
  };

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  // 2FA Functions
  const handleSetup2FA = async () => {
    setLoading(true);
    try {
      const data = await setup2FA();
      setTwoFASetup(data);
      showMessage('Scan the QR code with your authenticator app');
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Failed to setup 2FA', 'error');
    }
    setLoading(false);
  };

  const handleVerify2FA = async () => {
    if (!verifyCode || verifyCode.length !== 6) {
      showMessage('Please enter a 6-digit code', 'error');
      return;
    }
    setLoading(true);
    try {
      await verify2FA(verifyCode);
      showMessage('2FA enabled successfully!');
      setTwoFASetup(null);
      setVerifyCode('');
      // Refresh user data
      const userData = await getMe();
      onUserUpdate(userData);
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Invalid code', 'error');
    }
    setLoading(false);
  };

  const handleDisable2FA = async () => {
    if (!disablePassword) {
      showMessage('Please enter your password', 'error');
      return;
    }
    setLoading(true);
    try {
      await disable2FA(disablePassword);
      showMessage('2FA disabled');
      setDisablePassword('');
      const userData = await getMe();
      onUserUpdate(userData);
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Invalid password', 'error');
    }
    setLoading(false);
  };

  const handleLogoutAll = async () => {
    if (!confirm('This will log you out from all devices. Continue?')) return;
    setLoading(true);
    try {
      await logoutAll();
      showMessage('Logged out from all devices');
    } catch (error) {
      showMessage('Failed to logout', 'error');
    }
    setLoading(false);
  };

  // Alert Functions
  const handleCreateAlert = async () => {
    setLoading(true);
    try {
      await createAlert(newAlert);
      showMessage('Alert created!');
      loadAlerts();
      setNewAlert({ ...newAlert, email: user?.email || '' });
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Failed to create alert', 'error');
    }
    setLoading(false);
  };

  const handleDeleteAlert = async (alertId) => {
    if (!confirm('Delete this alert?')) return;
    try {
      await deleteAlert(alertId);
      showMessage('Alert deleted');
      loadAlerts();
    } catch (error) {
      showMessage('Failed to delete alert', 'error');
    }
  };

  const handleTestAlert = async (alertId) => {
    try {
      await testAlert(alertId);
      showMessage('Test email sent!');
    } catch (error) {
      showMessage('Failed to send test email', 'error');
    }
  };

  // Webhook Functions
  const handleCreateWebhook = async () => {
    if (!newWebhook.name || !newWebhook.url) {
      showMessage('Name and URL are required', 'error');
      return;
    }
    if (newWebhook.event_types.length === 0) {
      showMessage('Select at least one event type', 'error');
      return;
    }
    setLoading(true);
    try {
      await createWebhook(newWebhook);
      showMessage('Webhook created!');
      loadWebhooks();
      setNewWebhook({ name: '', url: '', event_types: ['fraud_detected'], secret: '' });
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Failed to create webhook', 'error');
    }
    setLoading(false);
  };

  const handleDeleteWebhook = async (webhookId) => {
    if (!confirm('Delete this webhook?')) return;
    try {
      await deleteWebhook(webhookId);
      showMessage('Webhook deleted');
      loadWebhooks();
    } catch (error) {
      showMessage('Failed to delete webhook', 'error');
    }
  };

  const handleTestWebhook = async (webhookId) => {
    setTestingWebhook(webhookId);
    try {
      const result = await testWebhook(webhookId);
      showMessage(result.message);
    } catch (error) {
      showMessage('Failed to send test webhook', 'error');
    }
    setTestingWebhook(null);
  };

  const handleToggleWebhook = async (webhookId) => {
    try {
      const result = await toggleWebhook(webhookId);
      showMessage(result.message);
      loadWebhooks();
    } catch (error) {
      showMessage('Failed to toggle webhook', 'error');
    }
  };

  const toggleEventType = (eventType) => {
    setNewWebhook(prev => ({
      ...prev,
      event_types: prev.event_types.includes(eventType)
        ? prev.event_types.filter(e => e !== eventType)
        : [...prev.event_types, eventType]
    }));
  };

  const tabs = [
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'alerts', label: 'Email Alerts', icon: Bell },
    { id: 'webhooks', label: 'Webhooks', icon: Link },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400">Manage your account settings and preferences</p>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'error'
            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
            : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
        }`}>
          {message.type === 'error' ? <AlertTriangle className="w-5 h-5" /> : <Check className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          {/* 2FA Section */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Smartphone className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Two-Factor Authentication</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Add an extra layer of security to your account
                </p>
              </div>
              <div className="ml-auto">
                {user?.is_2fa_enabled ? (
                  <span className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-sm font-medium">
                    Enabled
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full text-sm font-medium">
                    Disabled
                  </span>
                )}
              </div>
            </div>

            {user?.is_2fa_enabled ? (
              <div className="space-y-4">
                <p className="text-gray-600 dark:text-gray-400">
                  Your account is protected with two-factor authentication.
                </p>
                <div className="flex items-center gap-3">
                  <input
                    type="password"
                    placeholder="Enter password to disable"
                    value={disablePassword}
                    onChange={(e) => setDisablePassword(e.target.value)}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                  <button
                    onClick={handleDisable2FA}
                    disabled={loading}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                  >
                    Disable 2FA
                  </button>
                </div>
              </div>
            ) : twoFASetup ? (
              <div className="space-y-4">
                <div className="flex flex-col items-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    Scan this QR code with your authenticator app:
                  </p>
                  <img
                    src={`data:image/png;base64,${twoFASetup.qr_code}`}
                    alt="2FA QR Code"
                    className="w-48 h-48 bg-white p-2 rounded-lg"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Or enter manually: <code className="bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">{twoFASetup.secret}</code>
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Enter 6-digit code"
                    value={verifyCode}
                    onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center text-2xl tracking-widest"
                    maxLength={6}
                  />
                  <button
                    onClick={handleVerify2FA}
                    disabled={loading || verifyCode.length !== 6}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    Verify
                  </button>
                  <button
                    onClick={() => setTwoFASetup(null)}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={handleSetup2FA}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Enable 2FA
              </button>
            )}
          </div>

          {/* Session Management */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <LogOut className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Session Management</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Manage your active sessions
                </p>
              </div>
            </div>
            <button
              onClick={handleLogoutAll}
              disabled={loading}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
            >
              Logout from all devices
            </button>
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          {/* Create Alert */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Create New Alert</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newAlert.email}
                  onChange={(e) => setNewAlert({ ...newAlert, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Alert Type
                </label>
                <select
                  value={newAlert.alert_type}
                  onChange={(e) => setNewAlert({ ...newAlert, alert_type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="fraud_detected">Fraud Detected</option>
                  <option value="high_risk">High Risk Transaction</option>
                  <option value="daily_report">Daily Report</option>
                  <option value="weekly_report">Weekly Report</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Threshold (for fraud alerts)
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newAlert.threshold}
                  onChange={(e) => setNewAlert({ ...newAlert, threshold: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
            <button
              onClick={handleCreateAlert}
              disabled={loading}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Alert
            </button>
          </div>

          {/* Alert List */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Your Alerts</h3>
            {alerts.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400">No alerts configured</p>
            ) : (
              <div className="space-y-3">
                {alerts.map(alert => (
                  <div
                    key={alert.id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <Mail className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{alert.email}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {alert.alert_type.replace('_', ' ')}
                          {alert.threshold && ` (≥${(alert.threshold * 100).toFixed(0)}%)`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleTestAlert(alert.id)}
                        className="p-2 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg"
                        title="Send test email"
                      >
                        <TestTube className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteAlert(alert.id)}
                        className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg"
                        title="Delete alert"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Webhooks Tab */}
      {activeTab === 'webhooks' && (
        <div className="space-y-6">
          {/* Create Webhook */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Create New Webhook</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  placeholder="My Webhook"
                  value={newWebhook.name}
                  onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  URL
                </label>
                <input
                  type="url"
                  placeholder="https://example.com/webhook"
                  value={newWebhook.url}
                  onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Secret (optional)
                </label>
                <input
                  type="password"
                  placeholder="For signature verification"
                  value={newWebhook.secret}
                  onChange={(e) => setNewWebhook({ ...newWebhook, secret: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Events
                </label>
                <div className="flex flex-wrap gap-2">
                  {webhookEvents.map(event => (
                    <button
                      key={event.type}
                      type="button"
                      onClick={() => toggleEventType(event.type)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        newWebhook.event_types.includes(event.type)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                      title={event.description}
                    >
                      {event.type.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <button
              onClick={handleCreateWebhook}
              disabled={loading}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Webhook
            </button>
          </div>

          {/* Webhook List */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Your Webhooks</h3>
            {webhooks.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400">No webhooks configured</p>
            ) : (
              <div className="space-y-4">
                {webhooks.map(webhook => (
                  <div
                    key={webhook.id}
                    className={`p-4 rounded-lg border ${
                      webhook.is_active
                        ? 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600'
                        : 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Link className="w-5 h-5 text-blue-500" />
                          <h4 className="font-medium text-gray-900 dark:text-white">{webhook.name}</h4>
                          {!webhook.is_active && (
                            <span className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-400 rounded">
                              Disabled
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 font-mono truncate">
                          {webhook.url}
                        </p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {webhook.event_types.map(event => (
                            <span
                              key={event}
                              className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded"
                            >
                              {event.replace('_', ' ')}
                            </span>
                          ))}
                        </div>
                        {webhook.last_triggered_at && (
                          <p className="text-xs text-gray-400 mt-2">
                            Last triggered: {new Date(webhook.last_triggered_at).toLocaleString()}
                            {webhook.last_status_code && (
                              <span className={webhook.last_status_code < 300 ? 'text-green-500' : 'text-red-500'}>
                                {' '}(Status: {webhook.last_status_code})
                              </span>
                            )}
                          </p>
                        )}
                        {webhook.failure_count > 0 && (
                          <p className="text-xs text-red-500 mt-1">
                            {webhook.failure_count} failed attempt(s)
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleToggleWebhook(webhook.id)}
                          className={`p-2 rounded-lg ${
                            webhook.is_active
                              ? 'text-green-600 hover:bg-green-100 dark:hover:bg-green-900/30'
                              : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                          }`}
                          title={webhook.is_active ? 'Disable' : 'Enable'}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleTestWebhook(webhook.id)}
                          disabled={testingWebhook === webhook.id}
                          className="p-2 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg disabled:opacity-50"
                          title="Test webhook"
                        >
                          {testingWebhook === webhook.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <TestTube className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDeleteWebhook(webhook.id)}
                          className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg"
                          title="Delete webhook"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Webhook Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
            <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-2">Webhook Payload Format</h4>
            <p className="text-sm text-blue-700 dark:text-blue-400 mb-3">
              When an event occurs, we send a POST request to your URL with the following format:
            </p>
            <pre className="bg-white dark:bg-gray-800 p-4 rounded-lg text-xs text-gray-800 dark:text-gray-200 overflow-x-auto">
{`{
  "event": "fraud_detected",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "prediction_id": 123,
    "is_fraud": true,
    "risk_score": 85,
    "amount": 1500.00
  }
}`}
            </pre>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-3">
              If you set a secret, we include an X-Webhook-Signature header with HMAC-SHA256 signature.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
