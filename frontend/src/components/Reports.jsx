import { useState } from 'react';
import {
  FileText,
  Download,
  Calendar,
  BarChart2,
  PieChart,
  TrendingUp,
  AlertTriangle,
  Loader,
  Check,
  FileSpreadsheet,
  Table
} from 'lucide-react';
import {
  downloadFraudReport,
  downloadBatchReport,
  downloadTrendAnalysisReport,
  downloadHighRiskReport,
  downloadModelPerformanceReport,
  downloadExcelReport,
  downloadExcelFraudOnly,
  downloadExcelHighRisk,
  downloadCSVExport
} from '../services/api';
import { useI18n } from '../i18n/index.jsx';

export default function Reports() {
  const { t } = useI18n();
  const [loading, setLoading] = useState({});
  const [message, setMessage] = useState(null);
  const [selectedDays, setSelectedDays] = useState(30);
  const [batchId, setBatchId] = useState('');
  const [riskThreshold, setRiskThreshold] = useState(50);

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleDownload = async (type) => {
    setLoading({ ...loading, [type]: true });
    try {
      let response;
      let filename;

      switch (type) {
        case 'fraud-summary':
          response = await downloadFraudReport(selectedDays);
          filename = `fraud_summary_${selectedDays}days_${new Date().toISOString().split('T')[0]}.pdf`;
          break;
        case 'trends':
          response = await downloadTrendAnalysisReport(selectedDays);
          filename = `trend_analysis_${selectedDays}days_${new Date().toISOString().split('T')[0]}.pdf`;
          break;
        case 'high-risk':
          response = await downloadHighRiskReport(selectedDays, riskThreshold);
          filename = `high_risk_${riskThreshold}plus_${new Date().toISOString().split('T')[0]}.pdf`;
          break;
        case 'performance':
          response = await downloadModelPerformanceReport();
          filename = `model_performance_${new Date().toISOString().split('T')[0]}.pdf`;
          break;
        case 'batch':
          if (!batchId.trim()) {
            showMessage(t('reports.pleaseEnterBatchId'), 'error');
            setLoading({ ...loading, [type]: false });
            return;
          }
          response = await downloadBatchReport(batchId);
          filename = `batch_report_${batchId.substring(0, 8)}.pdf`;
          break;
        default:
          return;
      }

      // Create download
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);

      showMessage(`${t('reports.reportDownloaded')}: ${filename}`);
    } catch (error) {
      console.error('Download failed:', error);
      showMessage(error.response?.data?.detail || t('reports.failedDownload'), 'error');
    }
    setLoading({ ...loading, [type]: false });
  };

  const reportTypes = [
    {
      id: 'fraud-summary',
      titleKey: 'reports.fraudSummary',
      descKey: 'reports.fraudSummaryDesc',
      icon: PieChart,
      color: 'blue',
      hasDateRange: true
    },
    {
      id: 'trends',
      titleKey: 'reports.trendAnalysis',
      descKey: 'reports.trendAnalysisDesc',
      icon: TrendingUp,
      color: 'green',
      hasDateRange: true
    },
    {
      id: 'high-risk',
      titleKey: 'reports.highRisk',
      descKey: 'reports.highRiskDesc',
      icon: AlertTriangle,
      color: 'red',
      hasDateRange: true,
      hasThreshold: true
    },
    {
      id: 'performance',
      titleKey: 'reports.modelPerformance',
      descKey: 'reports.modelPerformanceDesc',
      icon: BarChart2,
      color: 'purple'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('reports.title')}</h1>
        <p className="text-gray-600 dark:text-gray-400">{t('reports.subtitle')}</p>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'error'
            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
            : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
        }`}>
          {message.type === 'error' ? <AlertTriangle className="w-5 h-5" /> : <Check className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Report Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reportTypes.map((report) => (
          <div
            key={report.id}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg ${
                report.color === 'blue' ? 'bg-blue-100 dark:bg-blue-900/30' :
                report.color === 'green' ? 'bg-green-100 dark:bg-green-900/30' :
                report.color === 'red' ? 'bg-red-100 dark:bg-red-900/30' :
                'bg-purple-100 dark:bg-purple-900/30'
              }`}>
                <report.icon className={`w-6 h-6 ${
                  report.color === 'blue' ? 'text-blue-600 dark:text-blue-400' :
                  report.color === 'green' ? 'text-green-600 dark:text-green-400' :
                  report.color === 'red' ? 'text-red-600 dark:text-red-400' :
                  'text-purple-600 dark:text-purple-400'
                }`} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t(report.titleKey)}</h3>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{t(report.descKey)}</p>

                {/* Date Range Selector */}
                {report.hasDateRange && (
                  <div className="mt-4 flex items-center gap-3">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <select
                      value={selectedDays}
                      onChange={(e) => setSelectedDays(parseInt(e.target.value))}
                      className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    >
                      <option value={7}>{t('reports.last7Days')}</option>
                      <option value={14}>{t('reports.last14Days')}</option>
                      <option value={30}>{t('reports.last30Days')}</option>
                      <option value={60}>{t('reports.last60Days')}</option>
                      <option value={90}>{t('reports.last90Days')}</option>
                    </select>
                  </div>
                )}

                {/* Risk Threshold Selector (for high-risk report) */}
                {report.hasThreshold && (
                  <div className="mt-3 flex items-center gap-3">
                    <AlertTriangle className="w-4 h-4 text-gray-400" />
                    <select
                      value={riskThreshold}
                      onChange={(e) => setRiskThreshold(parseInt(e.target.value))}
                      className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    >
                      <option value={25}>{t('reports.riskMedium')}</option>
                      <option value={50}>{t('reports.riskHigh')}</option>
                      <option value={75}>{t('reports.riskCritical')}</option>
                    </select>
                  </div>
                )}

                {/* Download Button */}
                <button
                  onClick={() => handleDownload(report.id)}
                  disabled={loading[report.id]}
                  className={`mt-4 flex items-center gap-2 px-4 py-2 rounded-lg text-white transition-colors disabled:opacity-50 ${
                    report.color === 'blue' ? 'bg-blue-600 hover:bg-blue-700' :
                    report.color === 'green' ? 'bg-green-600 hover:bg-green-700' :
                    report.color === 'red' ? 'bg-red-600 hover:bg-red-700' :
                    'bg-purple-600 hover:bg-purple-700'
                  }`}
                >
                  {loading[report.id] ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      {t('reports.generating')}
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      {t('reports.downloadPDF')}
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Batch Report Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
            <FileText className="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('reports.batchReport')}</h3>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              {t('reports.batchReportDesc')}
            </p>

            <div className="mt-4 flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder={t('reports.enterBatchId')}
                value={batchId}
                onChange={(e) => setBatchId(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <button
                onClick={() => handleDownload('batch')}
                disabled={loading.batch || !batchId.trim()}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
              >
                {loading.batch ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    {t('reports.generating')}
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    {t('reports.downloadReport')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Excel Export Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
            <FileSpreadsheet className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('reports.excelExports') || 'Excel Exports'}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{t('reports.excelExportsDesc') || 'Export data to Excel or CSV format for analysis'}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* All Predictions Excel */}
          <button
            onClick={async () => {
              setLoading({ ...loading, 'excel-all': true });
              try {
                const response = await downloadExcelReport(selectedDays);
                const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `predictions_${selectedDays}days_${new Date().toISOString().split('T')[0]}.xlsx`;
                a.click();
                URL.revokeObjectURL(url);
                showMessage(t('reports.reportDownloaded') || 'Report downloaded');
              } catch (error) {
                showMessage(error.response?.data?.detail || t('reports.failedDownload'), 'error');
              }
              setLoading({ ...loading, 'excel-all': false });
            }}
            disabled={loading['excel-all']}
            className="flex flex-col items-center gap-2 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition border border-emerald-200 dark:border-emerald-800"
          >
            {loading['excel-all'] ? <Loader className="w-6 h-6 text-emerald-600 animate-spin" /> : <FileSpreadsheet className="w-6 h-6 text-emerald-600" />}
            <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">{t('reports.allPredictions') || 'All Predictions'}</span>
            <span className="text-xs text-emerald-600 dark:text-emerald-400">.xlsx</span>
          </button>

          {/* Fraud Only Excel */}
          <button
            onClick={async () => {
              setLoading({ ...loading, 'excel-fraud': true });
              try {
                const response = await downloadExcelFraudOnly(selectedDays);
                const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `fraud_only_${selectedDays}days_${new Date().toISOString().split('T')[0]}.xlsx`;
                a.click();
                URL.revokeObjectURL(url);
                showMessage(t('reports.reportDownloaded') || 'Report downloaded');
              } catch (error) {
                showMessage(error.response?.data?.detail || t('reports.failedDownload'), 'error');
              }
              setLoading({ ...loading, 'excel-fraud': false });
            }}
            disabled={loading['excel-fraud']}
            className="flex flex-col items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition border border-red-200 dark:border-red-800"
          >
            {loading['excel-fraud'] ? <Loader className="w-6 h-6 text-red-600 animate-spin" /> : <AlertTriangle className="w-6 h-6 text-red-600" />}
            <span className="text-sm font-medium text-red-700 dark:text-red-300">{t('reports.fraudOnly') || 'Fraud Only'}</span>
            <span className="text-xs text-red-600 dark:text-red-400">.xlsx</span>
          </button>

          {/* High Risk Excel */}
          <button
            onClick={async () => {
              setLoading({ ...loading, 'excel-risk': true });
              try {
                const response = await downloadExcelHighRisk(selectedDays, riskThreshold);
                const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `high_risk_${riskThreshold}plus_${new Date().toISOString().split('T')[0]}.xlsx`;
                a.click();
                URL.revokeObjectURL(url);
                showMessage(t('reports.reportDownloaded') || 'Report downloaded');
              } catch (error) {
                showMessage(error.response?.data?.detail || t('reports.failedDownload'), 'error');
              }
              setLoading({ ...loading, 'excel-risk': false });
            }}
            disabled={loading['excel-risk']}
            className="flex flex-col items-center gap-2 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg hover:bg-orange-100 dark:hover:bg-orange-900/30 transition border border-orange-200 dark:border-orange-800"
          >
            {loading['excel-risk'] ? <Loader className="w-6 h-6 text-orange-600 animate-spin" /> : <TrendingUp className="w-6 h-6 text-orange-600" />}
            <span className="text-sm font-medium text-orange-700 dark:text-orange-300">{t('reports.highRiskExcel') || 'High Risk'}</span>
            <span className="text-xs text-orange-600 dark:text-orange-400">.xlsx ({riskThreshold}+)</span>
          </button>

          {/* CSV Export */}
          <button
            onClick={async () => {
              setLoading({ ...loading, 'csv': true });
              try {
                const response = await downloadCSVExport(selectedDays);
                const blob = new Blob([response.data], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `predictions_${selectedDays}days_${new Date().toISOString().split('T')[0]}.csv`;
                a.click();
                URL.revokeObjectURL(url);
                showMessage(t('reports.reportDownloaded') || 'Report downloaded');
              } catch (error) {
                showMessage(error.response?.data?.detail || t('reports.failedDownload'), 'error');
              }
              setLoading({ ...loading, 'csv': false });
            }}
            disabled={loading['csv']}
            className="flex flex-col items-center gap-2 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition border border-blue-200 dark:border-blue-800"
          >
            {loading['csv'] ? <Loader className="w-6 h-6 text-blue-600 animate-spin" /> : <Table className="w-6 h-6 text-blue-600" />}
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">{t('reports.csvExport') || 'CSV Export'}</span>
            <span className="text-xs text-blue-600 dark:text-blue-400">.csv</span>
          </button>
        </div>
      </div>

      {/* Report Information */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('reports.reportInfo')}</h3>
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <FileText className="w-5 h-5 text-gray-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">{t('reports.pdfFormat')}</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('reports.pdfFormatDesc')}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <BarChart2 className="w-5 h-5 text-gray-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">{t('reports.includedVisualizations')}</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('reports.includedVisualizationsDesc')}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">{t('reports.customDateRanges')}</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('reports.customDateRangesDesc')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
