import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../test/test-utils.jsx'
import userEvent from '@testing-library/user-event'
import Login from './Login.jsx'

// Mock the API module
vi.mock('../services/api', () => ({
  login: vi.fn(),
  register: vi.fn(),
  forgotPassword: vi.fn(),
  resetPassword: vi.fn(),
}))

import { login, register, forgotPassword, resetPassword } from '../services/api'

describe('Login Component', () => {
  const mockOnLogin = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders login form by default', () => {
      render(<Login onLogin={mockOnLogin} />)

      expect(screen.getByText('Fraud Detection')).toBeInTheDocument()
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('displays forgot password link', () => {
      render(<Login onLogin={mockOnLogin} />)

      expect(screen.getByRole('button', { name: /forgot password/i })).toBeInTheDocument()
    })

    it('displays register link', () => {
      render(<Login onLogin={mockOnLogin} />)

      expect(screen.getByText(/sign up/i)).toBeInTheDocument()
    })
  })

  describe('Mode Switching', () => {
    it('switches to register mode when clicking sign up', async () => {
      const user = userEvent.setup()
      render(<Login onLogin={mockOnLogin} />)

      await user.click(screen.getByText(/sign up/i))

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    })

    it('switches to forgot password mode', async () => {
      const user = userEvent.setup()
      render(<Login onLogin={mockOnLogin} />)

      await user.click(screen.getByRole('button', { name: /forgot password/i }))

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.queryByLabelText(/username/i)).not.toBeInTheDocument()
    })

    it('switches back to login from register mode', async () => {
      const user = userEvent.setup()
      render(<Login onLogin={mockOnLogin} />)

      // Go to register
      await user.click(screen.getByText(/sign up/i))
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()

      // Go back to login
      await user.click(screen.getByText(/sign in/i))
      expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument()
    })
  })

  describe('Login Flow', () => {
    it('submits login form successfully', async () => {
      const user = userEvent.setup()
      login.mockResolvedValueOnce({ access_token: 'test-token' })

      render(<Login onLogin={mockOnLogin} />)

      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /sign in/i }))

      await waitFor(() => {
        expect(login).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123'
        })
        expect(mockOnLogin).toHaveBeenCalled()
      })
    })

    it('displays error on login failure', async () => {
      const user = userEvent.setup()
      login.mockRejectedValueOnce({
        response: { data: { detail: 'Invalid credentials' } }
      })

      render(<Login onLogin={mockOnLogin} />)

      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
      await user.click(screen.getByRole('button', { name: /sign in/i }))

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
      })
      expect(mockOnLogin).not.toHaveBeenCalled()
    })

    it('shows loading state during submission', async () => {
      const user = userEvent.setup()
      login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<Login onLogin={mockOnLogin} />)

      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/password/i), 'password123')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Button should be disabled during loading
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Registration Flow', () => {
    it('submits registration form successfully', async () => {
      const user = userEvent.setup()
      register.mockResolvedValueOnce({})
      login.mockResolvedValueOnce({ access_token: 'test-token' })

      render(<Login onLogin={mockOnLogin} />)

      // Switch to register mode
      await user.click(screen.getByText(/sign up/i))

      await user.type(screen.getByLabelText(/username/i), 'newuser')
      await user.type(screen.getByLabelText(/email/i), 'newuser@test.com')
      await user.type(screen.getByLabelText(/full name/i), 'New User')
      await user.type(screen.getByLabelText(/password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /register/i }))

      await waitFor(() => {
        expect(register).toHaveBeenCalledWith({
          username: 'newuser',
          email: 'newuser@test.com',
          password: 'password123',
          full_name: 'New User',
          newPassword: ''
        })
        expect(login).toHaveBeenCalled()
        expect(mockOnLogin).toHaveBeenCalled()
      })
    })
  })

  describe('Forgot Password Flow', () => {
    it('submits forgot password form', async () => {
      const user = userEvent.setup()
      forgotPassword.mockResolvedValueOnce({
        message: 'Reset email sent',
        reset_token: 'test-reset-token'
      })

      render(<Login onLogin={mockOnLogin} />)

      // Switch to forgot password mode
      await user.click(screen.getByRole('button', { name: /forgot password/i }))

      await user.type(screen.getByLabelText(/email/i), 'user@test.com')
      await user.click(screen.getByRole('button', { name: /forgot password/i }))

      await waitFor(() => {
        expect(forgotPassword).toHaveBeenCalledWith('user@test.com')
      })
    })
  })

  describe('Input Validation', () => {
    it('clears error when user types', async () => {
      const user = userEvent.setup()
      login.mockRejectedValueOnce({
        response: { data: { detail: 'Invalid credentials' } }
      })

      render(<Login onLogin={mockOnLogin} />)

      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/password/i), 'wrong')
      await user.click(screen.getByRole('button', { name: /sign in/i }))

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
      })

      // Type again to clear error
      await user.type(screen.getByLabelText(/username/i), 'a')

      expect(screen.queryByText('Invalid credentials')).not.toBeInTheDocument()
    })
  })
})
