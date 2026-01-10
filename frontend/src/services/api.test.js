import { describe, it, expect, vi, beforeEach } from 'vitest'

// Simple tests for API functions that don't rely on complex mocking

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Clear localStorage
    localStorage.clear()
  })

  describe('Authentication Helpers', () => {
    describe('logout', () => {
      it('dispatches auth-logout event', async () => {
        const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

        const { logout } = await import('./api.js')
        logout()

        expect(dispatchSpy).toHaveBeenCalled()
        const event = dispatchSpy.mock.calls.find(call => call[0].type === 'auth-logout')
        expect(event).toBeDefined()
      })
    })

    describe('isAuthenticated', () => {
      it('is a function that checks token', async () => {
        const { isAuthenticated } = await import('./api.js')

        // Without token set in our mock localStorage, should return false
        expect(typeof isAuthenticated).toBe('function')
        // Call it to verify no errors
        const result = isAuthenticated()
        expect(typeof result).toBe('boolean')
      })
    })
  })

  describe('Cache utilities', () => {
    it('clearCache function exists', async () => {
      const { clearCache } = await import('./api.js')
      expect(typeof clearCache).toBe('function')
    })

    it('clearCache does not throw', async () => {
      const { clearCache } = await import('./api.js')
      expect(() => clearCache()).not.toThrow()
      expect(() => clearCache('pattern')).not.toThrow()
    })
  })

  describe('API functions exist', () => {
    it('exports authentication functions', async () => {
      const api = await import('./api.js')

      expect(typeof api.login).toBe('function')
      expect(typeof api.register).toBe('function')
      expect(typeof api.logout).toBe('function')
      expect(typeof api.getMe).toBe('function')
      expect(typeof api.refreshToken).toBe('function')
      expect(typeof api.isAuthenticated).toBe('function')
    })

    it('exports prediction functions', async () => {
      const api = await import('./api.js')

      expect(typeof api.predictFraud).toBe('function')
      expect(typeof api.predictBatch).toBe('function')
      expect(typeof api.getSampleLegitimate).toBe('function')
      expect(typeof api.getSampleFraud).toBe('function')
      expect(typeof api.getPredictionHistory).toBe('function')
    })

    it('exports analytics functions', async () => {
      const api = await import('./api.js')

      expect(typeof api.getStats).toBe('function')
      expect(typeof api.getModelInfo).toBe('function')
      expect(typeof api.getFeatureImportance).toBe('function')
      expect(typeof api.getTimeSeries).toBe('function')
    })

    it('exports admin functions', async () => {
      const api = await import('./api.js')

      expect(typeof api.getSystemStats).toBe('function')
      expect(typeof api.getUsers).toBe('function')
      expect(typeof api.changeUserRole).toBe('function')
      expect(typeof api.deleteUser).toBe('function')
    })

    it('exports health check function', async () => {
      const api = await import('./api.js')

      expect(typeof api.checkHealth).toBe('function')
    })
  })

  describe('Rate limit header extraction', () => {
    it('extracts rate limit headers correctly', async () => {
      const { extractRateLimitHeaders } = await import('./api.js')

      const mockResponse = {
        headers: {
          'x-ratelimit-limit': '100',
          'x-ratelimit-remaining': '95',
          'x-ratelimit-reset': '1609459200'
        }
      }

      const result = extractRateLimitHeaders(mockResponse)

      expect(result.limit).toBe(100)
      expect(result.remaining).toBe(95)
      expect(result.reset).toBe(1609459200)
    })

    it('returns defaults for missing headers', async () => {
      const { extractRateLimitHeaders } = await import('./api.js')

      const mockResponse = { headers: {} }

      const result = extractRateLimitHeaders(mockResponse)

      expect(result.limit).toBe(100)
      expect(result.remaining).toBe(100)
      expect(result.reset).toBe(0)
    })
  })
})
