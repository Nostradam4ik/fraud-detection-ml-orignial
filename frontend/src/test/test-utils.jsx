import { render } from '@testing-library/react'
import { I18nProvider } from '../i18n/index.jsx'

// Custom render that wraps components with providers
const customRender = (ui, options = {}) => {
  const Wrapper = ({ children }) => (
    <I18nProvider>
      {children}
    </I18nProvider>
  )

  return render(ui, { wrapper: Wrapper, ...options })
}

// Re-export everything
export * from '@testing-library/react'

// Override render method
export { customRender as render }
