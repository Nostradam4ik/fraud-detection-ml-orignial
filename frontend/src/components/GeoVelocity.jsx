import { useState, useEffect } from 'react';
import {
  MapPin,
  Navigation,
  AlertTriangle,
  CheckCircle,
  Clock,
  Plane,
  Car,
  Train,
  PersonStanding,
  Zap,
  RefreshCw,
  Play,
  Search,
  Globe,
  ArrowRight,
  Shield,
  TrendingUp,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useI18n } from '../i18n/index.jsx';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function GeoVelocity() {
  const { t } = useI18n();
  const [userId, setUserId] = useState('demo_user');
  const [days, setDays] = useState(30);
  const [analysis, setAnalysis] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('analysis'); // analysis, map, check
  const [expandedAlert, setExpandedAlert] = useState(null);

  // Real-time check state
  const [checkLocation, setCheckLocation] = useState('');
  const [checkResult, setCheckResult] = useState(null);
  const [cities, setCities] = useState([]);

  useEffect(() => {
    fetchCities();
  }, []);

  const fetchCities = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/v1/geo-velocity/cities`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCities(data.cities);
      }
    } catch (err) {
      console.error('Failed to fetch cities');
    }
  };

  const analyzeUser = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/v1/geo-velocity/analyze/${userId}?days=${days}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
      } else {
        setError('Failed to analyze user');
      }
    } catch (err) {
      setError('Failed to connect to API');
    } finally {
      setLoading(false);
    }
  };

  const fetchMapData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/v1/geo-velocity/map-data/${userId}?days=${days}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        setMapData(data);
      }
    } catch (err) {
      console.error('Failed to fetch map data');
    } finally {
      setLoading(false);
    }
  };

  const simulateFraud = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/v1/geo-velocity/simulate-fraud?user_id=${userId}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        await analyzeUser();
        await fetchMapData();
      }
    } catch (err) {
      setError('Failed to simulate fraud');
    } finally {
      setLoading(false);
    }
  };

  const checkVelocity = async () => {
    if (!checkLocation) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/v1/geo-velocity/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: userId,
          new_transaction: {
            location: checkLocation,
            timestamp: new Date().toISOString(),
            amount: 100,
            merchant: 'Test Merchant'
          }
        })
      });
      if (response.ok) {
        const data = await response.json();
        setCheckResult(data);
        // Refresh analysis
        await analyzeUser();
      }
    } catch (err) {
      setError('Failed to check velocity');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    };
    return colors[severity] || colors.low;
  };

  const getTravelIcon = (travelType) => {
    const icons = {
      walking: PersonStanding,
      car: Car,
      train: Train,
      flight: Plane,
      impossible: Zap
    };
    return icons[travelType] || Zap;
  };

  const formatSpeed = (speed) => {
    if (speed > 1000) {
      return `${(speed / 1000).toFixed(1)}K km/h`;
    }
    return `${speed.toFixed(0)} km/h`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <Globe className="w-8 h-8" />
          <h1 className="text-2xl font-bold">
            {t('geoVelocity.title') || 'Geo-Velocity Tracker'}
          </h1>
        </div>
        <p className="text-blue-100">
          {t('geoVelocity.subtitle') || 'Detect physically impossible travel patterns between transactions'}
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">
              {t('geoVelocity.userId') || 'User ID'}
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Enter user ID"
            />
          </div>

          <div className="w-32">
            <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">
              {t('geoVelocity.period') || 'Period (days)'}
            </label>
            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={analyzeUser}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              {t('geoVelocity.analyze') || 'Analyze'}
            </button>

            <button
              onClick={simulateFraud}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {t('geoVelocity.simulateFraud') || 'Simulate Fraud'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setView('analysis')}
          className={`px-4 py-2 font-medium transition-colors ${
            view === 'analysis'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          {t('geoVelocity.analysisTab') || 'Analysis'}
        </button>
        <button
          onClick={() => { setView('map'); fetchMapData(); }}
          className={`px-4 py-2 font-medium transition-colors ${
            view === 'map'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          {t('geoVelocity.mapTab') || 'Travel Map'}
        </button>
        <button
          onClick={() => setView('check')}
          className={`px-4 py-2 font-medium transition-colors ${
            view === 'check'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          {t('geoVelocity.realtimeCheck') || 'Real-time Check'}
        </button>
      </div>

      {/* Analysis View */}
      {view === 'analysis' && analysis && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={MapPin}
              label={t('geoVelocity.transactions') || 'Transactions'}
              value={analysis.total_transactions}
              color="blue"
            />
            <StatCard
              icon={Globe}
              label={t('geoVelocity.locations') || 'Unique Locations'}
              value={analysis.unique_locations}
              color="green"
            />
            <StatCard
              icon={AlertTriangle}
              label={t('geoVelocity.alerts') || 'Velocity Alerts'}
              value={analysis.alerts.length}
              color={analysis.alerts.length > 0 ? 'red' : 'gray'}
            />
            <StatCard
              icon={Shield}
              label={t('geoVelocity.riskScore') || 'Risk Score'}
              value={`${analysis.risk_score}%`}
              color={analysis.risk_score > 50 ? 'red' : analysis.risk_score > 20 ? 'yellow' : 'green'}
            />
          </div>

          {/* Travel Pattern */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <Navigation className="w-5 h-5 text-blue-500" />
              {t('geoVelocity.travelPattern') || 'Travel Pattern'}
            </h3>
            <p className={`text-lg ${
              analysis.travel_pattern.includes('SUSPICIOUS')
                ? 'text-red-600 dark:text-red-400 font-bold'
                : 'text-gray-700 dark:text-gray-300'
            }`}>
              {analysis.travel_pattern}
            </p>

            {/* Most Frequent Locations */}
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                {t('geoVelocity.frequentLocations') || 'Most Frequent Locations'}
              </h4>
              <div className="flex flex-wrap gap-2">
                {analysis.most_frequent_locations.map((loc, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm"
                  >
                    {loc.location} ({loc.count})
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Alerts */}
          {analysis.alerts.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-red-50 dark:bg-red-900/20">
                <h3 className="font-semibold text-red-700 dark:text-red-300 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  {t('geoVelocity.velocityAlerts') || 'Velocity Alerts'} ({analysis.alerts.length})
                </h3>
              </div>

              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {analysis.alerts.map((alert, index) => {
                  const TravelIcon = getTravelIcon(alert.travel_type_required);
                  const isExpanded = expandedAlert === index;

                  return (
                    <div key={alert.alert_id} className="p-4">
                      <div
                        className="flex items-center justify-between cursor-pointer"
                        onClick={() => setExpandedAlert(isExpanded ? null : index)}
                      >
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                            {alert.severity.toUpperCase()}
                          </span>
                          <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                            <MapPin className="w-4 h-4" />
                            <span>{alert.from_transaction.location}</span>
                            <ArrowRight className="w-4 h-4 text-gray-400" />
                            <MapPin className="w-4 h-4" />
                            <span>{alert.to_transaction.location}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                            <TravelIcon className="w-4 h-4" />
                            <span className="text-sm font-medium">{formatSpeed(alert.required_speed_kmh)}</span>
                          </div>
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="mt-4 pl-4 border-l-2 border-red-300 dark:border-red-700 space-y-3">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-500 dark:text-gray-400">{t('geoVelocity.distance') || 'Distance'}</p>
                              <p className="font-semibold text-gray-900 dark:text-white">{alert.distance_km.toLocaleString()} km</p>
                            </div>
                            <div>
                              <p className="text-gray-500 dark:text-gray-400">{t('geoVelocity.timeDiff') || 'Time Difference'}</p>
                              <p className="font-semibold text-gray-900 dark:text-white">{alert.time_diff_hours.toFixed(1)} hours</p>
                            </div>
                            <div>
                              <p className="text-gray-500 dark:text-gray-400">{t('geoVelocity.requiredSpeed') || 'Required Speed'}</p>
                              <p className="font-semibold text-red-600 dark:text-red-400">{formatSpeed(alert.required_speed_kmh)}</p>
                            </div>
                            <div>
                              <p className="text-gray-500 dark:text-gray-400">{t('geoVelocity.fraudProb') || 'Fraud Probability'}</p>
                              <p className="font-semibold text-red-600 dark:text-red-400">{(alert.probability_fraud * 100).toFixed(0)}%</p>
                            </div>
                          </div>

                          <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                            <p className="text-sm text-gray-700 dark:text-gray-300">{alert.explanation}</p>
                          </div>

                          <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                            <p className="text-sm font-medium text-red-700 dark:text-red-300">
                              {t('geoVelocity.recommendation') || 'Recommendation'}: {alert.recommendation}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Suspicious Patterns */}
          {analysis.suspicious_patterns.length > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-5">
              <h3 className="font-semibold text-red-700 dark:text-red-300 mb-3 flex items-center gap-2">
                <Zap className="w-5 h-5" />
                {t('geoVelocity.suspiciousPatterns') || 'Suspicious Patterns Detected'}
              </h3>
              <ul className="space-y-2">
                {analysis.suspicious_patterns.map((pattern, i) => (
                  <li key={i} className="flex items-start gap-2 text-red-600 dark:text-red-400">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    {pattern}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Map View */}
      {view === 'map' && mapData && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Navigation className="w-5 h-5 text-blue-500" />
              {t('geoVelocity.travelPath') || 'Transaction Travel Path'}
            </h3>

            {/* Simple Text-based Map (since we can't use real maps without API key) */}
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 overflow-x-auto">
              <div className="space-y-3">
                {mapData.markers.map((marker, i) => {
                  const path = mapData.paths[i - 1];
                  return (
                    <div key={marker.id}>
                      {path && (
                        <div className={`flex items-center gap-2 pl-4 py-2 border-l-2 ${
                          path.is_suspicious ? 'border-red-500' : 'border-green-500'
                        }`}>
                          <div className={`text-sm ${path.is_suspicious ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>
                            ↓ {path.distance_km.toLocaleString()} km in {path.time_hours.toFixed(1)}h
                            ({formatSpeed(path.speed_kmh)})
                            {path.is_suspicious && <span className="ml-2 font-bold">⚠️ IMPOSSIBLE</span>}
                          </div>
                        </div>
                      )}
                      <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                        <MapPin className={`w-5 h-5 ${path?.is_suspicious ? 'text-red-500' : 'text-blue-500'}`} />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{marker.location}</p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {new Date(marker.timestamp).toLocaleString()} · ${marker.amount.toFixed(2)} · {marker.merchant}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">
                {t('geoVelocity.totalDistance') || 'Total Distance'}: <span className="font-semibold text-gray-900 dark:text-white">{mapData.total_distance_km.toLocaleString()} km</span>
              </span>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                  {t('geoVelocity.normal') || 'Normal'}
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                  {t('geoVelocity.impossible') || 'Impossible'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Check View */}
      {view === 'check' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-500" />
              {t('geoVelocity.checkNewTransaction') || 'Check New Transaction'}
            </h3>

            <div className="flex gap-3">
              <div className="flex-1">
                <select
                  value={checkLocation}
                  onChange={(e) => setCheckLocation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">{t('geoVelocity.selectLocation') || 'Select location...'}</option>
                  {cities.map((city) => (
                    <option key={city.name} value={city.name}>{city.name}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={checkVelocity}
                disabled={loading || !checkLocation}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                {t('geoVelocity.check') || 'Check'}
              </button>
            </div>

            {checkResult && (
              <div className={`mt-4 p-4 rounded-lg ${
                checkResult.is_suspicious
                  ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                  : 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
              }`}>
                <div className="flex items-center gap-3 mb-2">
                  {checkResult.is_suspicious ? (
                    <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
                  ) : (
                    <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                  )}
                  <span className={`text-lg font-semibold ${
                    checkResult.is_suspicious ? 'text-red-700 dark:text-red-300' : 'text-green-700 dark:text-green-300'
                  }`}>
                    {checkResult.is_suspicious
                      ? (t('geoVelocity.suspicious') || 'Suspicious Velocity Detected!')
                      : (t('geoVelocity.passed') || 'Velocity Check Passed')
                    }
                  </span>
                </div>
                <p className={`text-sm ${
                  checkResult.is_suspicious ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
                }`}>
                  {checkResult.message}
                </p>

                {checkResult.alert && (
                  <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-700">
                    <p className="text-sm text-red-700 dark:text-red-300 font-medium">
                      {checkResult.alert.recommendation}
                    </p>
                  </div>
                )}

                <div className="mt-3 flex items-center gap-4 text-sm">
                  <span className={`px-2 py-1 rounded ${
                    checkResult.can_proceed
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  }`}>
                    {checkResult.can_proceed
                      ? (t('geoVelocity.canProceed') || 'Can Proceed')
                      : (t('geoVelocity.blocked') || 'Should Block')
                    }
                  </span>
                  {checkResult.requires_verification && (
                    <span className="px-2 py-1 rounded bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
                      {t('geoVelocity.requiresVerification') || 'Requires Verification'}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5">
            <div className="flex items-start gap-3">
              <Info className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">
                  {t('geoVelocity.howItWorksTitle') || 'How Geo-Velocity Detection Works'}
                </h3>
                <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                  <li>• {t('geoVelocity.howIt1') || 'Calculates distance between consecutive transaction locations'}</li>
                  <li>• {t('geoVelocity.howIt2') || 'Measures time elapsed between transactions'}</li>
                  <li>• {t('geoVelocity.howIt3') || 'Determines if required travel speed is physically possible'}</li>
                  <li>• {t('geoVelocity.howIt4') || 'Max commercial flight speed: 900 km/h - anything faster is impossible'}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!analysis && view === 'analysis' && (
        <div className="text-center py-12">
          <Globe className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {t('geoVelocity.noData') || 'No Analysis Yet'}
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {t('geoVelocity.clickAnalyze') || 'Enter a user ID and click Analyze to view geo-velocity patterns'}
          </p>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    yellow: 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400',
    red: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
    gray: 'bg-gray-50 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400'
  };

  return (
    <div className={`rounded-xl p-4 ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4" />
        <span className="text-sm">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

export default GeoVelocity;
