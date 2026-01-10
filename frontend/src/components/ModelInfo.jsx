import { useState, useEffect } from 'react';
import { getModelInfo, getFeatureImportance } from '../services/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import {
  Brain,
  Database,
  Target,
  TrendingUp,
  Award,
  AlertCircle,
} from 'lucide-react';

function ModelInfo() {
  const [modelInfo, setModelInfo] = useState(null);
  const [features, setFeatures] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [info, featureData] = await Promise.all([
          getModelInfo(),
          getFeatureImportance(),
        ]);
        setModelInfo(info);
        setFeatures(featureData);
      } catch (err) {
        setError('Failed to load model information. Make sure the model is trained.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-200 dark:border-blue-900 border-t-blue-600 dark:border-t-blue-400 rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-red-800 dark:text-red-300">Error Loading Model Info</h3>
            <p className="text-sm text-red-600 dark:text-red-400 mt-1">{error}</p>
            <p className="text-sm text-red-600 dark:text-red-400 mt-2">
              Run <code className="bg-red-100 dark:bg-red-900/50 px-1 rounded">python ml/train.py</code> to train the model.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Prepare feature importance data for chart
  const featureData = features
    ? Object.entries(features)
        .map(([name, importance]) => ({ name, importance }))
        .sort((a, b) => b.importance - a.importance)
        .slice(0, 10)
    : [];

  const metrics = [
    { label: 'Accuracy', value: modelInfo?.accuracy, icon: Target, color: 'text-blue-600 dark:text-blue-400' },
    { label: 'Precision', value: modelInfo?.precision, icon: Award, color: 'text-green-600 dark:text-green-400' },
    { label: 'Recall', value: modelInfo?.recall, icon: TrendingUp, color: 'text-purple-600 dark:text-purple-400' },
    { label: 'F1 Score', value: modelInfo?.f1_score, icon: Brain, color: 'text-orange-600 dark:text-orange-400' },
    { label: 'ROC-AUC', value: modelInfo?.roc_auc, icon: Database, color: 'text-cyan-600 dark:text-cyan-400' },
  ];

  // Custom tooltip for chart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-sm text-gray-900 dark:text-white font-medium">{payload[0].payload.name}</p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Importance: {(payload[0].value * 100).toFixed(2)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Model Information</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Details about the fraud detection machine learning model
        </p>
      </div>

      {/* Model Overview */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-3">
            <Brain className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {modelInfo?.model_name || 'Random Forest Classifier'}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">Version {modelInfo?.model_version || '1.0.0'}</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Training Samples</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {modelInfo?.training_samples?.toLocaleString() || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Fraud Samples</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {modelInfo?.fraud_samples?.toLocaleString() || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Features</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {modelInfo?.features_count || 30}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Performance Metrics</h3>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {metrics.map((metric) => (
              <div
                key={metric.label}
                className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center"
              >
                <metric.icon className={`w-6 h-6 ${metric.color} mx-auto mb-2`} />
                <p className="text-sm text-gray-500 dark:text-gray-400">{metric.label}</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
                  {metric.value ? (metric.value * 100).toFixed(1) + '%' : 'N/A'}
                </p>
              </div>
            ))}
          </div>

          {/* Metrics Explanation */}
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/50 rounded-lg">
            <h4 className="font-medium text-blue-900 dark:text-blue-300 mb-2">Understanding the Metrics</h4>
            <ul className="text-sm text-blue-800 dark:text-blue-300/90 space-y-1">
              <li><strong>Accuracy:</strong> Overall correctness of predictions</li>
              <li><strong>Precision:</strong> Of predicted frauds, how many are actually fraud</li>
              <li><strong>Recall:</strong> Of actual frauds, how many did we catch</li>
              <li><strong>F1 Score:</strong> Balance between precision and recall</li>
              <li><strong>ROC-AUC:</strong> Model's ability to distinguish between classes</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Feature Importance */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top 10 Feature Importance</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Features with highest influence on fraud detection
          </p>
        </div>

        <div className="p-6">
          {featureData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={featureData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
              >
                <XAxis type="number" domain={[0, 'auto']} stroke="#9ca3af" />
                <YAxis dataKey="name" type="category" width={50} stroke="#9ca3af" />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                  {featureData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index < 3 ? '#3b82f6' : '#93c5fd'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <p>Feature importance data not available</p>
            </div>
          )}
        </div>
      </div>

      {/* Dataset Info */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Dataset Information</h3>
        </div>

        <div className="p-6">
          <div className="prose prose-sm dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
            <p>
              This model is trained on the{' '}
              <a
                href="https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
              >
                Credit Card Fraud Detection
              </a>{' '}
              dataset from Kaggle.
            </p>
            <ul className="mt-4 space-y-2 text-gray-600 dark:text-gray-300">
              <li>284,807 total transactions</li>
              <li>492 fraudulent transactions (0.17%)</li>
              <li>Features V1-V28 are PCA-transformed (anonymized)</li>
              <li>Time and Amount are original features</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ModelInfo;
