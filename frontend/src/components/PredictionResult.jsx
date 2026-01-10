import { useState } from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, Gauge, Brain, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { useI18n } from '../i18n/index.jsx';
import FraudExplainer from './FraudExplainer';

function PredictionResult({ prediction }) {
  const { t } = useI18n();
  const [showExplainer, setShowExplainer] = useState(false);

  if (!prediction) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8">
        <div className="text-center">
          <Shield className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            {t('prediction.noPrediction') || 'No Prediction Yet'}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
            {t('prediction.enterDetails') || 'Enter transaction details and click Analyze to see results'}
          </p>
        </div>
      </div>
    );
  }

  const isFraud = prediction.is_fraud;
  const riskScore = prediction.risk_score;

  // Determine risk level color
  const getRiskColor = (score) => {
    if (score < 30) return 'text-green-600 dark:text-green-400';
    if (score < 70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getRiskBg = (score) => {
    if (score < 30) return 'bg-green-500';
    if (score < 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-4">
      {/* Main Result Card */}
      <div className={`bg-white dark:bg-gray-800 rounded-xl border-2 overflow-hidden ${
        isFraud
          ? 'border-red-300 dark:border-red-700'
          : 'border-green-300 dark:border-green-700'
      }`}>
        {/* Header */}
        <div className={`px-6 py-4 ${
          isFraud
            ? 'bg-red-50 dark:bg-red-950/50'
            : 'bg-green-50 dark:bg-green-950/50'
        }`}>
          <div className="flex items-center gap-3">
            {isFraud ? (
              <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
            ) : (
              <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
            )}
            <div>
              <h3 className={`text-xl font-bold ${
                isFraud
                  ? 'text-red-700 dark:text-red-300'
                  : 'text-green-700 dark:text-green-300'
              }`}>
                {isFraud
                  ? (t('prediction.fraudDetected') || 'Fraud Detected!')
                  : (t('prediction.legitimate') || 'Transaction Legitimate')
                }
              </h3>
              <p className={`text-sm ${
                isFraud
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-green-600 dark:text-green-400'
              }`}>
                {t('prediction.confidence') || 'Confidence'}: {prediction.confidence.toUpperCase()}
              </p>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="p-6 space-y-6">
          {/* Risk Score Gauge */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                <Gauge className="w-4 h-4" />
                {t('prediction.riskScore') || 'Risk Score'}
              </span>
              <span className={`text-2xl font-bold ${getRiskColor(riskScore)}`}>
                {riskScore}%
              </span>
            </div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${getRiskBg(riskScore)} transition-all duration-500`}
                style={{ width: `${riskScore}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500 mt-1">
              <span>{t('dashboard.low') || 'Low Risk'}</span>
              <span>{t('dashboard.medium') || 'Medium'}</span>
              <span>{t('dashboard.high') || 'High Risk'}</span>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('prediction.probability') || 'Fraud Probability'}
              </p>
              <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
                {(prediction.fraud_probability * 100).toFixed(2)}%
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {t('prediction.predictionTime') || 'Response Time'}
              </p>
              <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
                {prediction.prediction_time_ms.toFixed(1)}ms
              </p>
            </div>
          </div>

          {/* AI Explain Button */}
          <button
            onClick={() => setShowExplainer(!showExplainer)}
            className={`w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
              showExplainer
                ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                : 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:from-indigo-600 hover:to-purple-600 shadow-lg hover:shadow-xl'
            }`}
          >
            <Brain className="w-5 h-5" />
            <span>
              {showExplainer
                ? (t('explainer.hideAnalysis') || 'Hide AI Analysis')
                : (t('explainer.showAnalysis') || 'Explain with AI')
              }
            </span>
            {!showExplainer && <Sparkles className="w-4 h-4 animate-pulse" />}
            {showExplainer ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {/* Quick Recommendation */}
          {!showExplainer && (
            <div className={`p-4 rounded-lg ${
              isFraud
                ? 'bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50'
                : 'bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-900/50'
            }`}>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                {t('prediction.recommendation') || 'Recommendation'}
              </h4>
              <p className={`text-sm ${
                isFraud
                  ? 'text-red-700 dark:text-red-300'
                  : 'text-green-700 dark:text-green-300'
              }`}>
                {isFraud
                  ? (t('prediction.fraudRecommendation') || 'This transaction shows suspicious patterns. Recommend blocking and further investigation.')
                  : (t('prediction.legitimateRecommendation') || 'This transaction appears normal. No action required.')
                }
              </p>
            </div>
          )}
        </div>
      </div>

      {/* AI Explainer Panel */}
      {showExplainer && (
        <FraudExplainer
          prediction={prediction}
          onClose={() => setShowExplainer(false)}
        />
      )}
    </div>
  );
}

export default PredictionResult;
