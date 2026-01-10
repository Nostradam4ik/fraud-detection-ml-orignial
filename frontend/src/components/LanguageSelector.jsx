/**
 * Language Selector Component
 * Dropdown to switch between available languages
 */

import { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';
import { useI18n } from '../i18n';

export default function LanguageSelector({ variant = 'dropdown', showFlag = true, showName = true }) {
  const { locale, setLocale, locales } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentLocale = locales.find(l => l.code === locale);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'Enter' || e.key === ' ') {
      setIsOpen(!isOpen);
    }
  };

  const handleSelect = (code) => {
    setLocale(code);
    setIsOpen(false);
  };

  // Button variant - shows all languages as buttons
  if (variant === 'buttons') {
    return (
      <div className="flex items-center gap-1">
        {locales.map(({ code, name, flag }) => (
          <button
            key={code}
            onClick={() => setLocale(code)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              locale === code
                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title={name}
          >
            {showFlag && <span className="mr-1">{flag}</span>}
            {showName && code.toUpperCase()}
          </button>
        ))}
      </div>
    );
  }

  // Compact variant - just shows flags
  if (variant === 'compact') {
    return (
      <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
        {locales.map(({ code, name, flag }) => (
          <button
            key={code}
            onClick={() => setLocale(code)}
            className={`p-1.5 rounded-md text-lg transition-all ${
              locale === code
                ? 'bg-white dark:bg-gray-600 shadow-sm'
                : 'hover:bg-gray-200 dark:hover:bg-gray-600 opacity-60 hover:opacity-100'
            }`}
            title={name}
          >
            {flag}
          </button>
        ))}
      </div>
    );
  }

  // Default dropdown variant
  return (
    <div ref={dropdownRef} className="relative language-selector">
      <button
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        {showFlag && currentLocale && (
          <span className="text-lg">{currentLocale.flag}</span>
        )}
        {!showFlag && <Globe className="w-4 h-4" />}
        {showName && currentLocale && (
          <span className="hidden sm:inline">{currentLocale.name}</span>
        )}
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50"
          role="listbox"
          aria-label="Select language"
        >
          {locales.map(({ code, name, flag }) => (
            <button
              key={code}
              onClick={() => handleSelect(code)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                locale === code
                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
              role="option"
              aria-selected={locale === code}
            >
              <span className="text-lg">{flag}</span>
              <span className="flex-1 text-left">{name}</span>
              {locale === code && (
                <Check className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
