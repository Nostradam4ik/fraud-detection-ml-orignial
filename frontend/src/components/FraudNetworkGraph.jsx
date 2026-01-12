import { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import * as d3Force from 'd3-force';
import {
  Network,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  AlertTriangle,
  Activity,
  Info,
  X,
  Play,
  Pause,
  ChevronRight
} from 'lucide-react';
import { useI18n } from '../i18n/index.jsx';

// API call to get fraud network data
const getFraudNetwork = async (token, params) => {
  const queryParams = new URLSearchParams(params).toString();
  const response = await fetch(`/api/v1/fraud-network/graph?${queryParams}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to fetch network data');
  return response.json();
};

const getNodeDetails = async (token, nodeId) => {
  const response = await fetch(`/api/v1/fraud-network/node/${nodeId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to fetch node details');
  return response.json();
};

export default function FraudNetworkGraph() {
  const { t } = useI18n();
  const graphRef = useRef();
  const containerRef = useRef();

  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeDetails, setNodeDetails] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    days: 7,
    minRisk: 30,
    includeLegitimate: false,
    threshold: 0.25
  });

  // Load graph data
  const loadGraphData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const data = await getFraudNetwork(token, {
        days: filters.days,
        min_risk: filters.minRisk,
        include_legitimate: filters.includeLegitimate,
        similarity_threshold: filters.threshold
      });

      // Calculate circular layout positions
      const nodeCount = data.nodes.length;
      const centerX = 400;
      const centerY = 300;
      const radius = Math.min(250, 80 * nodeCount / Math.PI); // Dynamic radius based on node count

      // Transform data for force graph with circular positions
      const transformedData = {
        nodes: data.nodes.map((node, index) => {
          const angle = (2 * Math.PI * index) / nodeCount - Math.PI / 2;
          return {
            ...node,
            id: node.id,
            val: node.size || 10,
            // Pre-calculate fixed positions in a circle
            fx: centerX + radius * Math.cos(angle),
            fy: centerY + radius * Math.sin(angle)
          };
        }),
        links: data.edges.map(edge => ({
          ...edge,
          source: edge.source,
          target: edge.target,
          value: edge.weight
        }))
      };

      setGraphData(transformedData);
      setStatistics(data.statistics);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  }, [filters]);

  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  // Load node details
  const handleNodeClick = useCallback(async (node) => {
    setSelectedNode(node);
    try {
      const token = localStorage.getItem('token');
      const details = await getNodeDetails(token, node.id);
      setNodeDetails(details);
    } catch (err) {
      console.error('Failed to load node details:', err);
    }
  }, []);

  // Custom node canvas rendering
  const paintNode = useCallback((node, ctx, globalScale) => {
    const label = node.label;
    const fontSize = 12 / globalScale;
    ctx.font = `${fontSize}px Sans-Serif`;

    // Node circle
    const radius = node.val || 8;
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = node.color || '#6366f1';
    ctx.fill();

    // Glow effect for high-risk nodes
    if (node.risk_score >= 70) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI);
      ctx.strokeStyle = 'rgba(220, 38, 38, 0.5)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Selection ring
    if (selectedNode && selectedNode.id === node.id) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius + 5, 0, 2 * Math.PI);
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 3;
      ctx.stroke();
    }

    // Label
    if (globalScale > 0.7) {
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#fff';
      ctx.fillText(label, node.x, node.y);
    }
  }, [selectedNode]);

  // Custom link rendering
  const paintLink = useCallback((link, ctx) => {
    const start = link.source;
    const end = link.target;

    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = link.color || '#94a3b8';
    ctx.lineWidth = link.width || 1;
    ctx.stroke();
  }, []);

  // Zoom controls
  const handleZoomIn = () => graphRef.current?.zoom(1.5, 300);
  const handleZoomOut = () => graphRef.current?.zoom(0.67, 300);
  const handleFitView = () => graphRef.current?.zoomToFit(400, 50);

  // Pause/Play simulation
  const toggleSimulation = () => {
    if (isPlaying) {
      graphRef.current?.pauseAnimation();
    } else {
      graphRef.current?.resumeAnimation();
    }
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Network className="w-7 h-7 text-indigo-600" />
            {t('fraudNetwork.title') || 'Fraud Network Graph'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {t('fraudNetwork.subtitle') || 'Visualize connections between suspicious transactions'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition ${showFilters ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}`}
          >
            <Filter className="w-5 h-5" />
          </button>
          <button
            onClick={loadGraphData}
            disabled={loading}
            className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('fraudNetwork.period') || 'Period (days)'}
              </label>
              <select
                value={filters.days}
                onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={1}>1 day</option>
                <option value={3}>3 days</option>
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
                <option value={30}>30 days</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('fraudNetwork.minRisk') || 'Min Risk Score'}
              </label>
              <select
                value={filters.minRisk}
                onChange={(e) => setFilters({ ...filters, minRisk: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={0}>0+</option>
                <option value={25}>25+ (Medium)</option>
                <option value={50}>50+ (High)</option>
                <option value={75}>75+ (Critical)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('fraudNetwork.threshold') || 'Connection Threshold'}
              </label>
              <select
                value={filters.threshold}
                onChange={(e) => setFilters({ ...filters, threshold: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={0.15}>15% (More connections)</option>
                <option value={0.25}>25% (Balanced)</option>
                <option value={0.4}>40% (Strong only)</option>
                <option value={0.6}>60% (Very strong)</option>
              </select>
            </div>

            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.includeLegitimate}
                  onChange={(e) => setFilters({ ...filters, includeLegitimate: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {t('fraudNetwork.includeLegitimate') || 'Include legitimate'}
                </span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Bar */}
      {statistics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
              <Activity className="w-5 h-5" />
              <span className="text-sm font-medium">{t('fraudNetwork.nodes') || 'Nodes'}</span>
            </div>
            <p className="text-2xl font-bold text-indigo-700 dark:text-indigo-300 mt-1">
              {statistics.total_nodes}
            </p>
          </div>

          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
              <Network className="w-5 h-5" />
              <span className="text-sm font-medium">{t('fraudNetwork.edges') || 'Connections'}</span>
            </div>
            <p className="text-2xl font-bold text-orange-700 dark:text-orange-300 mt-1">
              {statistics.total_edges}
            </p>
          </div>

          <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertTriangle className="w-5 h-5" />
              <span className="text-sm font-medium">{t('fraudNetwork.clusters') || 'Clusters'}</span>
            </div>
            <p className="text-2xl font-bold text-red-700 dark:text-red-300 mt-1">
              {statistics.clusters_found}
            </p>
          </div>

          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400">
              <Activity className="w-5 h-5" />
              <span className="text-sm font-medium">{t('fraudNetwork.density') || 'Density'}</span>
            </div>
            <p className="text-2xl font-bold text-purple-700 dark:text-purple-300 mt-1">
              {(statistics.density * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Main Graph Area */}
      <div className="flex gap-6">
        {/* Graph */}
        <div
          ref={containerRef}
          className="flex-1 bg-gray-900 rounded-xl overflow-hidden relative"
          style={{ height: '600px' }}
        >
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <RefreshCw className="w-12 h-12 text-indigo-400 animate-spin mx-auto" />
                <p className="text-gray-400 mt-4">{t('fraudNetwork.loading') || 'Analyzing connections...'}</p>
              </div>
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-red-400">
                <AlertTriangle className="w-12 h-12 mx-auto" />
                <p className="mt-4">{error}</p>
                <button
                  onClick={loadGraphData}
                  className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg"
                >
                  {t('common.retry') || 'Retry'}
                </button>
              </div>
            </div>
          ) : graphData.nodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <Network className="w-12 h-12 mx-auto opacity-50" />
                <p className="mt-4">{t('fraudNetwork.noData') || 'No fraud connections found'}</p>
                <p className="text-sm mt-2">{t('fraudNetwork.tryAdjusting') || 'Try adjusting the filters'}</p>
              </div>
            </div>
          ) : (
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeCanvasObject={paintNode}
              linkCanvasObject={paintLink}
              onNodeClick={handleNodeClick}
              nodeRelSize={12}
              linkDirectionalParticles={2}
              linkDirectionalParticleSpeed={0.003}
              cooldownTicks={0}
              onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
              enableNodeDrag={false}
              backgroundColor="#111827"
              width={containerRef.current?.clientWidth || 800}
              height={600}
            />
          )}

          {/* Graph Controls */}
          <div className="absolute bottom-4 left-4 flex flex-col gap-2">
            <button
              onClick={handleZoomIn}
              className="p-2 bg-gray-800/80 hover:bg-gray-700 rounded-lg text-white"
              title="Zoom In"
            >
              <ZoomIn className="w-5 h-5" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 bg-gray-800/80 hover:bg-gray-700 rounded-lg text-white"
              title="Zoom Out"
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            <button
              onClick={handleFitView}
              className="p-2 bg-gray-800/80 hover:bg-gray-700 rounded-lg text-white"
              title="Fit to View"
            >
              <Maximize2 className="w-5 h-5" />
            </button>
            <button
              onClick={toggleSimulation}
              className="p-2 bg-gray-800/80 hover:bg-gray-700 rounded-lg text-white"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
          </div>

          {/* Legend */}
          <div className="absolute top-4 right-4 bg-gray-800/90 rounded-lg p-3 text-xs text-white">
            <p className="font-semibold mb-2">{t('fraudNetwork.legend') || 'Legend'}</p>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-600"></span>
                <span>Critical Risk (75+)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-orange-500"></span>
                <span>High Risk (50-74)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                <span>Medium Risk (25-49)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span>Low Risk (&lt;25)</span>
              </div>
              <hr className="border-gray-600 my-2" />
              <div className="flex items-center gap-2">
                <span className="w-6 h-0.5 bg-red-500"></span>
                <span>Strong connection</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-6 h-0.5 bg-gray-400"></span>
                <span>Weak connection</span>
              </div>
            </div>
          </div>
        </div>

        {/* Node Details Panel */}
        {selectedNode && (
          <div className="w-80 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Info className="w-5 h-5 text-indigo-600" />
                {t('fraudNetwork.nodeDetails') || 'Transaction Details'}
              </h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Main Info */}
              <div className="text-center">
                <div
                  className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-3"
                  style={{ backgroundColor: selectedNode.color }}
                >
                  <span className="text-white font-bold">{selectedNode.label}</span>
                </div>
                <p className={`text-lg font-bold ${selectedNode.is_fraud ? 'text-red-600' : 'text-green-600'}`}>
                  {selectedNode.is_fraud ? 'FRAUD DETECTED' : 'Legitimate'}
                </p>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Amount</p>
                  <p className="font-semibold text-gray-900 dark:text-white">${selectedNode.amount?.toFixed(2)}</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Risk Score</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{selectedNode.risk_score}</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Probability</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{(selectedNode.fraud_probability * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Confidence</p>
                  <p className="font-semibold text-gray-900 dark:text-white capitalize">{selectedNode.confidence}</p>
                </div>
              </div>

              {/* Connections */}
              {nodeDetails && nodeDetails.connections && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('fraudNetwork.relatedTransactions') || 'Related Transactions'} ({nodeDetails.total_connections})
                  </p>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {nodeDetails.connections.slice(0, 10).map((conn, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            TX-{conn.node_id}
                          </p>
                          <p className="text-xs text-gray-500">${conn.amount?.toFixed(2)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-indigo-600">
                            {(conn.similarity_score * 100).toFixed(0)}%
                          </p>
                          <p className="text-xs text-gray-500">match</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Connection Types */}
              {nodeDetails && nodeDetails.connections?.[0]?.connection_types && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('fraudNetwork.connectionTypes') || 'Connection Reasons'}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {nodeDetails.connections[0].connection_types.map((ct, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs rounded-full"
                      >
                        {ct.type.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Clusters Warning */}
      {statistics && statistics.clusters_found > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-red-800 dark:text-red-200">
                {t('fraudNetwork.clustersDetected') || 'Fraud Clusters Detected!'}
              </h4>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {t('fraudNetwork.clustersDesc') || `${statistics.clusters_found} potential fraud ring(s) identified. These transactions show strong interconnections and may indicate coordinated fraud activity.`}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
