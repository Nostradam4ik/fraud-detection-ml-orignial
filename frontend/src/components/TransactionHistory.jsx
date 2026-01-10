import { Clock, AlertTriangle, CheckCircle, Trash2 } from 'lucide-react';

function TransactionHistory({ history }) {
  if (history.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900">Prediction History</h3>
        </div>
        <span className="text-sm text-gray-500">{history.length} entries</span>
      </div>

      <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
        {history.map((item, index) => (
          <div
            key={item.id}
            className="px-6 py-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${
                  item.result.is_fraud ? 'bg-danger-100' : 'bg-success-100'
                }`}>
                  {item.result.is_fraud ? (
                    <AlertTriangle className="w-4 h-4 text-danger-600" />
                  ) : (
                    <CheckCircle className="w-4 h-4 text-success-600" />
                  )}
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {item.result.is_fraud ? 'Fraud' : 'Legitimate'}
                    <span className="text-gray-500 font-normal ml-2">
                      #{history.length - index}
                    </span>
                  </p>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span>Amount: ${item.transaction.amount.toFixed(2)}</span>
                    <span>Risk: {item.result.risk_score}%</span>
                    <span>{item.result.prediction_time_ms.toFixed(1)}ms</span>
                  </div>
                </div>
              </div>
              <span className="text-xs text-gray-400">
                {new Date(item.timestamp).toLocaleTimeString()}
              </span>
            </div>

            {/* Probability Bar */}
            <div className="mt-3 ml-11">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${
                      item.result.is_fraud ? 'bg-danger-500' : 'bg-success-500'
                    }`}
                    style={{ width: `${item.result.fraud_probability * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-12 text-right">
                  {(item.result.fraud_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TransactionHistory;
