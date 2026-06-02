import { writable } from 'svelte/store'

export type Page = 'operator' | 'config'

export const currentPage = writable<Page>('operator')
export const isVoiceActive = writable(false)
export const isListening = writable(false)
export const isSpeaking = writable(false)

function safeParse(value: string | null, fallback: any): any {
  if (value === null || value === undefined) return fallback
  try {
    return JSON.parse(value)
  } catch {
    // Если не JSON (например "light" или "dark") — возвращаем как есть
    return value
  }
}

function createLocalStore<T>(key: string, initial: T) {
  const stored = typeof window !== 'undefined' ? localStorage.getItem(key) : null
  const store = writable<T>(safeParse(stored, initial))
  store.subscribe(value => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(key, JSON.stringify(value))
      } catch (e) {
        console.error('Failed to save to localStorage:', e)
      }
    }
  })
  return store
}

export const voiceEnabled = createLocalStore('voice_enabled', true)
// ВАЖНО: тема теперь управляется через stores/theme.ts, НЕ через createLocalStore
// export const theme = createLocalStore('theme', 'light')  // УДАЛЕНО — дубль

export function navigate(page: Page) {
  currentPage.set(page)
}
