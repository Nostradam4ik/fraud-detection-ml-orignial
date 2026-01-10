import { useState } from 'react';
import { predictFraud, getSampleLegitimate, getSampleFraud } from '../services/api';
import { Send, RefreshCw, Zap, AlertCircle } from 'lucide-react';
import { useI18n } from '../i18n/index.jsx';

function TransactionForm({ onPrediction, apiStatus }) {
  const { t } = useI18n();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    time: 0,
    amount: 100,
    v1: 0, v2: 0, v3: 0, v4: 0, v5: 0,
    v6: 0, v7: 0, v8: 0, v9: 0, v10: 0,
    v11: 0, v12: 0, v13: 0, v14: 0, v15: 0,
    v16: 0, v17: 0, v18: 0, v19: 0, v20: 0,
    v21: 0, v22: 0, v23: 0, v24: 0, v25: 0,
    v26: 0, v27: 0, v28: 0,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (apiStatus !== 'online') {
      setError(t('prediction.apiNotAvailable'));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await predictFraud(formData);
      onPrediction(result, formData);
    } catch (err) {
      setError(err.response?.data?.detail || t('prediction.failedPrediction'));
    } finally {
      setLoading(false);
    }
  };

  const loadSample = async (type) => {
    setLoading(true);
    setError(null);

    try {
      const sample = type === 'fraud'
        ? await getSampleFraud()
        : await getSampleLegitimate();
      setFormData(sample);
    } catch (err) {
      setError(t('prediction.failedLoadSample'));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0,
    }));
  };

  const vFields = Array.from({ length: 28 }, (_, i) => `v${i + 1}`);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('prediction.title')}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('prediction.subtitle')}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex gap-3">
        <button
          onClick={() => loadSample('legitimate')}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 transition-colors text-sm font-medium disabled:opacity-50"
        >
          <Zap className="w-4 h-4" />
          {t('prediction.legitimateSample')}
        </button>
        <button
          onClick={() => loadSample('fraud')}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors text-sm font-medium disabled:opacity-50"
        >
          <AlertCircle className="w-4 h-4" />
          {t('prediction.fraudSample')}
        </button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        {/* Main Fields */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('prediction.time')}
            </label>
            <input
              type="number"
              value={formData.time}
              onChange={(e) => handleInputChange('time', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              step="any"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('prediction.amount')}
            </label>
            <input
              type="number"
              value={formData.amount}
              onChange={(e) => handleInputChange('amount', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              step="any"
              min="0"
            />
          </div>
        </div>

        {/* V Features */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            {t('prediction.features')}
          </label>
          <div className="grid grid-cols-4 sm:grid-cols-7 gap-2 max-h-48 overflow-y-auto p-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
            {vFields.map((field) => (
              <div key={field} className="relative">
                <label className="absolute -top-1 left-2 text-[10px] text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-1 z-10">
                  {field.toUpperCase()}
                </label>
                <input
                  type="number"
                  value={formData[field]}
                  onChange={(e) => handleInputChange(field, e.target.value)}
                  className="w-full px-2 py-1.5 pt-3 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  step="any"
                />
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
            * {t('prediction.pcaNote')}
          </p>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || apiStatus !== 'online'}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin" />
              {t('prediction.analyzing')}
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              {t('prediction.analyze')}
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default TransactionForm;
