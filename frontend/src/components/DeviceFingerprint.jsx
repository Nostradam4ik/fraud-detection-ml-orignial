import { useState, useEffect } from 'react';
import { useI18n } from '../i18n/index.jsx';
import {
  Fingerprint,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Monitor,
  Smartphone,
  Tablet,
  Bot,
  Eye,
  Cpu,
  Globe,
  Clock,
  Activity,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Zap,
  Lock,
  Unlock,
  History,
  BarChart3,
  Play
} from 'lucide-react';
import api from '../services/api';

// Stat Card Component
const StatCard = ({ icon: Icon, label, value, subValue, color = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    yellow: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">{value}</p>
          {subValue && <p className="text-xs text-gray-500 dark:text-gray-400">{subValue}</p>}
        </div>
      </div>
    </div>
  );
};

// Risk Badge Component
const RiskBadge = ({ level }) => {
  const { t } = useI18n();
  const config = {
    low: { color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400', icon: CheckCircle },
    medium: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400', icon: AlertTriangle },
    high: { color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400', icon: AlertTriangle },
    critical: { color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400', icon: XCircle },
  };

  const { color, icon: Icon } = config[level] || config.low;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${color}`}>
      <Icon className="w-3 h-3" />
      {t(`deviceFingerprint.${level}`)}
    </span>
  );
};

// Trust Score Gauge Component
const TrustGauge = ({ score, level }) => {
  const { t } = useI18n();
  const getColor = () => {
    if (score >= 80) return 'text-green-500';
    if (score >= 50) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getStrokeColor = () => {
    if (score >= 80) return '#22c55e';
    if (score >= 50) return '#eab308';
    return '#ef4444';
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg className="w-32 h-32 transform -rotate-90">
          <circle
            cx="64"
            cy="64"
            r="45"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            className="text-gray-200 dark:text-gray-700"
          />
          <circle
            cx="64"
            cy="64"
            r="45"
            stroke={getStrokeColor()}
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${getColor()}`}>{score}</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">/100</span>
        </div>
      </div>
      <p className={`mt-2 text-sm font-medium ${getColor()}`}>
        {t(`deviceFingerprint.trust${level.charAt(0).toUpperCase() + level.slice(1)}`)}
      </p>
    </div>
  );
};

// Detection Card Component
const DetectionCard = ({ title, icon: Icon, detected, indicators, riskScore, expanded, onToggle }) => {
  const { t } = useI18n();

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl border ${detected ? 'border-red-300 dark:border-red-700' : 'border-gray-200 dark:border-gray-700'}`}>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4"
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${detected ? 'bg-red-100 dark:bg-red-900/30 text-red-600' : 'bg-green-100 dark:bg-green-900/30 text-green-600'}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="text-left">
            <h4 className="font-medium text-gray-900 dark:text-white">{title}</h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {detected ? `${indicators.length} ${t('deviceFingerprint.issuesFound')}` : t('deviceFingerprint.noIssues')}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {detected && (
            <span className="text-sm font-medium text-red-600 dark:text-red-400">
              {t('deviceFingerprint.risk')}: {riskScore}%
            </span>
          )}
          {expanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </div>
      </button>

      {expanded && indicators.length > 0 && (
        <div className="px-4 pb-4 space-y-2">
          {indicators.map((indicator, idx) => (
            <div key={idx} className={`p-3 rounded-lg ${
              indicator.severity === 'critical' ? 'bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800' :
              indicator.severity === 'high' ? 'bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800' :
              indicator.severity === 'medium' ? 'bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800' :
              'bg-gray-50 dark:bg-gray-700/30 border border-gray-200 dark:border-gray-600'
            }`}>
              <div className="flex items-start gap-2">
                <AlertTriangle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                  indicator.severity === 'critical' ? 'text-red-500' :
                  indicator.severity === 'high' ? 'text-orange-500' :
                  indicator.severity === 'medium' ? 'text-yellow-500' :
                  'text-gray-500'
                }`} />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{indicator.type.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{indicator.detail}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Device Icon Component
const DeviceIcon = ({ type }) => {
  if (type === 'mobile') return <Smartphone className="w-5 h-5" />;
  if (type === 'tablet') return <Tablet className="w-5 h-5" />;
  return <Monitor className="w-5 h-5" />;
};

export default function DeviceFingerprint() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState('analyze');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [deviceHistory, setDeviceHistory] = useState(null);
  const [stats, setStats] = useState(null);
  const [threats, setThreats] = useState(null);
  const [expandedDetection, setExpandedDetection] = useState(null);
  const [simulationType, setSimulationType] = useState('legitimate');

  // Collect browser fingerprint
  const collectFingerprint = () => {
    return {
      user_agent: navigator.userAgent,
      screen_resolution: `${window.screen.width}x${window.screen.height}`,
      color_depth: window.screen.colorDepth,
      timezone_offset: new Date().getTimezoneOffset(),
      language: navigator.language,
      platform: navigator.platform,
      hardware_concurrency: navigator.hardwareConcurrency || null,
      device_memory: navigator.deviceMemory || null,
      canvas_hash: generateCanvasHash(),
      webgl_hash: generateWebGLHash(),
      plugins: Array.from(navigator.plugins || []).map(p => p.name),
      touch_support: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
      do_not_track: navigator.doNotTrack === '1',
      cookies_enabled: navigator.cookieEnabled,
      local_storage: !!window.localStorage,
      session_storage: !!window.sessionStorage,
      indexed_db: !!window.indexedDB,
      ad_blocker: false // Would need actual detection
    };
  };

  const generateCanvasHash = () => {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('fingerprint', 2, 2);
      return canvas.toDataURL().slice(-32);
    } catch {
      return null;
    }
  };

  const generateWebGLHash = () => {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl');
      if (!gl) return null;
      const renderer = gl.getParameter(gl.RENDERER);
      return btoa(renderer).slice(0, 32);
    } catch {
      return null;
    }
  };

  const analyzeFingerprint = async () => {
    setLoading(true);
    try {
      const fingerprint = collectFingerprint();
      const response = await api.post('/device-fingerprint/analyze', {
        user_id: 'current_user',
        fingerprint,
        transaction_id: `txn_${Date.now()}`
      });
      setAnalysis(response.data);
    } catch (error) {
      console.error('Error analyzing fingerprint:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDeviceHistory = async () => {
    setLoading(true);
    try {
      const response = await api.get('/device-fingerprint/history/current_user?days=30');
      setDeviceHistory(response.data);
    } catch (error) {
      console.error('Error loading device history:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.get('/device-fingerprint/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadThreats = async () => {
    try {
      const response = await api.get('/device-fingerprint/known-threats');
      setThreats(response.data);
    } catch (error) {
      console.error('Error loading threats:', error);
    }
  };

  const simulateThreat = async (type) => {
    setLoading(true);
    try {
      const response = await api.post(`/device-fingerprint/simulate-threat?threat_type=${type}`);
      setAnalysis(response.data);
    } catch (error) {
      console.error('Error simulating threat:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    loadThreats();
  }, []);

  useEffect(() => {
    if (activeTab === 'history') {
      loadDeviceHistory();
    }
  }, [activeTab]);

  const tabs = [
    { id: 'analyze', label: t('deviceFingerprint.analyze'), icon: Fingerprint },
    { id: 'history', label: t('deviceFingerprint.history'), icon: History },
    { id: 'simulate', label: t('deviceFingerprint.simulate'), icon: Play },
    { id: 'threats', label: t('deviceFingerprint.threats'), icon: Shield }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Fingerprint className="w-7 h-7 text-purple-600" />
            {t('deviceFingerprint.title')}
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {t('deviceFingerprint.subtitle')}
          </p>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={Monitor}
            label={t('deviceFingerprint.devicesAnalyzed')}
            value={stats.total_devices_analyzed?.toLocaleString()}
            color="blue"
          />
          <StatCard
            icon={Fingerprint}
            label={t('deviceFingerprint.uniqueFingerprints')}
            value={stats.unique_fingerprints?.toLocaleString()}
            color="purple"
          />
          <StatCard
            icon={AlertTriangle}
            label={t('deviceFingerprint.threatsDetected')}
            value={Object.values(stats.threats_detected || {}).reduce((a, b) => a + b, 0)}
            color="red"
          />
          <StatCard
            icon={Shield}
            label={t('deviceFingerprint.highTrust')}
            value={`${stats.trust_distribution?.high || 0}%`}
            color="green"
          />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-purple-600 text-purple-600 dark:border-purple-400 dark:text-purple-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Analyze Tab */}
      {activeTab === 'analyze' && (
        <div className="space-y-6">
          {/* Analyze Button */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="text-center">
              <Fingerprint className="w-16 h-16 mx-auto text-purple-600 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('deviceFingerprint.analyzeDevice')}
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {t('deviceFingerprint.analyzeDesc')}
              </p>
              <button
                onClick={analyzeFingerprint}
                disabled={loading}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors inline-flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    {t('deviceFingerprint.analyzing')}
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    {t('deviceFingerprint.analyzeNow')}
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Analysis Results */}
          {analysis && (
            <div className="space-y-6">
              {/* Overall Risk & Trust */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Risk Score */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    {t('deviceFingerprint.overallRisk')}
                  </h3>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-4xl font-bold text-gray-900 dark:text-white">
                          {analysis.overall_risk?.score}%
                        </span>
                        <RiskBadge level={analysis.overall_risk?.level} />
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {analysis.overall_risk?.recommendation}
                      </p>
                    </div>
                    <div className={`p-4 rounded-full ${
                      analysis.overall_risk?.level === 'low' ? 'bg-green-100 dark:bg-green-900/30' :
                      analysis.overall_risk?.level === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
                      analysis.overall_risk?.level === 'high' ? 'bg-orange-100 dark:bg-orange-900/30' :
                      'bg-red-100 dark:bg-red-900/30'
                    }`}>
                      {analysis.overall_risk?.level === 'low' ? <Lock className="w-8 h-8 text-green-600" /> :
                       analysis.overall_risk?.level === 'critical' ? <Unlock className="w-8 h-8 text-red-600" /> :
                       <AlertTriangle className="w-8 h-8 text-orange-600" />}
                    </div>
                  </div>
                </div>

                {/* Trust Score */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    {t('deviceFingerprint.trustScore')}
                  </h3>
                  <div className="flex items-center justify-center">
                    <TrustGauge score={analysis.trust_score?.score} level={analysis.trust_score?.level} />
                  </div>
                </div>
              </div>

              {/* Device Info */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {t('deviceFingerprint.deviceInfo')}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="flex items-center gap-2">
                    <DeviceIcon type={analysis.device_info?.device_type} />
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t('deviceFingerprint.deviceType')}</p>
                      <p className="font-medium text-gray-900 dark:text-white capitalize">{analysis.device_info?.device_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t('deviceFingerprint.browser')}</p>
                      <p className="font-medium text-gray-900 dark:text-white">{analysis.device_info?.browser}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t('deviceFingerprint.os')}</p>
                      <p className="font-medium text-gray-900 dark:text-white">{analysis.device_info?.os}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t('deviceFingerprint.timezone')}</p>
                      <p className="font-medium text-gray-900 dark:text-white">{analysis.device_info?.timezone}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('deviceFingerprint.fingerprintHash')}: <code className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">{analysis.fingerprint_hash}</code>
                  </p>
                </div>
              </div>

              {/* Detection Results */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('deviceFingerprint.detectionResults')}
                </h3>
                <DetectionCard
                  title={t('deviceFingerprint.automation')}
                  icon={Bot}
                  detected={analysis.detections?.automation?.detected}
                  indicators={analysis.detections?.automation?.indicators || []}
                  riskScore={analysis.detections?.automation?.risk_score}
                  expanded={expandedDetection === 'automation'}
                  onToggle={() => setExpandedDetection(expandedDetection === 'automation' ? null : 'automation')}
                />
                <DetectionCard
                  title={t('deviceFingerprint.emulator')}
                  icon={Smartphone}
                  detected={analysis.detections?.emulator?.detected}
                  indicators={analysis.detections?.emulator?.indicators || []}
                  riskScore={analysis.detections?.emulator?.risk_score}
                  expanded={expandedDetection === 'emulator'}
                  onToggle={() => setExpandedDetection(expandedDetection === 'emulator' ? null : 'emulator')}
                />
                <DetectionCard
                  title={t('deviceFingerprint.vpnProxy')}
                  icon={Eye}
                  detected={analysis.detections?.vpn_proxy?.detected}
                  indicators={analysis.detections?.vpn_proxy?.indicators || []}
                  riskScore={analysis.detections?.vpn_proxy?.risk_score}
                  expanded={expandedDetection === 'vpn_proxy'}
                  onToggle={() => setExpandedDetection(expandedDetection === 'vpn_proxy' ? null : 'vpn_proxy')}
                />
                <DetectionCard
                  title={t('deviceFingerprint.browserTampering')}
                  icon={Activity}
                  detected={analysis.detections?.browser_tampering?.detected}
                  indicators={analysis.detections?.browser_tampering?.indicators || []}
                  riskScore={analysis.detections?.browser_tampering?.risk_score}
                  expanded={expandedDetection === 'tampering'}
                  onToggle={() => setExpandedDetection(expandedDetection === 'tampering' ? null : 'tampering')}
                />
                <DetectionCard
                  title={t('deviceFingerprint.deviceCloning')}
                  icon={Monitor}
                  detected={analysis.detections?.device_cloning?.detected}
                  indicators={analysis.detections?.device_cloning?.indicators || []}
                  riskScore={analysis.detections?.device_cloning?.risk_score}
                  expanded={expandedDetection === 'cloning'}
                  onToggle={() => setExpandedDetection(expandedDetection === 'cloning' ? null : 'cloning')}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-purple-600" />
            </div>
          ) : deviceHistory ? (
            <>
              {/* Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  icon={Monitor}
                  label={t('deviceFingerprint.totalDevices')}
                  value={deviceHistory.total_devices}
                  color="blue"
                />
                <StatCard
                  icon={CheckCircle}
                  label={t('deviceFingerprint.trustedDevices')}
                  value={deviceHistory.summary?.high_trust_devices}
                  color="green"
                />
                <StatCard
                  icon={AlertTriangle}
                  label={t('deviceFingerprint.flaggedDevices')}
                  value={deviceHistory.summary?.flagged_devices}
                  color="red"
                />
                <StatCard
                  icon={Clock}
                  label={t('deviceFingerprint.periodDays')}
                  value={`${deviceHistory.period_days} ${t('deviceFingerprint.days')}`}
                  color="purple"
                />
              </div>

              {/* Device List */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-white">{t('deviceFingerprint.knownDevices')}</h3>
                </div>
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {deviceHistory.devices?.map((device, idx) => (
                    <div key={idx} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`p-3 rounded-lg ${
                            device.trust_level === 'high' ? 'bg-green-100 dark:bg-green-900/30 text-green-600' :
                            device.trust_level === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600' :
                            'bg-red-100 dark:bg-red-900/30 text-red-600'
                          }`}>
                            <DeviceIcon type={device.device_type} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium text-gray-900 dark:text-white">
                                {device.browser} on {device.os}
                              </p>
                              {device.is_current && (
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 text-xs rounded-full">
                                  {t('deviceFingerprint.current')}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {device.location} • {device.total_sessions} {t('deviceFingerprint.sessions')}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <RiskBadge level={device.trust_level === 'high' ? 'low' : device.trust_level === 'low' ? 'high' : 'medium'} />
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {t('deviceFingerprint.lastSeen')}: {new Date(device.last_seen).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Anomalies */}
              {deviceHistory.anomalies?.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-yellow-300 dark:border-yellow-700 overflow-hidden">
                  <div className="p-4 border-b border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950/30">
                    <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      {t('deviceFingerprint.recentAnomalies')}
                    </h3>
                  </div>
                  <div className="divide-y divide-yellow-200 dark:divide-yellow-800">
                    {deviceHistory.anomalies.map((anomaly, idx) => (
                      <div key={idx} className="p-4">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className={`w-5 h-5 flex-shrink-0 ${
                            anomaly.severity === 'high' ? 'text-red-500' : 'text-yellow-500'
                          }`} />
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">{anomaly.description}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {new Date(anomaly.timestamp).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              {t('deviceFingerprint.noHistory')}
            </div>
          )}
        </div>
      )}

      {/* Simulate Tab */}
      {activeTab === 'simulate' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('deviceFingerprint.simulateThreat')}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              {t('deviceFingerprint.simulateDesc')}
            </p>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {['legitimate', 'automation', 'emulator', 'tampering'].map(type => (
                <button
                  key={type}
                  onClick={() => setSimulationType(type)}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    simulationType === type
                      ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg mb-2 flex items-center justify-center ${
                    type === 'legitimate' ? 'bg-green-100 text-green-600' :
                    type === 'automation' ? 'bg-red-100 text-red-600' :
                    type === 'emulator' ? 'bg-orange-100 text-orange-600' :
                    'bg-yellow-100 text-yellow-600'
                  }`}>
                    {type === 'legitimate' ? <CheckCircle className="w-5 h-5" /> :
                     type === 'automation' ? <Bot className="w-5 h-5" /> :
                     type === 'emulator' ? <Smartphone className="w-5 h-5" /> :
                     <Activity className="w-5 h-5" />}
                  </div>
                  <p className="font-medium text-gray-900 dark:text-white capitalize">{t(`deviceFingerprint.sim${type.charAt(0).toUpperCase() + type.slice(1)}`)}</p>
                </button>
              ))}
            </div>

            <button
              onClick={() => simulateThreat(simulationType)}
              disabled={loading}
              className="w-full py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  {t('deviceFingerprint.simulating')}
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  {t('deviceFingerprint.runSimulation')}
                </>
              )}
            </button>
          </div>

          {/* Show analysis results if available */}
          {analysis && activeTab === 'simulate' && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {t('deviceFingerprint.simulationResults')}
              </h3>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <span className="text-3xl font-bold text-gray-900 dark:text-white">
                    {analysis.overall_risk?.score}%
                  </span>
                  <span className="ml-2">
                    <RiskBadge level={analysis.overall_risk?.level} />
                  </span>
                </div>
                <TrustGauge score={analysis.trust_score?.score} level={analysis.trust_score?.level} />
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {analysis.overall_risk?.recommendation}
              </p>
              {analysis.all_indicators?.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('deviceFingerprint.indicatorsFound')}:
                  </p>
                  {analysis.all_indicators.map((indicator, idx) => (
                    <div key={idx} className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      {indicator.detail}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Threats Tab */}
      {activeTab === 'threats' && threats && (
        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {threats.threat_categories?.map((category, idx) => (
              <div key={idx} className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-start gap-4 mb-4">
                  <div className={`p-3 rounded-lg ${
                    category.severity === 'critical' ? 'bg-red-100 dark:bg-red-900/30 text-red-600' :
                    category.severity === 'high' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-600' :
                    'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600'
                  }`}>
                    {category.id === 'automation' ? <Bot className="w-6 h-6" /> :
                     category.id === 'emulator' ? <Smartphone className="w-6 h-6" /> :
                     category.id === 'vpn_proxy' ? <Eye className="w-6 h-6" /> :
                     category.id === 'tampering' ? <Activity className="w-6 h-6" /> :
                     <Monitor className="w-6 h-6" />}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">{category.name}</h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{category.description}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {category.indicators?.map((indicator, iIdx) => (
                    <div key={iIdx} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      {indicator}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Detection Capabilities */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('deviceFingerprint.detectionCapabilities')}
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('deviceFingerprint.fingerprintComponents')}
                </p>
                <div className="flex flex-wrap gap-2">
                  {threats.detection_capabilities?.fingerprint_components?.map((comp, idx) => (
                    <span key={idx} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs">
                      {comp}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('deviceFingerprint.supportedPlatforms')}
                </p>
                <div className="flex flex-wrap gap-2">
                  {threats.detection_capabilities?.platforms?.map((platform, idx) => (
                    <span key={idx} className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs">
                      {platform}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
