import { browser } from '$app/environment';
import { getLocale, getTextDirection, locales, setLocale } from '$lib/paraglide/runtime';

export type AppLocale = (typeof locales)[number];

export const localeOptions: Array<{ value: AppLocale; label: string }> = [
  { value: 'en', label: 'English' },
  { value: 'sw', label: 'Kiswahili' },
  { value: 'fr', label: 'Francais' },
  { value: 'ar', label: 'Arabic' },
  { value: 'pt', label: 'Portuguese' },
];

export function currentLocale(): AppLocale {
  return getLocale() as AppLocale;
}

export function currentTextDirection(): 'ltr' | 'rtl' {
  return getTextDirection(currentLocale());
}

export function isSupportedLocale(value: string): value is AppLocale {
  return (locales as readonly string[]).includes(value);
}

export function changeLocale(value: string): void {
  if (!isSupportedLocale(value)) return;
  if (browser) {
    localStorage.setItem('PARAGLIDE_LOCALE', value);
    document.cookie = `PARAGLIDE_LOCALE=${value}; path=/; max-age=34560000`;
    setLocale(value, { reload: false });
    window.location.reload();
    return;
  }

  setLocale(value);
}
