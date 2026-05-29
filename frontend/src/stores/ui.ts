import { writable } from 'svelte/store'

export type Page = 'operator' | 'config'

export const currentPage = writable<Page>('operator')
export const isVoiceActive = writable(false)
export const isListening = writable(false)
export const isSpeaking = writable(false)

function createLocalStore<T>(key: string, initial: T) {
  const stored = typeof window !== 'undefined' ? localStorage.getItem(key) : null
  const store = writable<T>(stored ? JSON.parse(stored) : initial)
  store.subscribe(value => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(key, JSON.stringify(value))
    }
  })
  return store
}

export const voiceEnabled = createLocalStore('voice_enabled', true)
export const theme = createLocalStore('theme', 'light')

export function navigate(page: Page) {
  currentPage.set(page)
}
