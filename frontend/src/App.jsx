import { useState, useEffect, lazy, Suspense } from 'react';
import { checkHealth, getMe, logout, isAuthenticated } from './services/api';
import { useI18n } from './i18n/index.jsx';
import LanguageSelector from './components/LanguageSelector';

// Lazy load components for better performance
const Dashboard = lazy(() => import('./components/Dashboard'));
const TransactionForm = lazy(() => import('./components/TransactionForm'));
const PredictionResult = lazy(() => import('./components/PredictionResult'));
const TransactionHistory = lazy(() => import('./components/TransactionHistory'));
const ModelInfo = lazy(() => import('./components/ModelInfo'));
const Login = lazy(() => import('./components/Login'));
const Settings = lazy(() => import('./components/Settings'));
const Profile = lazy(() => import('./components/Profile'));
const BatchUpload = lazy(() => import('./components/BatchUpload'));
const TimeSeriesChart = lazy(() => import('./components/TimeSeriesChart'));
const AdvancedFilters = lazy(() => import('./components/AdvancedFilters'));
const Admin = lazy(() => import('./components/Admin'));
const Reports = lazy(() => import('./components/Reports'));
const FraudNetworkGraph = lazy(() => import('./components/FraudNetworkGraph'));
const RiskForecast = lazy(() => import('./components/RiskForecast'));
const SimulationLab = lazy(() => import('./components/SimulationLab'));
const GeoVelocity = lazy(() => import('./components/GeoVelocity'));
const DeviceFingerprint = lazy(() => import('./components/DeviceFingerprint'));

// Loading spinner component
const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
  </div>
);
import {
  Shield,
  AlertTriangle,
  Activity,
  LogOut,
  User,
  Moon,
  Sun,
  Bell,
  Settings as SettingsIcon,
  Upload,
  BarChart2,
  Search,
  Users,
  FileText,
  ChevronDown,
  Menu,
  Home,
  MoreHorizontal,
  Network,
  TrendingUp,
  FlaskConical,
  Globe,
  Fingerprint
} from 'lucide-react';

function App() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState([]);
  const [apiStatus, setApiStatus] = useState('checking');
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated());
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) {
      return JSON.parse(saved);
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  // Apply dark mode
  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add('dark');
      root.style.colorScheme = 'dark';
    } else {
      root.classList.remove('dark');
      root.style.colorScheme = 'light';
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(prev => !prev);
  };

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const health = await checkHealth();
        setApiStatus(health.model_loaded ? 'online' : 'no-model');
      } catch (error) {
        setApiStatus('offline');
      }
    };

    checkApiStatus();
    const interval = setInterval(checkApiStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      loadUser();
    }
  }, [isLoggedIn]);

  useEffect(() => {
    const handleLogout = () => {
      setIsLoggedIn(false);
      setUser(null);
    };

    window.addEventListener('auth-logout', handleLogout);
    return () => window.removeEventListener('auth-logout', handleLogout);
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.more-menu-container')) {
        setShowMoreMenu(false);
      }
      if (!e.target.closest('.notifications-container')) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const loadUser = async () => {
    try {
      const userData = await getMe();
      setUser(userData);
    } catch (error) {
      setIsLoggedIn(false);
      setUser(null);
    }
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    logout();
    setIsLoggedIn(false);
    setUser(null);
  };

  const handleUserUpdate = (updatedUser) => {
    setUser(updatedUser);
  };

  const handlePrediction = (result, transaction) => {
    setPrediction(result);
    setHistory(prev => [{
      id: Date.now(),
      timestamp: new Date().toISOString(),
      transaction,
      result,
    }, ...prev].slice(0, 50));

    if (result.is_fraud) {
      const notification = {
        id: Date.now(),
        type: 'fraud',
        message: `Fraud detected! Amount: $${transaction.amount.toFixed(2)}, Risk: ${result.risk_score}%`,
        timestamp: new Date().toISOString(),
      };
      setNotifications(prev => [notification, ...prev].slice(0, 10));
    }
  };

  const clearNotifications = () => {
    setNotifications([]);
    setShowNotifications(false);
  };

  // Main navigation tabs
  const mainTabs = [
    { id: 'dashboard', label: t('nav.dashboard'), icon: Activity },
    { id: 'predict', label: t('nav.analyzer'), icon: Shield },
    { id: 'batch', label: t('nav.batchUpload'), icon: Upload },
    { id: 'analytics', label: t('nav.analytics'), icon: BarChart2 },
    { id: 'history', label: t('nav.history'), icon: Search },
  ];

  // Mobile bottom navigation (limited to 5 items)
  const mobileTabs = [
    { id: 'dashboard', label: t('nav.dashboard'), icon: Home },
    { id: 'predict', label: t('nav.analyzer'), icon: Shield },
    { id: 'batch', label: t('nav.batchUpload'), icon: Upload },
    { id: 'history', label: t('nav.history'), icon: Search },
    { id: 'more', label: t('nav.more'), icon: MoreHorizontal },
  ];

  // More menu items
  const moreMenuItems = [
    { id: 'deviceFingerprint', label: t('nav.deviceFingerprint'), icon: Fingerprint },
    { id: 'geoVelocity', label: t('nav.geoVelocity'), icon: Globe },
    { id: 'simulation', label: t('nav.simulationLab'), icon: FlaskConical },
    { id: 'forecast', label: t('nav.riskForecast'), icon: TrendingUp },
    { id: 'network', label: t('nav.fraudNetwork'), icon: Network },
    { id: 'reports', label: t('nav.reports'), icon: FileText },
    { id: 'profile', label: t('nav.profile'), icon: User },
    { id: 'model', label: t('nav.modelInfo'), icon: AlertTriangle },
    { id: 'settings', label: t('nav.settings'), icon: SettingsIcon },
    { id: 'analytics', label: t('nav.analytics'), icon: BarChart2 },
  ];

  // Admin-only menu items
  const adminMenuItems = [
    { id: 'admin', label: t('nav.admin'), icon: Users },
  ];

  const isAdmin = user?.role === 'admin' || user?.role === 'ADMIN';

  if (!isLoggedIn) {
    return (
      <Suspense fallback={<LoadingSpinner />}>
        <Login onLogin={handleLogin} />
      </Suspense>
    );
  }

  return (
    <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors`}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">Fraud Detection</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">ML-Powered Analysis</p>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-4">
              {/* API Status - hidden on mobile */}
              <div className="hidden sm:flex items-center gap-2">
                <div className={`status-dot ${apiStatus === 'online' ? 'online' : 'offline'}`} />
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {apiStatus === 'online' && t('header.apiOnline')}
                  {apiStatus === 'offline' && t('header.apiOffline')}
                  {apiStatus === 'no-model' && t('header.modelNotLoaded')}
                  {apiStatus === 'checking' && t('header.checking')}
                </span>
              </div>
              {/* Mobile status indicator only */}
              <div className="sm:hidden">
                <div className={`status-dot ${apiStatus === 'online' ? 'online' : 'offline'}`} />
              </div>

              {/* Notifications */}
              <div className="relative notifications-container">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowNotifications(!showNotifications);
                  }}
                  className="relative p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition"
                >
                  <Bell className="w-5 h-5" />
                  {notifications.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {notifications.length}
                    </span>
                  )}
                </button>

                {showNotifications && (
                  <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                    <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                      <span className="font-medium text-gray-900 dark:text-white">{t('header.notifications')}</span>
                      {notifications.length > 0 && (
                        <button
                          onClick={clearNotifications}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                        >
                          {t('header.clearAll')}
                        </button>
                      )}
                    </div>
                    {notifications.length === 0 ? (
                      <p className="text-sm text-gray-500 dark:text-gray-400 px-4 py-4 text-center">
                        {t('header.noNotifications')}
                      </p>
                    ) : (
                      <div className="max-h-64 overflow-y-auto">
                        {notifications.map((notif) => (
                          <div
                            key={notif.id}
                            className={`px-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-0 ${
                              notif.type === 'fraud' ? 'bg-red-50 dark:bg-red-950/40' : ''
                            }`}
                          >
                            <p className={`text-sm ${notif.type === 'fraud' ? 'text-red-800 dark:text-red-200' : 'text-gray-900 dark:text-white'}`}>{notif.message}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {new Date(notif.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Language Selector - Hidden on mobile */}
              <div className="hidden sm:block">
                <LanguageSelector variant="compact" />
              </div>

              {/* Dark mode toggle */}
              <button
                onClick={toggleDarkMode}
                className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200"
                title={darkMode ? t('header.lightMode') : t('header.darkMode')}
              >
                {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* User menu */}
              <div className="flex items-center gap-2 sm:gap-3 pl-2 sm:pl-4 border-l border-gray-200 dark:border-gray-700">
                <div className="hidden sm:flex items-center gap-2">
                  <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {user?.full_name || user?.username || 'User'}
                    </span>
                    {user?.role && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user.role}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 p-2 sm:px-3 sm:py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">{t('header.logout')}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Navigation - Hidden on mobile */}
          <nav className="hidden sm:flex items-center gap-1 -mb-px">
            {mainTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}

            {/* More dropdown */}
            <div className="relative more-menu-container">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMoreMenu(!showMoreMenu);
                }}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  ['deviceFingerprint', 'geoVelocity', 'simulation', 'forecast', 'network', 'reports', 'profile', 'model', 'settings', 'admin'].includes(activeTab)
                    ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                }`}
              >
                {t('nav.more')}
                <ChevronDown className={`w-4 h-4 transition-transform ${showMoreMenu ? 'rotate-180' : ''}`} />
              </button>

              {showMoreMenu && (
                <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
                  {moreMenuItems.map(item => (
                    <button
                      key={item.id}
                      onClick={() => {
                        setActiveTab(item.id);
                        setShowMoreMenu(false);
                      }}
                      className={`w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors ${
                        activeTab === item.id
                          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <item.icon className="w-4 h-4" />
                      {item.label}
                    </button>
                  ))}
                  {isAdmin && (
                    <>
                      <div className="border-t border-gray-200 dark:border-gray-700 my-1"></div>
                      {adminMenuItems.map(item => (
                        <button
                          key={item.id}
                          onClick={() => {
                            setActiveTab(item.id);
                            setShowMoreMenu(false);
                          }}
                          className={`w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors ${
                            activeTab === item.id
                              ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                          }`}
                        >
                          <item.icon className="w-4 h-4" />
                          {item.label}
                        </button>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 pb-24 sm:pb-8">
        <Suspense fallback={<LoadingSpinner />}>
          {activeTab === 'dashboard' && <Dashboard />}

          {activeTab === 'predict' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <TransactionForm
                  onPrediction={handlePrediction}
                  apiStatus={apiStatus}
                />
              </div>
              <div className="space-y-6">
                <PredictionResult prediction={prediction} />
                <TransactionHistory history={history} />
              </div>
            </div>
          )}

          {activeTab === 'batch' && <BatchUpload />}

          {activeTab === 'analytics' && <TimeSeriesChart />}

          {activeTab === 'history' && <AdvancedFilters />}

          {activeTab === 'model' && <ModelInfo />}

          {activeTab === 'settings' && (
            <Settings user={user} onUserUpdate={handleUserUpdate} />
          )}

          {activeTab === 'profile' && (
            <Profile user={user} onUserUpdate={handleUserUpdate} />
          )}

          {activeTab === 'reports' && <Reports />}

          {activeTab === 'network' && <FraudNetworkGraph />}

          {activeTab === 'forecast' && <RiskForecast />}

          {activeTab === 'simulation' && <SimulationLab />}

          {activeTab === 'geoVelocity' && <GeoVelocity />}

          {activeTab === 'deviceFingerprint' && <DeviceFingerprint />}

          {activeTab === 'admin' && isAdmin && (
            <Admin user={user} />
          )}
        </Suspense>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-nav sm:hidden">
        <div className="flex items-center justify-around">
          {mobileTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => {
                if (tab.id === 'more') {
                  setShowMobileMenu(!showMobileMenu);
                } else {
                  setActiveTab(tab.id);
                  setShowMobileMenu(false);
                }
              }}
              className={`mobile-nav-item flex-1 ${
                (tab.id === 'more' && showMobileMenu) || (tab.id !== 'more' && activeTab === tab.id)
                  ? 'active'
                  : ''
              }`}
            >
              <tab.icon className="w-5 h-5 mb-1" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Mobile More Menu */}
        {showMobileMenu && (
          <div className="absolute bottom-full left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="grid grid-cols-3 gap-1 p-4">
              {moreMenuItems.map(item => (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setShowMobileMenu(false);
                  }}
                  className={`flex flex-col items-center justify-center p-4 rounded-lg transition-colors ${
                    activeTab === item.id
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <item.icon className="w-6 h-6 mb-2" />
                  <span className="text-xs font-medium">{item.label}</span>
                </button>
              ))}
              {isAdmin && adminMenuItems.map(item => (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setShowMobileMenu(false);
                  }}
                  className={`flex flex-col items-center justify-center p-4 rounded-lg transition-colors ${
                    activeTab === item.id
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <item.icon className="w-6 h-6 mb-2" />
                  <span className="text-xs font-medium">{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Footer - Hidden on mobile */}
      <footer className="hidden sm:block bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Built with FastAPI, scikit-learn, and React
            </p>
            <div className="flex items-center gap-4">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
              >
                API Documentation
              </a>
              <a
                href="https://github.com/Nostradam4ik/fraud-detection-ml"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
              >
                GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
