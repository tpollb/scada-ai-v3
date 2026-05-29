import { writable } from 'svelte/store'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export const messages = writable<Message[]>([])
export const isLoading = writable(false)

export function addMessage(role: Message['role'], content: string) {
  messages.update(msgs => [...msgs, {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: Date.now()
  }])
}

export function clearMessages() {
  messages.set([])
}
