/**
 * Internationalization (i18n) System
 * Supports English (en), French (fr), and Ukrainian (ua)
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';

// Import locale files
import en from './locales/en.json';
import fr from './locales/fr.json';
import ua from './locales/ua.json';

// Available locales
export const locales = {
  en: { name: 'English', flag: '🇺🇸', translations: en },
  fr: { name: 'Français', flag: '🇫🇷', translations: fr },
  ua: { name: 'Українська', flag: '🇺🇦', translations: ua },
};

export const defaultLocale = 'en';

// Get nested translation value
const getNestedValue = (obj, path) => {
  const keys = path.split('.');
  let value = obj;

  for (const key of keys) {
    if (value === undefined || value === null) {
      return undefined;
    }
    value = value[key];
  }

  return value;
};

// Interpolate variables in translation string
const interpolate = (str, params) => {
  if (!params || typeof str !== 'string') return str;

  return Object.entries(params).reduce((result, [key, value]) => {
    return result.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }, str);
};

// Create i18n context
const I18nContext = createContext(null);

/**
 * I18n Provider Component
 */
export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState(() => {
    // Try to get saved locale from localStorage
    const saved = localStorage.getItem('locale');
    if (saved && locales[saved]) {
      return saved;
    }

    // Try to detect browser language
    const browserLang = navigator.language.split('-')[0];
    if (locales[browserLang]) {
      return browserLang;
    }

    return defaultLocale;
  });

  // Update document lang attribute
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((newLocale) => {
    if (locales[newLocale]) {
      setLocaleState(newLocale);
      localStorage.setItem('locale', newLocale);
    }
  }, []);

  // Translation function
  const t = useCallback((key, params) => {
    const translations = locales[locale]?.translations || locales[defaultLocale].translations;
    let value = getNestedValue(translations, key);

    // Fallback to English if translation not found
    if (value === undefined && locale !== defaultLocale) {
      value = getNestedValue(locales[defaultLocale].translations, key);
    }

    // Return key if no translation found
    if (value === undefined) {
      console.warn(`Translation missing for key: ${key}`);
      return key;
    }

    return interpolate(value, params);
  }, [locale]);

  // Get all translations for a section
  const getSection = useCallback((section) => {
    const translations = locales[locale]?.translations || locales[defaultLocale].translations;
    return translations[section] || {};
  }, [locale]);

  const value = {
    locale,
    setLocale,
    t,
    getSection,
    locales: Object.entries(locales).map(([code, { name, flag }]) => ({
      code,
      name,
      flag,
    })),
    isRTL: false, // Add RTL support if needed later
  };

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
}

/**
 * Hook to use i18n in components
 */
export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}

/**
 * Hook for just the translation function
 */
export function useTranslation() {
  const { t } = useI18n();
  return t;
}

export default { I18nProvider, useI18n, useTranslation, locales, defaultLocale };
