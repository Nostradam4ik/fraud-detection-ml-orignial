import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../test/test-utils.jsx'
import userEvent from '@testing-library/user-event'
import TransactionForm from './TransactionForm.jsx'

// Mock the API module
vi.mock('../services/api', () => ({
  predictFraud: vi.fn(),
  getSampleLegitimate: vi.fn(),
  getSampleFraud: vi.fn(),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Send: () => <span data-testid="send-icon">Send</span>,
  RefreshCw: () => <span data-testid="refresh-icon">Refresh</span>,
  Zap: () => <span data-testid="zap-icon">Zap</span>,
  AlertCircle: () => <span data-testid="alert-icon">Alert</span>,
}))

import { predictFraud, getSampleLegitimate, getSampleFraud } from '../services/api'

describe('TransactionForm Component', () => {
  const mockOnPrediction = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders the form with all required fields', () => {
      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      // Check for title (translated as "Transaction Analysis" or similar)
      expect(screen.getByRole('heading', { level: 3 }) || screen.getByText(/analysis/i)).toBeTruthy()
      // Check for time and amount labels
      expect(screen.getAllByText(/time/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/amount/i).length).toBeGreaterThan(0)
    })

    it('renders sample buttons', () => {
      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      expect(screen.getByText(/legitimate sample/i)).toBeInTheDocument()
      expect(screen.getByText(/fraud sample/i)).toBeInTheDocument()
    })

    it('renders V1-V28 feature inputs', () => {
      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      // Check for V1 and V28 at minimum
      expect(screen.getByText('V1')).toBeInTheDocument()
      expect(screen.getByText('V28')).toBeInTheDocument()
    })

    it('renders analyze button', () => {
      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('submits form with correct data when API is online', async () => {
      const user = userEvent.setup()
      const mockResult = { is_fraud: false, probability: 0.05 }
      predictFraud.mockResolvedValueOnce(mockResult)

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      await user.click(screen.getByRole('button', { name: /analyze/i }))

      await waitFor(() => {
        expect(predictFraud).toHaveBeenCalled()
        expect(mockOnPrediction).toHaveBeenCalledWith(mockResult, expect.any(Object))
      })
    })

    it('does not call API when offline', async () => {
      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="offline" />)

      // Button should be disabled when API is offline
      const submitButton = screen.getByRole('button', { name: /analyze/i })
      expect(submitButton).toBeDisabled()
      expect(predictFraud).not.toHaveBeenCalled()
    })

    it('disables submit button when loading', async () => {
      const user = userEvent.setup()
      predictFraud.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      const submitButton = screen.getByRole('button', { name: /analyze/i })
      await user.click(submitButton)

      expect(submitButton).toBeDisabled()
    })

    it('displays error message on prediction failure', async () => {
      const user = userEvent.setup()
      predictFraud.mockRejectedValueOnce({
        response: { data: { detail: 'Prediction failed' } }
      })

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      await user.click(screen.getByRole('button', { name: /analyze/i }))

      await waitFor(() => {
        expect(screen.getByText(/prediction failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Sample Loading', () => {
    it('loads legitimate sample', async () => {
      const user = userEvent.setup()
      const mockSample = { time: 100, amount: 50.5, v1: 1.5, v2: -0.5 }
      getSampleLegitimate.mockResolvedValueOnce(mockSample)

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      await user.click(screen.getByText(/legitimate sample/i))

      await waitFor(() => {
        expect(getSampleLegitimate).toHaveBeenCalled()
      })
    })

    it('loads fraud sample', async () => {
      const user = userEvent.setup()
      const mockSample = { time: 200, amount: 1000, v1: -5.5, v2: 3.2 }
      getSampleFraud.mockResolvedValueOnce(mockSample)

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      await user.click(screen.getByText(/fraud sample/i))

      await waitFor(() => {
        expect(getSampleFraud).toHaveBeenCalled()
      })
    })

    it('shows error when sample loading fails', async () => {
      const user = userEvent.setup()
      getSampleLegitimate.mockRejectedValueOnce(new Error('Network error'))

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      await user.click(screen.getByText(/legitimate sample/i))

      await waitFor(() => {
        expect(screen.getByText(/failed to load sample/i)).toBeInTheDocument()
      })
    })
  })

  describe('Input Handling', () => {
    it('updates amount field', async () => {
      const user = userEvent.setup()

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      const amountInputs = screen.getAllByRole('spinbutton')
      const amountInput = amountInputs[1] // Second input is amount

      await user.clear(amountInput)
      await user.type(amountInput, '250.50')

      expect(amountInput).toHaveValue(250.5)
    })

    it('can clear input field', async () => {
      const user = userEvent.setup()

      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      const amountInputs = screen.getAllByRole('spinbutton')
      const timeInput = amountInputs[0] // First input is time

      await user.clear(timeInput)

      // After clearing, input should be empty or null
      expect(timeInput.value === '' || timeInput.value === '0').toBe(true)
    })
  })

  describe('API Status', () => {
    it('disables submit button when API is offline', () => {
      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="offline" />)

      const submitButton = screen.getByRole('button', { name: /analyze/i })
      expect(submitButton).toBeDisabled()
    })

    it('enables submit button when API is online', () => {
      render(<TransactionForm onPrediction={mockOnPrediction} apiStatus="online" />)

      const submitButton = screen.getByRole('button', { name: /analyze/i })
      expect(submitButton).not.toBeDisabled()
    })
  })
})
