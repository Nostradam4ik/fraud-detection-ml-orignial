import { useState, useEffect } from 'react';
import { getUserPredictionStats, getPredictionHistory, getTimeSeries } from '../services/api';
import { useI18n } from '../i18n/index.jsx';
import StatsChart from './StatsChart';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Download,
  RefreshCw,
  Zap,
  Target,
  DollarSign,
} from 'lucide-react';

function Dashboard() {
  const { t } = useI18n();
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  const fetchData = async () => {
    try {
      const [statsData, historyData, tsData] = await Promise.all([
        getUserPredictionStats(),
        getPredictionHistory(50),
        getTimeSeries('day', selectedPeriod).catch(() => ({ data: [] }))
      ]);
      setStats(statsData);
      setHistory(historyData);
      setTimeSeriesData(tsData.data || []);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [selectedPeriod]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Calculate additional metrics
  const fraudRate = stats?.fraud_rate ? (stats.fraud_rate * 100).toFixed(2) : '0.00';
  const totalAmount = history.reduce((sum, h) => sum + (h.amount || 0), 0);
  const avgRiskScore = history.length > 0
    ? (history.reduce((sum, h) => sum + (h.risk_score || 0), 0) / history.length).toFixed(1)
    : 0;
  const highRiskCount = history.filter(h => h.risk_score >= 70).length;

  // Trend calculation
  const recentFraudRate = history.slice(0, 10).filter(h => h.is_fraud).length / Math.max(history.slice(0, 10).length, 1);
  const olderFraudRate = history.slice(10, 20).filter(h => h.is_fraud).length / Math.max(history.slice(10, 20).length, 1);
  const trend = recentFraudRate > olderFraudRate ? 'up' : recentFraudRate < olderFraudRate ? 'down' : 'stable';

  const statCards = [
    { title: t('dashboard.totalPredictions'), value: stats?.total_predictions || 0, icon: Activity, color: 'blue', change: null },
    { title: t('dashboard.fraudDetected'), value: stats?.fraud_detected || 0, icon: AlertTriangle, color: 'red', change: trend === 'up' ? '+' : trend === 'down' ? '-' : null },
    { title: t('dashboard.legitimate'), value: stats?.legitimate_detected || 0, icon: CheckCircle, color: 'green', change: null },
    { title: t('dashboard.avgResponseTime'), value: `${stats?.average_response_time_ms?.toFixed(1) || 0}ms`, icon: Zap, color: 'purple', change: null },
  ];

  const additionalStats = [
    { title: t('dashboard.totalVolume'), value: `$${totalAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, icon: DollarSign, color: 'emerald' },
    { title: t('dashboard.avgRiskScore'), value: avgRiskScore, icon: Target, color: 'orange' },
    { title: t('dashboard.highRisk'), value: highRiskCount, icon: AlertTriangle, color: 'amber' },
    { title: t('dashboard.fraudRate'), value: `${fraudRate}%`, icon: parseFloat(fraudRate) > 1 ? TrendingUp : TrendingDown, color: parseFloat(fraudRate) > 1 ? 'red' : 'green' },
  ];

  // Export to CSV
  const exportToCSV = () => {
    if (history.length === 0) return;
    const headers = ['ID', 'Time', 'Amount', 'Is Fraud', 'Probability', 'Confidence', 'Risk Score', 'Response Time (ms)', 'Date'];
    const rows = history.map(p => [p.id, p.time, p.amount, p.is_fraud ? 'Yes' : 'No', (p.fraud_probability * 100).toFixed(2) + '%', p.confidence, p.risk_score, p.prediction_time_ms, new Date(p.created_at).toLocaleString()]);
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fraud_predictions_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Hourly distribution data
  const hourlyData = Array(24).fill(0).map((_, hour) => ({
    hour: `${hour}:00`,
    predictions: history.filter(h => new Date(h.created_at).getHours() === hour).length,
    fraud: history.filter(h => new Date(h.created_at).getHours() === hour && h.is_fraud).length
  }));

  // Risk distribution
  const riskDistribution = [
    { name: 'Low (0-25)', value: history.filter(h => h.risk_score < 25).length, fill: '#22c55e' },
    { name: 'Medium (25-50)', value: history.filter(h => h.risk_score >= 25 && h.risk_score < 50).length, fill: '#eab308' },
    { name: 'High (50-75)', value: history.filter(h => h.risk_score >= 50 && h.risk_score < 75).length, fill: '#f97316' },
    { name: 'Critical (75+)', value: history.filter(h => h.risk_score >= 75).length, fill: '#ef4444' },
  ];

  const colorMap = {
    blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', icon: 'text-blue-500' },
    red: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400', icon: 'text-red-500' },
    green: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', icon: 'text-green-500' },
    purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400', icon: 'text-purple-500' },
    emerald: { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400', icon: 'text-emerald-500' },
    orange: { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-600 dark:text-orange-400', icon: 'text-orange-500' },
    amber: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600 dark:text-amber-400', icon: 'text-amber-500' },
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-medium text-gray-900 dark:text-white mb-1">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{t('dashboard.title')}</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('dashboard.subtitle')}</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={selectedPeriod} onChange={(e) => setSelectedPeriod(parseInt(e.target.value))} className="px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-700 dark:text-gray-300">
            <option value={7}>{t('dashboard.last7Days')}</option>
            <option value={14}>{t('dashboard.last14Days')}</option>
            <option value={30}>{t('dashboard.last30Days')}</option>
            <option value={60}>{t('dashboard.last60Days')}</option>
            <option value={90}>{t('dashboard.last90Days')}</option>
          </select>
          <button onClick={handleRefresh} disabled={refreshing} className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 text-gray-600 dark:text-gray-400 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:inline">{t('common.refresh')}</span>
          </button>
          <button onClick={exportToCSV} disabled={history.length === 0} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
            <Download className="w-4 h-4" />
            <span className="text-sm font-medium hidden sm:inline">{t('dashboard.exportCSV')}</span>
          </button>
        </div>
      </div>

      {/* Main Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const colors = colorMap[stat.color];
          return (
            <div key={stat.title} className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className={`p-2.5 rounded-lg ${colors.bg}`}>
                  <stat.icon className={`w-5 h-5 ${colors.icon}`} />
                </div>
                {loading && <div className="w-4 h-4 border-2 border-gray-300 dark:border-gray-600 border-t-blue-600 rounded-full animate-spin" />}
                {stat.change && <span className={`text-xs font-medium ${stat.change === '+' ? 'text-red-500' : 'text-green-500'}`}>{stat.change === '+' ? '↑' : '↓'}</span>}
              </div>
              <div className="mt-3">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.title}</p>
                <p className={`text-2xl font-bold mt-1 ${colors.text}`}>{typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {additionalStats.map((stat) => {
          const colors = colorMap[stat.color];
          return (
            <div key={stat.title} className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${colors.bg}`}>
                  <stat.icon className={`w-4 h-4 ${colors.icon}`} />
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{stat.title}</p>
                  <p className={`text-lg font-semibold ${colors.text}`}>{stat.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Time Series Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-gray-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('dashboard.predictionsOverTime')}</h3>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded"></span> {t('dashboard.total')}</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded"></span> {t('dashboard.fraud')}</span>
            </div>
          </div>
          {timeSeriesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={timeSeriesData}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                <XAxis dataKey="period" className="text-xs" tick={{ fill: '#9ca3af' }} />
                <YAxis className="text-xs" tick={{ fill: '#9ca3af' }} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="total" stroke="#3b82f6" fill="url(#colorTotal)" name="Total" />
                <Area type="monotone" dataKey="fraud" stroke="#ef4444" fill="url(#colorFraud)" name="Fraud" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              <p>{t('dashboard.noTimeSeriesData')}</p>
            </div>
          )}
        </div>

        {/* Prediction Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-5 h-5 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('dashboard.fraudVsLegitimate')}</h3>
          </div>
          <StatsChart fraudCount={stats?.fraud_detected || 0} legitimateCount={stats?.legitimate_detected || 0} />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-6">
            <Target className="w-5 h-5 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('dashboard.riskDistribution')}</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={riskDistribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis type="number" tick={{ fill: '#9ca3af' }} />
              <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} name="Count">
                {riskDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Hourly Activity */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-6">
            <Clock className="w-5 h-5 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('dashboard.hourlyActivity')}</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis dataKey="hour" tick={{ fill: '#9ca3af', fontSize: 10 }} interval={2} />
              <YAxis tick={{ fill: '#9ca3af' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="predictions" fill="#3b82f6" name="Predictions" radius={[4, 4, 0, 0]} />
              <Bar dataKey="fraud" fill="#ef4444" name="Fraud" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('dashboard.recentActivity')}</h3>
          </div>
          <span className="text-sm text-gray-500 dark:text-gray-400">{history.length} {t('dashboard.predictions').toLowerCase()}</span>
        </div>
        {history.length === 0 ? (
          <div className="text-center py-12">
            <Activity className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">{t('dashboard.noPredictionsYet')}</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">{t('dashboard.goToAnalyzer')}</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {history.slice(0, 15).map((item) => (
              <div key={item.id} className={`flex items-center justify-between p-3 rounded-lg ${item.is_fraud ? 'bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50' : 'bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-900/50'}`}>
                <div className="flex items-center gap-3">
                  {item.is_fraud ? <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" /> : <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />}
                  <div>
                    <p className={`text-sm font-medium ${item.is_fraud ? 'text-red-800 dark:text-red-200' : 'text-green-800 dark:text-green-200'}`}>{item.is_fraud ? t('dashboard.fraudDetected') : t('dashboard.legitimate')}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-300">${item.amount?.toFixed(2)} | Risk: {item.risk_score}% | {item.prediction_time_ms?.toFixed(1)}ms</p>
                  </div>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">{new Date(item.created_at).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* System Status */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('dashboard.systemStatus')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">{t('dashboard.apiStatus')}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('dashboard.healthy')}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <Clock className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">{t('dashboard.uptime')}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">99.9%</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <Activity className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">{t('dashboard.predictions')}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{stats?.total_predictions || 0} {t('dashboard.total').toLowerCase()}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <BarChart3 className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">{t('dashboard.model')}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Random Forest v1.0</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
