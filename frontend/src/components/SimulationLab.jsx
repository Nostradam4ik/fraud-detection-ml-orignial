import { useState, useEffect, useCallback } from 'react';
import {
  FlaskConical,
  Play,
  Square,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Target,
  Trophy,
  Award,
  BookOpen,
  Lightbulb,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  HelpCircle,
  Zap,
  Shield,
  Users,
  TrendingUp,
  Eye,
  EyeOff,
  Send,
  BarChart2
} from 'lucide-react';
import { useI18n } from '../i18n/index.jsx';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function SimulationLab() {
  const { t } = useI18n();
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [decisions, setDecisions] = useState({});
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('scenarios'); // scenarios, simulation, results
  const [startTime, setStartTime] = useState(null);
  const [expandedTx, setExpandedTx] = useState(null);
  const [showHints, setShowHints] = useState({});
  const [filterStatus, setFilterStatus] = useState('all'); // all, pending, decided

  // Fetch scenarios on mount
  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/v1/simulation/scenarios`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setScenarios(data);
      }
    } catch (err) {
      setError('Failed to load scenarios');
    }
  };

  const startSimulation = async (scenarioId) => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/v1/simulation/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          scenario_id: scenarioId,
          num_transactions: 50,
          fraud_rate: 0.20,
          time_span_hours: 48,
          include_edge_cases: true,
          randomize_patterns: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSimulation(data);
        setDecisions({});
        setEvaluation(null);
        setStartTime(Date.now());
        setView('simulation');
      } else {
        setError('Failed to start simulation');
      }
    } catch (err) {
      setError('Failed to start simulation');
    } finally {
      setLoading(false);
    }
  };

  const makeDecision = (transactionId, decision, confidence = 80) => {
    setDecisions(prev => ({
      ...prev,
      [transactionId]: { decision, confidence }
    }));
  };

  const submitDecisions = async () => {
    if (!simulation) return;

    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    const decisionList = Object.entries(decisions).map(([txId, data]) => ({
      transaction_id: txId,
      decision: data.decision,
      confidence: data.confidence,
      reasoning: null
    }));

    // Add pending decisions as "legitimate" with low confidence
    simulation.transactions.forEach(tx => {
      if (!decisions[tx.id]) {
        decisionList.push({
          transaction_id: tx.id,
          decision: 'legitimate',
          confidence: 50,
          reasoning: null
        });
      }
    });

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/v1/simulation/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          simulation_id: simulation.simulation_id,
          decisions: decisionList,
          time_taken_seconds: timeTaken
        })
      });

      if (response.ok) {
        const data = await response.json();
        setEvaluation(data);
        setView('results');
      } else {
        setError('Failed to submit decisions');
      }
    } catch (err) {
      setError('Failed to submit decisions');
    } finally {
      setLoading(false);
    }
  };

  const getHint = async (transactionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_URL}/api/v1/simulation/hints/${simulation.simulation_id}/${transactionId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        setShowHints(prev => ({ ...prev, [transactionId]: data.hints }));
      }
    } catch (err) {
      console.error('Failed to get hint');
    }
  };

  const resetSimulation = () => {
    setSimulation(null);
    setDecisions({});
    setEvaluation(null);
    setView('scenarios');
    setStartTime(null);
    setExpandedTx(null);
    setShowHints({});
  };

  const getDifficultyColor = (difficulty) => {
    const colors = {
      beginner: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      intermediate: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      advanced: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      expert: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    };
    return colors[difficulty] || colors.beginner;
  };

  const getCategoryIcon = (category) => {
    const icons = {
      card_not_present: Shield,
      account_takeover: Users,
      velocity_attack: Zap,
      money_laundering: TrendingUp,
      synthetic_identity: Users,
      friendly_fraud: AlertTriangle,
      bust_out: TrendingUp,
      identity_theft: Shield
    };
    const Icon = icons[category] || Shield;
    return <Icon className="w-5 h-5" />;
  };

  const getGradeColor = (grade) => {
    if (grade.startsWith('A')) return 'text-green-600 dark:text-green-400';
    if (grade.startsWith('B')) return 'text-blue-600 dark:text-blue-400';
    if (grade.startsWith('C')) return 'text-yellow-600 dark:text-yellow-400';
    if (grade.startsWith('D')) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  const filteredTransactions = simulation?.transactions.filter(tx => {
    if (filterStatus === 'pending') return !decisions[tx.id];
    if (filterStatus === 'decided') return decisions[tx.id];
    return true;
  }) || [];

  const decidedCount = Object.keys(decisions).length;
  const totalCount = simulation?.transactions.length || 0;
  const progress = totalCount > 0 ? (decidedCount / totalCount) * 100 : 0;

  // Scenarios View
  if (view === 'scenarios') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <FlaskConical className="w-8 h-8" />
            <h1 className="text-2xl font-bold">
              {t('simulation.title') || 'Fraud Simulation Lab'}
            </h1>
          </div>
          <p className="text-purple-100">
            {t('simulation.subtitle') || 'Train your fraud detection skills in a safe sandbox environment'}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-300">
            {error}
          </div>
        )}

        {/* Scenario Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scenarios.map(scenario => (
            <div
              key={scenario.id}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
                      {getCategoryIcon(scenario.category)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {scenario.name}
                      </h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getDifficultyColor(scenario.difficulty)}`}>
                        {scenario.difficulty}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400 text-sm">
                    <Clock className="w-4 h-4" />
                    {scenario.estimated_time_minutes}m
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                  {scenario.description}
                </p>

                {/* Learning Objectives */}
                <div className="mb-4">
                  <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
                    {t('simulation.objectives') || 'Learning Objectives'}
                  </h4>
                  <ul className="space-y-1">
                    {scenario.learning_objectives.slice(0, 3).map((obj, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <Target className="w-3 h-3 mt-1 text-purple-500 flex-shrink-0" />
                        <span className="line-clamp-1">{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => {
                    setSelectedScenario(scenario);
                    startSimulation(scenario.id);
                  }}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {loading && selectedScenario?.id === scenario.id ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      {t('simulation.loading') || 'Loading...'}
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      {t('simulation.start') || 'Start Simulation'}
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Info Card */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <BookOpen className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-1">
                {t('simulation.howItWorks') || 'How It Works'}
              </h3>
              <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                <li>1. {t('simulation.step1') || 'Choose a fraud scenario to practice'}</li>
                <li>2. {t('simulation.step2') || 'Review simulated transactions and identify fraud'}</li>
                <li>3. {t('simulation.step3') || 'Submit your decisions and receive instant feedback'}</li>
                <li>4. {t('simulation.step4') || 'Learn from detailed analysis and improve your skills'}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Simulation View
  if (view === 'simulation' && simulation) {
    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <FlaskConical className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h2 className="font-semibold text-gray-900 dark:text-white">
                  {simulation.scenario.name}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('simulation.reviewTransactions') || 'Review each transaction and mark as fraud or legitimate'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Timer */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Clock className="w-4 h-4 text-gray-500" />
                <Timer startTime={startTime} />
              </div>

              {/* Progress */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Target className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
                  {decidedCount}/{totalCount}
                </span>
              </div>

              <button
                onClick={resetSimulation}
                className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                title={t('simulation.cancel') || 'Cancel'}
              >
                <Square className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-600 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilterStatus('all')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              filterStatus === 'all'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
          >
            {t('simulation.all') || 'All'} ({totalCount})
          </button>
          <button
            onClick={() => setFilterStatus('pending')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              filterStatus === 'pending'
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
          >
            {t('simulation.pending') || 'Pending'} ({totalCount - decidedCount})
          </button>
          <button
            onClick={() => setFilterStatus('decided')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              filterStatus === 'decided'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
          >
            {t('simulation.decided') || 'Decided'} ({decidedCount})
          </button>
        </div>

        {/* Transactions */}
        <div className="space-y-3">
          {filteredTransactions.map(tx => (
            <TransactionCard
              key={tx.id}
              transaction={tx}
              decision={decisions[tx.id]}
              onDecision={makeDecision}
              expanded={expandedTx === tx.id}
              onToggle={() => setExpandedTx(expandedTx === tx.id ? null : tx.id)}
              hints={showHints[tx.id]}
              onGetHint={() => getHint(tx.id)}
              t={t}
            />
          ))}
        </div>

        {/* Submit Button */}
        <div className="sticky bottom-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {decidedCount < totalCount && (
                <span className="text-yellow-600 dark:text-yellow-400">
                  {t('simulation.undecided', { count: totalCount - decidedCount }) ||
                    `${totalCount - decidedCount} undecided will be marked as legitimate`}
                </span>
              )}
            </div>
            <button
              onClick={submitDecisions}
              disabled={loading || decidedCount === 0}
              className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  {t('simulation.submitting') || 'Submitting...'}
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  {t('simulation.submit') || 'Submit Decisions'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Results View
  if (view === 'results' && evaluation) {
    return (
      <div className="space-y-6">
        {/* Grade Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-6 text-white text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Trophy className="w-8 h-8" />
            <h2 className="text-2xl font-bold">
              {t('simulation.results') || 'Simulation Complete!'}
            </h2>
          </div>
          <div className={`text-6xl font-bold ${getGradeColor(evaluation.performance_grade)}`}>
            {evaluation.performance_grade}
          </div>
          <p className="text-purple-100 mt-2">
            {t('simulation.score') || 'Score'}: {evaluation.f1_score.toFixed(1)}%
          </p>
        </div>

        {/* Badges */}
        {evaluation.badges_earned.length > 0 && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
            <h3 className="font-medium text-yellow-800 dark:text-yellow-300 mb-3 flex items-center gap-2">
              <Award className="w-5 h-5" />
              {t('simulation.badgesEarned') || 'Badges Earned'}
            </h3>
            <div className="flex flex-wrap gap-2">
              {evaluation.badges_earned.map((badge, i) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-300 rounded-full text-sm font-medium"
                >
                  {badge}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={CheckCircle}
            label={t('simulation.accuracy') || 'Accuracy'}
            value={`${evaluation.accuracy.toFixed(1)}%`}
            color="green"
          />
          <StatCard
            icon={Target}
            label={t('simulation.precision') || 'Precision'}
            value={`${evaluation.precision.toFixed(1)}%`}
            color="blue"
          />
          <StatCard
            icon={BarChart2}
            label={t('simulation.recall') || 'Recall'}
            value={`${evaluation.recall.toFixed(1)}%`}
            color="purple"
          />
          <StatCard
            icon={Clock}
            label={t('simulation.timeTaken') || 'Time'}
            value={formatTime(evaluation.time_taken_seconds)}
            color="gray"
          />
        </div>

        {/* Detailed Metrics */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
            {t('simulation.detailedMetrics') || 'Detailed Metrics'}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500 dark:text-gray-400">{t('simulation.totalTx') || 'Total Transactions'}</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">{evaluation.total_transactions}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">{t('simulation.correct') || 'Correct Decisions'}</p>
              <p className="text-lg font-semibold text-green-600 dark:text-green-400">{evaluation.correct_decisions}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">{t('simulation.falsePositives') || 'False Positives'}</p>
              <p className="text-lg font-semibold text-yellow-600 dark:text-yellow-400">{evaluation.false_positives}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">{t('simulation.falseNegatives') || 'False Negatives'}</p>
              <p className="text-lg font-semibold text-red-600 dark:text-red-400">{evaluation.false_negatives}</p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 grid grid-cols-2 gap-4">
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">
                {t('simulation.missedFraud') || 'Missed Fraud Amount'}
              </p>
              <p className="text-xl font-bold text-red-700 dark:text-red-300">
                ${evaluation.missed_fraud_amount.toFixed(2)}
              </p>
            </div>
            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <p className="text-sm text-yellow-600 dark:text-yellow-400">
                {t('simulation.blockedLegit') || 'Blocked Legitimate'}
              </p>
              <p className="text-xl font-bold text-yellow-700 dark:text-yellow-300">
                ${evaluation.blocked_legitimate_amount.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        {/* Feedback */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            {t('simulation.feedback') || 'Feedback'}
          </h3>
          <ul className="space-y-2">
            {evaluation.detailed_feedback.map((fb, i) => (
              <li key={i} className="flex items-start gap-2 text-gray-600 dark:text-gray-400">
                <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
                {fb}
              </li>
            ))}
          </ul>

          {evaluation.areas_to_improve.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <h4 className="font-medium text-orange-600 dark:text-orange-400 mb-2">
                {t('simulation.areasToImprove') || 'Areas to Improve'}
              </h4>
              <ul className="space-y-1">
                {evaluation.areas_to_improve.map((area, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <AlertTriangle className="w-4 h-4 mt-0.5 text-orange-500 flex-shrink-0" />
                    {area}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => startSimulation(simulation.scenario.id)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            {t('simulation.tryAgain') || 'Try Again'}
          </button>
          <button
            onClick={resetSimulation}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg font-medium transition-colors"
          >
            {t('simulation.backToScenarios') || 'Back to Scenarios'}
          </button>
        </div>
      </div>
    );
  }

  return null;
}

// Timer Component
function Timer({ startTime }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  return <span className="text-sm font-mono text-gray-600 dark:text-gray-400">{formatTime(elapsed)}</span>;
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Transaction Card Component
function TransactionCard({ transaction, decision, onDecision, expanded, onToggle, hints, onGetHint, t }) {
  const tx = transaction;

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl border transition-all ${
      decision?.decision === 'fraud'
        ? 'border-red-300 dark:border-red-700'
        : decision?.decision === 'legitimate'
        ? 'border-green-300 dark:border-green-700'
        : 'border-gray-200 dark:border-gray-700'
    }`}>
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onToggle}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
            <div>
              <p className="font-medium text-gray-900 dark:text-white">{tx.merchant}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {new Date(tx.timestamp).toLocaleString()} · {tx.merchant_category}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-lg font-bold text-gray-900 dark:text-white">
              ${tx.amount.toFixed(2)}
            </span>

            {/* Decision Buttons */}
            <div className="flex gap-1">
              <button
                onClick={() => onDecision(tx.id, 'legitimate')}
                className={`p-2 rounded-lg transition-colors ${
                  decision?.decision === 'legitimate'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-green-100 dark:hover:bg-green-900/30'
                }`}
                title={t('simulation.markLegit') || 'Mark as Legitimate'}
              >
                <CheckCircle className="w-5 h-5" />
              </button>
              <button
                onClick={() => onDecision(tx.id, 'fraud')}
                className={`p-2 rounded-lg transition-colors ${
                  decision?.decision === 'fraud'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-red-100 dark:hover:bg-red-900/30'
                }`}
                title={t('simulation.markFraud') || 'Mark as Fraud'}
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Expanded Details */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <p className="text-gray-500 dark:text-gray-400">{t('simulation.location') || 'Location'}</p>
                <p className="text-gray-900 dark:text-white">{tx.location}</p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">{t('simulation.cardPresent') || 'Card Present'}</p>
                <p className="text-gray-900 dark:text-white">{tx.card_present ? 'Yes' : 'No'}</p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">{t('simulation.device') || 'Device'}</p>
                <p className="text-gray-900 dark:text-white font-mono text-xs">{tx.device_fingerprint}</p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">{t('simulation.ip') || 'IP Address'}</p>
                <p className="text-gray-900 dark:text-white font-mono text-xs">{tx.ip_address}</p>
              </div>
            </div>

            {/* Hint Section */}
            {hints ? (
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2 flex items-center gap-1">
                  <Lightbulb className="w-4 h-4" />
                  {t('simulation.hints') || 'Hints'}
                </h4>
                <ul className="text-sm text-blue-600 dark:text-blue-400 space-y-1">
                  {hints.map((hint, i) => (
                    <li key={i}>• {hint}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <button
                onClick={onGetHint}
                className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                <HelpCircle className="w-4 h-4" />
                {t('simulation.getHint') || 'Get Hint (-5 points)'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
    gray: 'bg-gray-50 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400'
  };

  return (
    <div className={`rounded-xl p-4 ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4" />
        <span className="text-sm">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

export default SimulationLab;
