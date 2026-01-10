import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '../test/test-utils.jsx'
import userEvent from '@testing-library/user-event'
import Dashboard from './Dashboard.jsx'

// Mock the API module
vi.mock('../services/api', () => ({
  getUserPredictionStats: vi.fn(),
  getPredictionHistory: vi.fn(),
  getTimeSeries: vi.fn(),
}))

// Mock recharts to avoid complex chart rendering
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>,
  AreaChart: ({ children }) => <div data-testid="area-chart">{children}</div>,
  Area: () => null,
  BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Cell: () => null,
}))

// Mock lucide-react
vi.mock('lucide-react', () => ({
  Activity: () => <span data-testid="activity-icon">Activity</span>,
  AlertTriangle: () => <span data-testid="alert-icon">Alert</span>,
  CheckCircle: () => <span data-testid="check-icon">Check</span>,
  Clock: () => <span data-testid="clock-icon">Clock</span>,
  TrendingUp: () => <span data-testid="trending-up-icon">TrendingUp</span>,
  TrendingDown: () => <span data-testid="trending-down-icon">TrendingDown</span>,
  BarChart3: () => <span data-testid="bar-chart-icon">BarChart</span>,
  Download: () => <span data-testid="download-icon">Download</span>,
  RefreshCw: () => <span data-testid="refresh-icon">Refresh</span>,
  Zap: () => <span data-testid="zap-icon">Zap</span>,
  Target: () => <span data-testid="target-icon">Target</span>,
  DollarSign: () => <span data-testid="dollar-icon">Dollar</span>,
}))

// Mock StatsChart
vi.mock('./StatsChart', () => ({
  default: () => <div data-testid="stats-chart">StatsChart</div>
}))

import { getUserPredictionStats, getPredictionHistory, getTimeSeries } from '../services/api'

describe('Dashboard Component', () => {
  const mockStats = {
    total_predictions: 100,
    fraud_detected: 10,
    legitimate_detected: 90,
    fraud_rate: 0.1,
    average_response_time_ms: 45.5,
  }

  const mockHistory = [
    {
      id: 1,
      time: 100,
      amount: 250.50,
      is_fraud: false,
      fraud_probability: 0.05,
      confidence: 'High',
      risk_score: 15,
      prediction_time_ms: 42,
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      time: 200,
      amount: 1500.00,
      is_fraud: true,
      fraud_probability: 0.95,
      confidence: 'High',
      risk_score: 85,
      prediction_time_ms: 38,
      created_at: new Date().toISOString(),
    },
  ]

  const mockTimeSeries = {
    data: [
      { period: '2024-01-01', total: 10, fraud: 1 },
      { period: '2024-01-02', total: 15, fraud: 2 },
    ]
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    getUserPredictionStats.mockResolvedValue(mockStats)
    getPredictionHistory.mockResolvedValue(mockHistory)
    getTimeSeries.mockResolvedValue(mockTimeSeries)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Rendering', () => {
    it('renders dashboard title', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument()
      })
    })

    it('renders stat cards', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/total predictions/i)).toBeInTheDocument()
      })

      // Check fraud and legitimate text exist somewhere on the page
      await waitFor(() => {
        const fraudElements = screen.getAllByText(/fraud/i)
        expect(fraudElements.length).toBeGreaterThan(0)
      })
    })

    it('renders period selector', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })
    })

    it('renders refresh button', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByTestId('refresh-icon')).toBeInTheDocument()
      })
    })

    it('renders export button', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByTestId('download-icon')).toBeInTheDocument()
      })
    })
  })

  describe('Data Fetching', () => {
    it('fetches stats on mount', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(getUserPredictionStats).toHaveBeenCalled()
        expect(getPredictionHistory).toHaveBeenCalledWith(50)
        expect(getTimeSeries).toHaveBeenCalledWith('day', 30)
      })
    })

    it('displays fetched stats', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument() // total predictions
        expect(screen.getByText('10')).toBeInTheDocument() // fraud detected
        expect(screen.getByText('90')).toBeInTheDocument() // legitimate
      })
    })

    it('handles API errors gracefully', async () => {
      getUserPredictionStats.mockRejectedValueOnce(new Error('API Error'))

      render(<Dashboard />)

      await waitFor(() => {
        // Should not crash, just show zeros or defaults
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument()
      })
    })
  })

  describe('Period Selection', () => {
    it('changes period when selecting new option', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      const select = screen.getByRole('combobox')
      await user.selectOptions(select, '7')

      await waitFor(() => {
        expect(getTimeSeries).toHaveBeenCalledWith('day', 7)
      })
    })
  })

  describe('Refresh Functionality', () => {
    it('refreshes data when clicking refresh button', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
      render(<Dashboard />)

      await waitFor(() => {
        expect(getUserPredictionStats).toHaveBeenCalledTimes(1)
      })

      const refreshButton = screen.getByTestId('refresh-icon').closest('button')
      await user.click(refreshButton)

      await waitFor(() => {
        expect(getUserPredictionStats).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Recent Activity', () => {
    it('displays recent prediction history', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/recent activity/i)).toBeInTheDocument()
      })
    })

    it('shows correct count of predictions', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/2 predictions/i)).toBeInTheDocument()
      })
    })

    it('displays no predictions message when history is empty', async () => {
      getPredictionHistory.mockResolvedValueOnce([])

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/no predictions yet/i)).toBeInTheDocument()
      })
    })
  })

  describe('Charts', () => {
    it('renders StatsChart component', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByTestId('stats-chart')).toBeInTheDocument()
      })
    })

    it('renders time series chart when data available', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByTestId('area-chart')).toBeInTheDocument()
      })
    })

    it('shows message when no time series data', async () => {
      getTimeSeries.mockResolvedValueOnce({ data: [] })

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/no time series data/i)).toBeInTheDocument()
      })
    })
  })

  describe('Export Functionality', () => {
    it('export button is enabled when history exists', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        const exportButton = screen.getByTestId('download-icon').closest('button')
        expect(exportButton).not.toBeDisabled()
      })
    })

    it('export button is disabled when no history', async () => {
      getPredictionHistory.mockResolvedValueOnce([])

      render(<Dashboard />)

      await waitFor(() => {
        const exportButton = screen.getByTestId('download-icon').closest('button')
        expect(exportButton).toBeDisabled()
      })
    })
  })

  describe('System Status', () => {
    it('renders system status section', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/system status/i)).toBeInTheDocument()
      })
    })

    it('shows healthy API status', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/healthy/i)).toBeInTheDocument()
      })
    })
  })
})
