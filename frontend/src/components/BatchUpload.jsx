import { useState, useRef } from 'react';
import { Upload, FileText, Download, AlertTriangle, Check, X, Loader } from 'lucide-react';
import { uploadCSV } from '../services/api';
import { useI18n } from '../i18n/index.jsx';

export default function BatchUpload() {
  const { t } = useI18n();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    if (!selectedFile.name.endsWith('.csv')) {
      setError(t('batch.selectCsvFile'));
      return;
    }
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError(t('batch.fileTooLarge'));
      return;
    }
    setFile(selectedFile);
    setError(null);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await uploadCSV(file);

      // Get metadata from headers
      const batchId = response.headers['x-batch-id'];
      const totalRows = response.headers['x-total-rows'];
      const fraudCount = response.headers['x-fraud-count'];
      const legitimateCount = response.headers['x-legitimate-count'];

      // Create download URL
      const blob = new Blob([response.data], { type: 'text/csv' });
      const downloadUrl = URL.createObjectURL(blob);

      setResult({
        batchId,
        totalRows: parseInt(totalRows),
        fraudCount: parseInt(fraudCount),
        legitimateCount: parseInt(legitimateCount),
        downloadUrl,
        filename: `predictions_${batchId?.substring(0, 8) || 'batch'}.csv`
      });
    } catch (err) {
      console.error('Upload error:', err);
      // Try to get error message from different sources
      let errorMsg = 'Failed to process file';
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.response?.data) {
        // If response.data is a Blob, try to read it
        if (err.response.data instanceof Blob) {
          try {
            const text = await err.response.data.text();
            const json = JSON.parse(text);
            errorMsg = json.detail || text;
          } catch {
            errorMsg = 'Server error';
          }
        } else {
          errorMsg = JSON.stringify(err.response.data);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
    }

    setLoading(false);
  };

  const resetForm = () => {
    setFile(null);
    setResult(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('batch.title')}</h1>
        <p className="text-gray-600 dark:text-gray-400">{t('batch.subtitle')}</p>
      </div>

      {/* Upload Area */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            onChange={handleChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <Upload className="w-8 h-8 text-gray-400" />
            </div>

            {file ? (
              <div className="flex items-center justify-center gap-2 text-gray-900 dark:text-white">
                <FileText className="w-5 h-5 text-blue-500" />
                <span className="font-medium">{file.name}</span>
                <span className="text-gray-500 dark:text-gray-400">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    resetForm();
                  }}
                  className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            ) : (
              <>
                <p className="text-gray-600 dark:text-gray-400">
                  <span className="text-blue-600 dark:text-blue-400 font-medium">{t('batch.clickToUpload')}</span>
                  {' '}{t('batch.orDragDrop')}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500">
                  {t('batch.csvUpTo')} ({t('batch.maxRows')})
                </p>
              </>
            )}
          </div>
        </div>

        {/* CSV Format Info */}
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">{t('batch.requiredFormat')}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            {t('batch.requiredColumns')}
          </p>
          <code className="text-xs bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded text-gray-800 dark:text-gray-200">
            time, amount, v1, v2, v3, ... v28
          </code>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-400">
            <AlertTriangle className="w-5 h-5" />
            {error}
          </div>
        )}

        {/* Upload Button */}
        {file && !result && (
          <button
            onClick={handleUpload}
            disabled={loading}
            className="mt-4 w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                {t('batch.processing')}
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                {t('batch.analyzeTransactions')}
              </>
            )}
          </button>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-4">
            <Check className="w-6 h-6 text-green-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('batch.analysisComplete')}</h3>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{result.totalRows}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('batch.totalRows')}</p>
            </div>
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg text-center">
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">{result.fraudCount}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('batch.fraudCount')}</p>
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{result.legitimateCount}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('batch.legitimateCount')}</p>
            </div>
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {((result.fraudCount / result.totalRows) * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{t('batch.fraudRate')}</p>
            </div>
          </div>

          {/* Download Button */}
          <div className="flex gap-3">
            <a
              href={result.downloadUrl}
              download={result.filename}
              className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              {t('batch.downloadCSV')}
            </a>
            <button
              onClick={resetForm}
              className="px-6 py-3 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500"
            >
              {t('batch.uploadAnother')}
            </button>
          </div>

          <p className="mt-3 text-sm text-gray-500 dark:text-gray-400 text-center">
            {t('batch.batchId')}: {result.batchId}
          </p>
        </div>
      )}
    </div>
  );
}
