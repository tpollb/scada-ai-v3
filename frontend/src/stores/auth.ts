/**
 * Store для управления состоянием аутентификации
 */
import { writable, derived } from 'svelte/store'
import api, { type User, type TokenResponse } from '../lib/api'

export interface AuthState {
  isAuthenticated: boolean
  user: User | null
  token: string | null
  permissions: string[]
  isLoading: boolean
  error: string | null
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  permissions: [],
  isLoading: true,
  error: null,
}

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>(initialState)

  return {
    subscribe,

    /**
     * Инициализация состояния при загрузке приложения
     */
    async init() {
      // Проверить есть ли сохранённый токен в localStorage
      const savedToken = typeof window !== 'undefined' 
        ? localStorage.getItem('auth_token') 
        : null

      if (savedToken) {
        api.setToken(savedToken)
        try {
          // Попытаться получить данные пользователя
          const user = await api.getCurrentUser()
          const permissions = await api.getPermissions()
          
          set({
            isAuthenticated: true,
            user,
            token: savedToken,
            permissions,
            isLoading: false,
            error: null,
          })
          return true
        } catch (error) {
          // Токен недействителен - очистить
          console.warn('Invalid token, clearing auth state')
          localStorage.removeItem('auth_token')
          api.setToken(null)
        }
      }

      // Нет токена или он недействителен
      set({
        ...initialState,
        isLoading: false,
      })
      return false
    },

    /**
     * Вход в систему
     */
    async login(username: string, password: string): Promise<void> {
      update(state => ({ ...state, isLoading: true, error: null }))

      try {
        const tokenData: TokenResponse = await api.login({ username, password })
        
        // Сохранить токен в localStorage
        if (typeof window !== 'undefined') {
          localStorage.setItem('auth_token', tokenData.access_token)
        }

        // Получить данные пользователя и разрешения
        const user = await api.getCurrentUser()
        const permissions = await api.getPermissions()

        set({
          isAuthenticated: true,
          user,
          token: tokenData.access_token,
          permissions,
          isLoading: false,
          error: null,
        })
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Login failed'
        update(state => ({
          ...state,
          isLoading: false,
          error: errorMessage,
        }))
        throw error
      }
    },

    /**
     * Выход из системы
     */
    logout() {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
      }
      api.logout()
      set(initialState)
    },

    /**
     * Проверка наличия разрешения
     */
    hasPermission(permission: string): boolean {
      let hasPerm = false
      this.subscribe(state => {
        hasPerm = state.permissions.includes(permission)
      })()
      return hasPerm
    },

    /**
     * Проверка роли пользователя
     */
    hasRole(role: string): boolean {
      let hasRole = false
      this.subscribe(state => {
        hasRole = state.user?.role === role
      })()
      return hasRole
    },

    /**
     * Очистить ошибку
     */
    clearError() {
      update(state => ({ ...state, error: null }))
    },
  }
}

export const auth = createAuthStore()

/**
 * Derived store для проверки наличия любого разрешения из списка
 */
export function hasAnyPermission(permissions: string[]) {
  return derived(auth, $auth => 
    permissions.some(p => $auth.permissions.includes(p))
  )
}

/**
 * Derived store для проверки наличия всех разрешений из списка
 */
export function hasAllPermissions(permissions: string[]) {
  return derived(auth, $auth => 
    permissions.every(p => $auth.permissions.includes(p))
  )
}

/**
 * Derived store для проверки роли
 */
export function isRole(role: string) {
  return derived(auth, $auth => $auth.user?.role === role)
}

/**
 * Список доступных ролей
 */
export type UserRole = 'admin' | 'engineer' | 'operator' | 'boss'

/**
 * Маппинг ролей к описанию
 */
export const ROLE_DESCRIPTIONS: Record<UserRole, string> = {
  admin: 'Администратор',
  engineer: 'Инженер',
  operator: 'Оператор',
  boss: 'Руководитель',
}
