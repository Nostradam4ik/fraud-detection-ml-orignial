/**
 * Push Notifications Service
 * Handles browser push notifications for fraud alerts
 */

class NotificationService {
  constructor() {
    this.permission = Notification.permission;
    this.registration = null;
  }

  /**
   * Request notification permission from user
   */
  async requestPermission() {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    const permission = await Notification.requestPermission();
    this.permission = permission;

    return permission === 'granted';
  }

  /**
   * Show a notification
   */
  async showNotification(title, options = {}) {
    if (this.permission !== 'granted') {
      const granted = await this.requestPermission();
      if (!granted) {
        console.warn('Notification permission denied');
        return;
      }
    }

    const defaultOptions = {
      icon: '/logo192.png',
      badge: '/logo192.png',
      vibrate: [200, 100, 200],
      requireInteraction: false,
      ...options
    };

    // Use service worker if available
    if ('serviceWorker' in navigator && this.registration) {
      await this.registration.showNotification(title, defaultOptions);
    } else {
      new Notification(title, defaultOptions);
    }
  }

  /**
   * Show fraud alert notification
   */
  async showFraudAlert(data) {
    const options = {
      body: `Transaction #${data.id} - Amount: $${data.amount}\nRisk Score: ${data.riskScore}%`,
      icon: '/fraud-alert-icon.png',
      badge: '/fraud-badge.png',
      tag: 'fraud-alert',
      requireInteraction: true,
      actions: [
        { action: 'view', title: 'View Details' },
        { action: 'dismiss', title: 'Dismiss' }
      ],
      data: {
        url: `/prediction/${data.id}`,
        type: 'fraud_alert',
        ...data
      },
      vibrate: [300, 200, 300],
      sound: '/alert-sound.mp3'
    };

    await this.showNotification('🚨 Fraud Detected!', options);
  }

  /**
   * Show high risk notification
   */
  async showHighRiskAlert(data) {
    const options = {
      body: `High risk transaction detected\nAmount: $${data.amount}\nRisk: ${data.riskScore}%`,
      icon: '/warning-icon.png',
      tag: 'high-risk',
      requireInteraction: false,
      data: {
        url: `/prediction/${data.id}`,
        type: 'high_risk',
        ...data
      }
    };

    await this.showNotification('⚠️ High Risk Transaction', options);
  }

  /**
   * Show anomaly alert
   */
  async showAnomalyAlert(data) {
    const options = {
      body: data.description || 'Unusual activity detected',
      icon: '/anomaly-icon.png',
      tag: 'anomaly',
      data: {
        type: 'anomaly',
        ...data
      }
    };

    await this.showNotification('📊 Anomaly Detected', options);
  }

  /**
   * Register service worker for push notifications
   */
  async registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker not supported');
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js');
      this.registration = registration;
      console.log('Service Worker registered:', registration);
      return registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return null;
    }
  }

  /**
   * Subscribe to push notifications
   */
  async subscribeToPush() {
    if (!this.registration) {
      await this.registerServiceWorker();
    }

    if (!this.registration) {
      return null;
    }

    try {
      // Get push subscription
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this._urlBase64ToUint8Array(process.env.REACT_APP_VAPID_PUBLIC_KEY)
      });

      console.log('Push subscription:', subscription);

      // Send subscription to server
      await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/push/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(subscription)
      });

      return subscription;
    } catch (error) {
      console.error('Push subscription failed:', error);
      return null;
    }
  }

  /**
   * Convert VAPID key
   */
  _urlBase64ToUint8Array(base64String) {
    if (!base64String) {
      // Default key for development
      base64String = 'BEl62iUYgUivxIkv69yViEuiBIa-Ib37gp_ObC0TgAVMM1JtmYYWlYMz0lZGbCdmCJKqmNM1Gu7KfhkE7s1DF3M';
    }

    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  /**
   * Test notification system
   */
  async test() {
    await this.showNotification('Test Notification', {
      body: 'If you see this, notifications are working!',
      icon: '/logo192.png'
    });
  }
}

export const notificationService = new NotificationService();
export default notificationService;
