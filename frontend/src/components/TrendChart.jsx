import { useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, Calendar } from 'lucide-react';

export default function TrendChart({
  data,
  title,
  dataKeys = ['value'],
  colors = ['#3B82F6', '#10B981', '#F59E0B'],
  type = 'line',
  showBrush = false,
  height = 300
}) {
  const [timeRange, setTimeRange] = useState('7d');

  // Generate sample data if none provided
  const chartData = useMemo(() => {
    if (data) return data;

    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    return Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i - 1));

      return {
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        predictions: Math.floor(Math.random() * 500 + 200),
        fraudDetected: Math.floor(Math.random() * 30 + 5),
        fraudRate: Math.random() * 0.08 + 0.02
      };
    });
  }, [data, timeRange]);

  // Calculate trend
  const trend = useMemo(() => {
    if (!chartData || chartData.length < 2) return { direction: 'stable', percentage: 0 };

    const firstHalf = chartData.slice(0, Math.floor(chartData.length / 2));
    const secondHalf = chartData.slice(Math.floor(chartData.length / 2));

    const firstAvg = firstHalf.reduce((sum, d) => sum + (d.fraudRate || 0), 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, d) => sum + (d.fraudRate || 0), 0) / secondHalf.length;

    const change = ((secondAvg - firstAvg) / firstAvg) * 100;

    return {
      direction: change > 5 ? 'up' : change < -5 ? 'down' : 'stable',
      percentage: Math.abs(change).toFixed(1)
    };
  }, [chartData]);

  const TrendIcon = trend.direction === 'up' ? TrendingUp : trend.direction === 'down' ? TrendingDown : Minus;
  const trendColor = trend.direction === 'up' ? 'text-red-500' : trend.direction === 'down' ? 'text-green-500' : 'text-gray-500';

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null;

    return (
      <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        <p className="font-medium text-gray-900 dark:text-white mb-2">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-600 dark:text-gray-400">{entry.name}:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {typeof entry.value === 'number' && entry.value < 1
                ? `${(entry.value * 100).toFixed(2)}%`
                : entry.value?.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const Chart = type === 'area' ? AreaChart : LineChart;
  const DataComponent = type === 'area' ? Area : Line;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {title}
            </h3>
          )}
          <div className={`flex items-center gap-1 mt-1 ${trendColor}`}>
            <TrendIcon className="w-4 h-4" />
            <span className="text-sm font-medium">
              {trend.direction === 'stable' ? 'Stable' : `${trend.percentage}% ${trend.direction === 'up' ? 'increase' : 'decrease'}`}
            </span>
          </div>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {['7d', '30d', '90d'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                timeRange === range
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <Chart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <defs>
            {colors.map((color, index) => (
              <linearGradient key={index} id={`gradient-${index}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => value >= 1 ? value.toLocaleString() : `${(value * 100).toFixed(0)}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => <span className="text-gray-600 dark:text-gray-400">{value}</span>}
          />

          {type === 'area' ? (
            <>
              <Area
                type="monotone"
                dataKey="predictions"
                name="Predictions"
                stroke={colors[0]}
                fill={`url(#gradient-0)`}
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="fraudDetected"
                name="Fraud Detected"
                stroke={colors[1]}
                fill={`url(#gradient-1)`}
                strokeWidth={2}
              />
            </>
          ) : (
            <>
              <Line
                type="monotone"
                dataKey="predictions"
                name="Predictions"
                stroke={colors[0]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="fraudDetected"
                name="Fraud Detected"
                stroke={colors[1]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
            </>
          )}

          {showBrush && (
            <Brush
              dataKey="date"
              height={30}
              stroke="#3B82F6"
              fill="#1F2937"
              tickFormatter={(value) => value}
            />
          )}
        </Chart>
      </ResponsiveContainer>
    </div>
  );
}
