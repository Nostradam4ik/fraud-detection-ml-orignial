import { useState, useEffect } from 'react';
import {
  Brain,
  AlertTriangle,
  Shield,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  TrendingUp,
  TrendingDown,
  Info,
  XCircle,
  Eye,
  Radio,
  Ban,
  RefreshCw,
  Sparkles,
  BarChart3,
  Target,
  Clock,
  DollarSign,
  MapPin,
  Zap,
  Store,
  Smartphone,
  Search,
  Activity
} from 'lucide-react';
import { useI18n } from '../i18n/index.jsx';

// API call to get explanation
const getExplanation = async (token, data) => {
  const response = await fetch('/api/v1/explain', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to get explanation');
  return response.json();
};

// Icon mapping
const getCategoryIcon = (category) => {
  const icons = {
    'amount': DollarSign,
    'timing': Clock,
    'velocity': Zap,
    'location': MapPin,
    'merchant': Store,
    'device': Smartphone,
    'behavior': Search,
    'pattern': Activity
  };
  return icons[category] || BarChart3;
};

const getActionIcon = (actionType) => {
  const icons = {
    'block': Ban,
    'review': Eye,
    'monitor': Radio,
    'allow': CheckCircle,
    'verify': Shield
  };
  return icons[actionType] || Info;
};

const getSeverityColor = (severity) => {
  const colors = {
    'critical': 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800',
    'high': 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800',
    'medium': 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800',
    'low': 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800'
  };
  return colors[severity] || colors.medium;
};

const getVerdictStyle = (verdict) => {
  const styles = {
    'FRAUD': {
      bg: 'bg-red-500',
      text: 'text-white',
      icon: XCircle,
      glow: 'shadow-red-500/50'
    },
    'SUSPICIOUS': {
      bg: 'bg-orange-500',
      text: 'text-white',
      icon: AlertTriangle,
      glow: 'shadow-orange-500/50'
    },
    'LEGITIMATE': {
      bg: 'bg-green-500',
      text: 'text-white',
      icon: CheckCircle,
      glow: 'shadow-green-500/50'
    }
  };
  return styles[verdict] || styles.SUSPICIOUS;
};

export default function FraudExplainer({ prediction, predictionId, onClose }) {
  const { t } = useI18n();
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    riskFactors: true,
    features: false,
    recommendations: true,
    comparison: false
  });

  useEffect(() => {
    loadExplanation();
  }, [prediction, predictionId]);

  const loadExplanation = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const data = predictionId
        ? { prediction_id: predictionId }
        : {
            amount: prediction?.amount,
            risk_score: prediction?.risk_score,
            fraud_probability: prediction?.fraud_probability,
            is_fraud: prediction?.is_fraud,
            shap_values: prediction?.shap_values,
            time: prediction?.time
          };

      const result = await getExplanation(token, data);
      setExplanation(result);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <Brain className="w-16 h-16 text-indigo-500 animate-pulse" />
            <Sparkles className="w-6 h-6 text-amber-400 absolute -top-1 -right-1 animate-bounce" />
          </div>
          <p className="text-gray-600 dark:text-gray-400 font-medium">
            {t('explainer.analyzing') || 'AI is analyzing the transaction...'}
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
            onClick={loadExplanation}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            {t('common.retry') || 'Retry'}
          </button>
        </div>
      </div>
    );
  }

  if (!explanation) return null;

  const verdictStyle = getVerdictStyle(explanation.verdict);
  const VerdictIcon = verdictStyle.icon;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">
                {t('explainer.title') || 'AI Fraud Analysis'}
              </h2>
              <p className="text-indigo-100 text-sm">
                {t('explainer.subtitle') || 'Intelligent explanation powered by ML'}
              </p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg text-white transition"
            >
              <XCircle className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Verdict Banner */}
      <div className={`${verdictStyle.bg} px-6 py-4 shadow-lg ${verdictStyle.glow}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <VerdictIcon className={`w-10 h-10 ${verdictStyle.text}`} />
            <div>
              <p className={`text-2xl font-bold ${verdictStyle.text}`}>
                {explanation.verdict}
              </p>
              <p className={`text-sm opacity-90 ${verdictStyle.text}`}>
                {explanation.summary}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${verdictStyle.text}`}>
              {explanation.confidence_percentage.toFixed(0)}%
            </div>
            <p className={`text-sm opacity-90 ${verdictStyle.text}`}>
              {explanation.confidence_level} confidence
            </p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Main Explanation */}
        <div className="prose dark:prose-invert max-w-none">
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 border-l-4 border-indigo-500">
            <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
              {explanation.main_explanation.replace(/\*\*/g, '')}
            </p>
          </div>
        </div>

        {/* Risk Factors Section */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('riskFactors')}
            className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          >
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              <span className="font-semibold text-gray-900 dark:text-white">
                {t('explainer.riskFactors') || 'Risk Factors'} ({explanation.risk_factors.length})
              </span>
            </div>
            {expandedSections.riskFactors ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </button>

          {expandedSections.riskFactors && (
            <div className="p-4 space-y-3">
              {explanation.risk_factors.map((factor, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border ${getSeverityColor(factor.severity)}`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{factor.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold">{factor.category}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full uppercase font-medium
                          ${factor.severity === 'critical' ? 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200' : ''}
                          ${factor.severity === 'high' ? 'bg-orange-200 text-orange-800 dark:bg-orange-800 dark:text-orange-200' : ''}
                          ${factor.severity === 'medium' ? 'bg-amber-200 text-amber-800 dark:bg-amber-800 dark:text-amber-200' : ''}
                          ${factor.severity === 'low' ? 'bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-200' : ''}
                        `}>
                          {factor.severity}
                        </span>
                      </div>
                      <p className="text-sm">{factor.description}</p>
                      <p className="text-xs opacity-75 mt-1">{factor.technical_detail}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Feature Contributions Section */}
        {explanation.feature_contributions.length > 0 && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => toggleSection('features')}
              className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-indigo-500" />
                <span className="font-semibold text-gray-900 dark:text-white">
                  {t('explainer.featureContributions') || 'Feature Analysis'} ({explanation.feature_contributions.length})
                </span>
              </div>
              {expandedSections.features ? (
                <ChevronUp className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              )}
            </button>

            {expandedSections.features && (
              <div className="p-4 space-y-3">
                {explanation.feature_contributions.map((feature, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg"
                  >
                    <span className="text-xl">{feature.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {feature.feature}
                        </span>
                        <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full
                          ${feature.contribution === 'increases'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                            : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                          }`}
                        >
                          {feature.contribution === 'increases' ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {feature.contribution} risk
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full
                          ${feature.impact === 'high' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' : ''}
                          ${feature.impact === 'medium' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : ''}
                          ${feature.impact === 'low' ? 'bg-gray-100 text-gray-700 dark:bg-gray-600 dark:text-gray-300' : ''}
                        `}>
                          {feature.impact} impact
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {feature.human_readable}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Recommendations Section */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('recommendations')}
            className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          >
            <div className="flex items-center gap-3">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              <span className="font-semibold text-gray-900 dark:text-white">
                {t('explainer.recommendations') || 'Recommended Actions'} ({explanation.recommended_actions.length})
              </span>
            </div>
            {expandedSections.recommendations ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </button>

          {expandedSections.recommendations && (
            <div className="p-4 space-y-3">
              {explanation.recommended_actions.map((action, idx) => {
                const ActionIcon = getActionIcon(action.action_type);
                return (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border-2 ${
                      action.action_type === 'block' ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20' :
                      action.action_type === 'review' ? 'border-orange-300 bg-orange-50 dark:border-orange-700 dark:bg-orange-900/20' :
                      action.action_type === 'monitor' ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-900/20' :
                      'border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-900/20'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-full ${
                        action.action_type === 'block' ? 'bg-red-200 dark:bg-red-800' :
                        action.action_type === 'review' ? 'bg-orange-200 dark:bg-orange-800' :
                        action.action_type === 'monitor' ? 'bg-blue-200 dark:bg-blue-800' :
                        'bg-green-200 dark:bg-green-800'
                      }`}>
                        <ActionIcon className={`w-5 h-5 ${
                          action.action_type === 'block' ? 'text-red-700 dark:text-red-300' :
                          action.action_type === 'review' ? 'text-orange-700 dark:text-orange-300' :
                          action.action_type === 'monitor' ? 'text-blue-700 dark:text-blue-300' :
                          'text-green-700 dark:text-green-300'
                        }`} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-bold text-gray-500 dark:text-gray-400">
                            #{action.priority}
                          </span>
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {action.action}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {action.reason}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Comparison Section */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('comparison')}
            className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          >
            <div className="flex items-center gap-3">
              <Target className="w-5 h-5 text-purple-500" />
              <span className="font-semibold text-gray-900 dark:text-white">
                {t('explainer.comparison') || 'Comparative Analysis'}
              </span>
            </div>
            {expandedSections.comparison ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </button>

          {expandedSections.comparison && (
            <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Amount Comparison */}
              <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <DollarSign className="w-5 h-5 text-green-500" />
                  <span className="font-medium text-gray-900 dark:text-white">Amount</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">vs Average</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {explanation.comparison.amount_comparison.vs_average}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Percentile</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {explanation.comparison.amount_comparison.percentile}th
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2 mt-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
                      style={{ width: `${explanation.comparison.amount_comparison.percentile}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Risk Comparison */}
              <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-orange-500" />
                  <span className="font-medium text-gray-900 dark:text-white">Risk</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">vs Average</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {explanation.comparison.risk_comparison.vs_average}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Percentile</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {explanation.comparison.risk_comparison.percentile}th
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2 mt-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        explanation.comparison.risk_comparison.percentile >= 75 ? 'bg-red-500' :
                        explanation.comparison.risk_comparison.percentile >= 50 ? 'bg-orange-500' :
                        explanation.comparison.risk_comparison.percentile >= 25 ? 'bg-amber-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${explanation.comparison.risk_comparison.percentile}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Probability Context */}
              <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Target className="w-5 h-5 text-purple-500" />
                  <span className="font-medium text-gray-900 dark:text-white">Probability</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">vs Baseline</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {explanation.comparison.probability_context.relative_to_baseline}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Confidence</span>
                    <span className={`font-semibold px-2 py-0.5 rounded text-xs uppercase ${
                      explanation.comparison.probability_context.confidence_band === 'high'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                        : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                    }`}>
                      {explanation.comparison.probability_context.confidence_band}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Detailed Explanation */}
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700/50 dark:to-gray-700/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-blue-500" />
            <span className="font-semibold text-gray-900 dark:text-white">
              {t('explainer.detailedAnalysis') || 'Detailed Analysis'}
            </span>
          </div>
          <div className="prose dark:prose-invert prose-sm max-w-none">
            {explanation.detailed_explanation.split('\n\n').map((paragraph, idx) => (
              <p key={idx} className="text-gray-700 dark:text-gray-300 mb-3 last:mb-0">
                {paragraph.replace(/\*\*/g, '')}
              </p>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
          <span>Model v{explanation.model_version}</span>
          <span>Generated: {new Date(explanation.explanation_generated_at).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
