import { useMemo } from 'react';
import { Tooltip } from 'recharts';

export default function HeatmapChart({ data, title, xLabels, yLabels }) {
  // Generate color based on value (0-1)
  const getColor = (value) => {
    if (value === null || value === undefined) return 'bg-gray-100 dark:bg-gray-700';

    const intensity = Math.min(Math.max(value, 0), 1);

    if (intensity < 0.2) return 'bg-green-100 dark:bg-green-900/30';
    if (intensity < 0.4) return 'bg-green-300 dark:bg-green-700/50';
    if (intensity < 0.6) return 'bg-yellow-300 dark:bg-yellow-700/50';
    if (intensity < 0.8) return 'bg-orange-400 dark:bg-orange-600/50';
    return 'bg-red-500 dark:bg-red-600/70';
  };

  const getTextColor = (value) => {
    if (value === null || value === undefined) return 'text-gray-400';
    if (value >= 0.6) return 'text-white';
    return 'text-gray-700 dark:text-gray-300';
  };

  // Sample data if none provided
  const heatmapData = useMemo(() => {
    if (data) return data;

    // Generate sample hourly fraud rate data
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    return days.map(day =>
      hours.map(() => Math.random() * 0.3 + (day === 'Sat' || day === 'Sun' ? 0.1 : 0))
    );
  }, [data]);

  const xAxisLabels = xLabels || Array.from({ length: 24 }, (_, i) => `${i}:00`);
  const yAxisLabels = yLabels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {title}
        </h3>
      )}

      <div className="overflow-x-auto">
        <div className="min-w-[600px]">
          {/* X-axis labels */}
          <div className="flex ml-16">
            {xAxisLabels.filter((_, i) => i % 3 === 0).map((label, i) => (
              <div
                key={i}
                className="flex-1 text-xs text-gray-500 dark:text-gray-400 text-center"
                style={{ minWidth: '36px' }}
              >
                {label}
              </div>
            ))}
          </div>

          {/* Heatmap grid */}
          <div className="flex flex-col gap-1 mt-2">
            {heatmapData.map((row, rowIndex) => (
              <div key={rowIndex} className="flex items-center gap-1">
                {/* Y-axis label */}
                <div className="w-14 text-sm text-gray-500 dark:text-gray-400 text-right pr-2">
                  {yAxisLabels[rowIndex]}
                </div>

                {/* Row cells */}
                <div className="flex gap-0.5 flex-1">
                  {row.map((value, colIndex) => (
                    <div
                      key={colIndex}
                      className={`relative group flex-1 h-8 rounded-sm ${getColor(value)} cursor-pointer transition-transform hover:scale-110 hover:z-10`}
                      title={`${yAxisLabels[rowIndex]} ${xAxisLabels[colIndex]}: ${(value * 100).toFixed(1)}%`}
                    >
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 pointer-events-none">
                        <div className="font-medium">{yAxisLabels[rowIndex]} {xAxisLabels[colIndex]}</div>
                        <div>Fraud Rate: {(value * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center gap-4 mt-6">
            <span className="text-xs text-gray-500 dark:text-gray-400">Low</span>
            <div className="flex gap-1">
              <div className="w-6 h-4 bg-green-100 dark:bg-green-900/30 rounded-sm" />
              <div className="w-6 h-4 bg-green-300 dark:bg-green-700/50 rounded-sm" />
              <div className="w-6 h-4 bg-yellow-300 dark:bg-yellow-700/50 rounded-sm" />
              <div className="w-6 h-4 bg-orange-400 dark:bg-orange-600/50 rounded-sm" />
              <div className="w-6 h-4 bg-red-500 dark:bg-red-600/70 rounded-sm" />
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">High</span>
          </div>
        </div>
      </div>
    </div>
  );
}
