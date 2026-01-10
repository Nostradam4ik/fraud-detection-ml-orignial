import { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Calendar,
  AlertTriangle,
  Shield,
  Sun,
  Moon,
  RefreshCw,
  ChevronRight,
  Zap,
  Target,
  BarChart3,
  Activity,
  Info,
  Bell,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useI18n } from '../i18n/index.jsx';

// API call to get forecast
const getForecast = async (token, hours = 72) => {
  const response = await fetch(`/api/v1/forecast?hours=${hours}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to fetch forecast');
  return response.json();
};

const getHeatmap = async (token) => {
  const response = await fetch('/api/v1/forecast/heatmap', {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to fetch heatmap');
  return response.json();
};

// Risk level colors
const getRiskColor = (level) => {
  const colors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-amber-500',
    low: 'bg-green-500'
  };
  return colors[level] || colors.low;
};

const getRiskBgLight = (level) => {
  const colors = {
    critical: 'bg-red-100 dark:bg-red-900/30',
    high: 'bg-orange-100 dark:bg-orange-900/30',
    medium: 'bg-amber-100 dark:bg-amber-900/30',
    low: 'bg-green-100 dark:bg-green-900/30'
  };
  return colors[level] || colors.low;
};

const getRiskTextColor = (level) => {
  const colors = {
    critical: 'text-red-700 dark:text-red-300',
    high: 'text-orange-700 dark:text-orange-300',
    medium: 'text-amber-700 dark:text-amber-300',
    low: 'text-green-700 dark:text-green-300'
  };
  return colors[level] || colors.low;
};

const getRiskBorderColor = (level) => {
  const colors = {
    critical: 'border-red-300 dark:border-red-700',
    high: 'border-orange-300 dark:border-orange-700',
    medium: 'border-amber-300 dark:border-amber-700',
    low: 'border-green-300 dark:border-green-700'
  };
  return colors[level] || colors.low;
};

// Heatmap cell color
const getHeatmapColor = (score) => {
  if (score >= 75) return 'bg-red-500 hover:bg-red-600';
  if (score >= 50) return 'bg-orange-500 hover:bg-orange-600';
  if (score >= 25) return 'bg-amber-400 hover:bg-amber-500';
  return 'bg-green-400 hover:bg-green-500';
};

export default function RiskForecast() {
  const { t } = useI18n();
  const [forecast, setForecast] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [forecastHours, setForecastHours] = useState(72);
  const [activeView, setActiveView] = useState('timeline'); // timeline, heatmap, daily
  const [expandedDay, setExpandedDay] = useState(null);
  const [hoveredCell, setHoveredCell] = useState(null);

  useEffect(() => {
    loadData();
  }, [forecastHours]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const [forecastData, heatmapData] = await Promise.all([
        getForecast(token, forecastHours),
        getHeatmap(token)
      ]);
      setForecast(forecastData);
      setHeatmap(heatmapData);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  // Group hourly forecasts by day for timeline view
  const groupedByDay = useMemo(() => {
    if (!forecast?.hourly_forecast) return {};

    const groups = {};
    forecast.hourly_forecast.forEach(hour => {
      if (!groups[hour.date]) {
        groups[hour.date] = {
          date: hour.date,
          day_of_week: hour.day_of_week,
          hours: []
        };
      }
      groups[hour.date].hours.push(hour);
    });
    return groups;
  }, [forecast]);

  // Transform heatmap data for visualization
  const heatmapGrid = useMemo(() => {
    if (!heatmap?.heatmap) return [];

    const grid = Array(7).fill(null).map(() => Array(24).fill(null));
    heatmap.heatmap.forEach(cell => {
      grid[cell.day][cell.hour] = cell;
    });
    return grid;
  }, [heatmap]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <TrendingUp className="w-16 h-16 text-indigo-500 animate-pulse" />
            <Activity className="w-6 h-6 text-amber-400 absolute -top-1 -right-1 animate-bounce" />
          </div>
          <p className="text-gray-600 dark:text-gray-400 font-medium">
            {t('forecast.analyzing') || 'Analyzing patterns and generating forecast...'}
          </p>
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            {t('common.retry') || 'Retry'}
          </button>
        </div>
      </div>
    );
  }

  if (!forecast) return null;

  const DAY_NAMES_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-indigo-600" />
            {t('forecast.title') || 'Predictive Risk Forecast'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {t('forecast.subtitle') || 'AI-powered prediction of future fraud risk periods'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Forecast period selector */}
          <select
            value={forecastHours}
            onChange={(e) => setForecastHours(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value={24}>24 hours</option>
            <option value={48}>48 hours</option>
            <option value={72}>72 hours</option>
            <option value={168}>7 days</option>
          </select>

          <button
            onClick={loadData}
            className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Overall Risk Summary */}
      <div className={`rounded-xl p-6 border-2 ${getRiskBorderColor(forecast.overall_risk_next_24h)} ${getRiskBgLight(forecast.overall_risk_next_24h)}`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={`p-4 rounded-full ${getRiskColor(forecast.overall_risk_next_24h)}`}>
              {forecast.overall_risk_next_24h === 'critical' ? (
                <AlertTriangle className="w-8 h-8 text-white" />
              ) : forecast.overall_risk_next_24h === 'high' ? (
                <Zap className="w-8 h-8 text-white" />
              ) : (
                <Shield className="w-8 h-8 text-white" />
              )}
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 uppercase font-medium">
                {t('forecast.next24h') || 'Next 24 Hours Risk'}
              </p>
              <p className={`text-3xl font-bold ${getRiskTextColor(forecast.overall_risk_next_24h)}`}>
                {forecast.overall_risk_next_24h.toUpperCase()}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('forecast.confidence') || 'Confidence'}: {forecast.confidence_level}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900 dark:text-white">
                {forecast.overall_risk_score.toFixed(0)}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Risk Score</p>
            </div>
            <div className="h-16 w-px bg-gray-300 dark:bg-gray-600" />
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900 dark:text-white">
                {forecast.active_patterns.length}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Active Patterns</p>
            </div>
          </div>
        </div>
      </div>

      {/* Active Patterns */}
      {forecast.active_patterns.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-500" />
            {t('forecast.activePatterns') || 'Active Risk Patterns'}
          </h3>
          <div className="flex flex-wrap gap-3">
            {forecast.active_patterns.map((pattern, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 px-3 py-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800"
              >
                <span className="text-xl">{pattern.icon}</span>
                <div>
                  <p className="font-medium text-purple-800 dark:text-purple-200 text-sm">
                    {pattern.pattern_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                  <p className="text-xs text-purple-600 dark:text-purple-400">
                    {pattern.risk_multiplier}x risk multiplier
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {[
          { id: 'timeline', label: t('forecast.timeline') || 'Timeline', icon: Clock },
          { id: 'heatmap', label: t('forecast.heatmap') || 'Heatmap', icon: BarChart3 },
          { id: 'daily', label: t('forecast.daily') || 'Daily Summary', icon: Calendar }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveView(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeView === tab.id
                ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Timeline View */}
      {activeView === 'timeline' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {t('forecast.hourlyForecast') || 'Hourly Risk Forecast'}
            </h3>
          </div>

          <div className="overflow-x-auto">
            <div className="min-w-[800px] p-4">
              {Object.values(groupedByDay).map((day, dayIdx) => (
                <div key={day.date} className="mb-6 last:mb-0">
                  <div className="flex items-center gap-2 mb-3">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <span className="font-medium text-gray-900 dark:text-white">
                      {day.day_of_week}, {day.date}
                    </span>
                  </div>

                  <div className="flex gap-1">
                    {day.hours.map((hour, hourIdx) => (
                      <div
                        key={hourIdx}
                        className={`flex-1 h-12 rounded cursor-pointer transition-all hover:scale-105 ${getHeatmapColor(hour.risk_score)}`}
                        title={`${hour.hour}:00 - Risk: ${hour.risk_score.toFixed(0)}%`}
                      >
                        <div className="h-full flex items-center justify-center">
                          <span className="text-xs font-medium text-white/90">
                            {hour.hour}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Hour labels */}
                  <div className="flex gap-1 mt-1">
                    {day.hours.map((hour, hourIdx) => (
                      <div key={hourIdx} className="flex-1 text-center">
                        <span className="text-[10px] text-gray-400">
                          {hour.hour % 6 === 0 ? `${hour.hour}h` : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-green-400" />
                <span className="text-gray-600 dark:text-gray-400">Low (0-24)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-amber-400" />
                <span className="text-gray-600 dark:text-gray-400">Medium (25-49)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-orange-500" />
                <span className="text-gray-600 dark:text-gray-400">High (50-74)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-red-500" />
                <span className="text-gray-600 dark:text-gray-400">Critical (75+)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Heatmap View */}
      {activeView === 'heatmap' && heatmapGrid.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {t('forecast.weeklyHeatmap') || 'Weekly Risk Heatmap'}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('forecast.heatmapDesc') || 'Historical risk patterns by hour and day of week'}
            </p>
          </div>

          <div className="p-4 overflow-x-auto">
            <div className="min-w-[700px]">
              {/* Hour labels */}
              <div className="flex mb-2">
                <div className="w-16" />
                {Array.from({ length: 24 }, (_, i) => (
                  <div key={i} className="flex-1 text-center">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {i % 3 === 0 ? `${i}h` : ''}
                    </span>
                  </div>
                ))}
              </div>

              {/* Grid */}
              {heatmapGrid.map((row, dayIdx) => (
                <div key={dayIdx} className="flex mb-1 items-center">
                  <div className="w-16 pr-2 text-right">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {DAY_NAMES_SHORT[dayIdx]}
                    </span>
                  </div>
                  {row.map((cell, hourIdx) => (
                    <div
                      key={hourIdx}
                      className={`flex-1 h-8 mx-px rounded-sm cursor-pointer transition-all ${
                        cell ? getHeatmapColor(cell.risk_score) : 'bg-gray-200 dark:bg-gray-700'
                      }`}
                      onMouseEnter={() => setHoveredCell(cell)}
                      onMouseLeave={() => setHoveredCell(null)}
                    />
                  ))}
                </div>
              ))}

              {/* Hover tooltip */}
              {hoveredCell && (
                <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {hoveredCell.day_name} at {hoveredCell.hour}:00
                  </p>
                  <p className={`text-lg font-bold ${getRiskTextColor(hoveredCell.risk_level)}`}>
                    Risk Score: {hoveredCell.risk_score.toFixed(0)}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                    Level: {hoveredCell.risk_level}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Legend */}
          <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {t('forecast.basedOnHistory') || 'Based on 90 days of historical data'}
              </span>
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500">Low</span>
                <div className="flex h-3">
                  <div className="w-6 bg-green-400 rounded-l" />
                  <div className="w-6 bg-amber-400" />
                  <div className="w-6 bg-orange-500" />
                  <div className="w-6 bg-red-500 rounded-r" />
                </div>
                <span className="text-xs text-gray-500">High</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Daily Summary View */}
      {activeView === 'daily' && (
        <div className="space-y-4">
          {forecast.daily_forecasts.map((day, idx) => (
            <div
              key={day.date}
              className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border overflow-hidden ${getRiskBorderColor(day.overall_risk)}`}
            >
              <button
                onClick={() => setExpandedDay(expandedDay === idx ? null : idx)}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-12 rounded-full ${getRiskColor(day.overall_risk)}`} />
                  <div className="text-left">
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {day.day_of_week}, {day.date}
                    </p>
                    <p className={`text-sm ${getRiskTextColor(day.overall_risk)}`}>
                      {day.overall_risk.toUpperCase()} RISK • Score: {day.risk_score.toFixed(0)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right hidden sm:block">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Expected</p>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {day.expected_total_transactions} txns / {day.expected_fraud_count} fraud
                    </p>
                  </div>
                  {expandedDay === idx ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </button>

              {expandedDay === idx && (
                <div className="px-4 pb-4 pt-2 border-t border-gray-200 dark:border-gray-700">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                        Peak Risk Hours
                      </p>
                      <p className="font-semibold text-gray-900 dark:text-white mt-1">
                        {day.peak_hours.length > 0
                          ? day.peak_hours.map(h => `${h}:00`).join(', ')
                          : 'None identified'}
                      </p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <Shield className="w-4 h-4 text-green-500" />
                        Safe Hours
                      </p>
                      <p className="font-semibold text-gray-900 dark:text-white mt-1">
                        {day.safe_hours.length > 0
                          ? day.safe_hours.map(h => `${h}:00`).join(', ')
                          : 'None identified'}
                      </p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                        <Target className="w-4 h-4 text-purple-500" />
                        Expected Fraud Rate
                      </p>
                      <p className="font-semibold text-gray-900 dark:text-white mt-1">
                        {(day.expected_fraud_rate * 100).toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {day.alerts.length > 0 && (
                    <div className="space-y-2">
                      {day.alerts.map((alert, alertIdx) => (
                        <div
                          key={alertIdx}
                          className="flex items-center gap-2 p-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg text-sm text-amber-800 dark:text-amber-200"
                        >
                          <Bell className="w-4 h-4 flex-shrink-0" />
                          {alert}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Insights & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Insights */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <Info className="w-5 h-5 text-blue-500" />
            {t('forecast.insights') || 'Key Insights'}
          </h3>
          <div className="space-y-2">
            {forecast.insights.map((insight, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
              >
                <ChevronRight className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-blue-800 dark:text-blue-200">{insight}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-500" />
            {t('forecast.recommendations') || 'Recommendations'}
          </h3>
          <div className="space-y-2">
            {forecast.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg"
              >
                <span className="text-xl">{rec.icon}</span>
                <div>
                  <p className="font-medium text-purple-800 dark:text-purple-200 text-sm">
                    {rec.action}
                  </p>
                  <p className="text-xs text-purple-600 dark:text-purple-400 mt-0.5">
                    {rec.reason}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Model Accuracy */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>
          {t('forecast.modelInfo') || 'Forecast based on'}{' '}
          <span className="font-semibold text-gray-700 dark:text-gray-300">
            {forecast.model_accuracy.historical_predictions_analyzed.toLocaleString()}
          </span>{' '}
          {t('forecast.historicalPredictions') || 'historical predictions'} •{' '}
          {t('forecast.estimatedAccuracy') || 'Estimated accuracy'}:{' '}
          <span className="font-semibold text-gray-700 dark:text-gray-300">
            {(forecast.model_accuracy.estimated_accuracy * 100).toFixed(0)}%
          </span>{' '}
          ({forecast.model_accuracy.confidence_interval})
        </p>
      </div>
    </div>
  );
}
