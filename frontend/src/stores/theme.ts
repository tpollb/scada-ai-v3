import { writable } from 'svelte/store'

type Theme = 'light' | 'dark'

function createThemeStore() {
  const initial: Theme = (typeof window !== 'undefined' && localStorage.getItem('theme') === 'dark') ? 'dark' : 'light'
  const { subscribe, set, update } = writable<Theme>(initial)

  return {
    subscribe,
    toggle: () => update(t => {
      const next = t === 'light' ? 'dark' : 'light'
      if (typeof window !== 'undefined') {
        localStorage.setItem('theme', next)
        document.documentElement.classList.toggle('dark', next === 'dark')
      }
      return next
    }),
    set: (theme: Theme) => {
      if (typeof window !== 'undefined') {
        localStorage.setItem('theme', theme)
        document.documentElement.classList.toggle('dark', theme === 'dark')
      }
      set(theme)
    },
    init: () => {
      if (typeof window !== 'undefined') {
        const saved = localStorage.getItem('theme') as Theme | null
        const theme = saved || 'light'
        document.documentElement.classList.toggle('dark', theme === 'dark')
        set(theme)
      }
    }
  }
}

export const theme = createThemeStore()
