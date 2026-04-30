import { create } from 'zustand';
import fr from './fr.json';
import en from './en.json';

type Locale = 'fr' | 'en';
type Translations = typeof fr;

interface TranslationStore {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export const useTranslationStore = create<TranslationStore>((set) => ({
  locale: 'fr', // Default
  setLocale: (locale) => set({ locale }),
}));

// Extremely simple path-based object resolver (e.g. "assistant.title")
const getNestedValue = (obj: any, path: string, params?: Record<string, string | number>): string => {
  const keys = path.split('.');
  let current = obj;
  for (const key of keys) {
    if (current[key] === undefined) return path; // fallback to path
    current = current[key];
  }
  
  let result = current as string;
  if (params && typeof result === 'string') {
    for (const [key, value] of Object.entries(params)) {
      result = result.replace(`{{${key}}}`, String(value));
    }
  }
  return result;
};

export const useAssistantTranslation = () => {
  const { locale, setLocale } = useTranslationStore();
  const translations: Record<Locale, Translations> = { fr, en };

  const t = (path: string, params?: Record<string, string | number>) => {
    return getNestedValue(translations[locale], path, params);
  };

  return { t, locale, setLocale };
};
