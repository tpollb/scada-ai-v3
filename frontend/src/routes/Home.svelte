<script lang="ts">
  import { onMount } from 'svelte'
  import { getHealth } from '../lib/api'
  import { messages, isLoading, addMessage } from '../stores/chat'
  import { navigate } from '../stores/ui'
  import Input from '../components/Input.svelte'
  import NarrativePanel from '../components/NarrativePanel.svelte'
  import api from '../lib/api'
  import { Settings } from 'lucide-svelte'

  let health: any = null

  onMount(async () => {
    try { health = await getHealth() }
    catch (e) { console.error('Failed to fetch health:', e) }
  })

  async function handleSend(message: string) {
    addMessage('user', message)
    isLoading.set(true)
    try {
      const resp: any = await api.post('chat', { json: { message } }).json()
      addMessage('assistant', resp.response)
    } catch (e) {
      addMessage('system', 'Ошибка подключения к backend')
    } finally {
      isLoading.set(false)
    }
  }
</script>

<div class="flex flex-col h-screen bg-gray-50">
  <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <h1 class="text-xl font-bold text-gray-900">SCADA.AI v3.0.0</h1>
      {#if health}
        <span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded font-medium">
          {health.modules.length} модулей
        </span>
      {/if}
    </div>
    <div class="flex items-center gap-3">
      <button
        on:click={() => navigate('config')}
        class="p-2 rounded-lg hover:bg-gray-100 transition"
        title="Конфигуратор"
      >
        <Settings size={20} class="text-gray-700" />
      </button>
      <div class="flex items-center gap-2 text-sm text-gray-700">
        <span class="w-2 h-2 rounded-full bg-green-500"></span>
        <span class="font-medium">Online</span>
      </div>
    </div>
  </header>

  <div class="flex-1 flex overflow-hidden">
    <div class="flex-1 flex flex-col bg-white">
      <NarrativePanel />
      <Input onSend={handleSend} />
    </div>
    <aside class="w-80 border-l border-gray-200 bg-gray-50 hidden lg:flex lg:flex-col">
      <div class="p-4 border-b border-gray-200">
        <h2 class="font-semibold text-gray-900">Visual</h2>
        <p class="text-sm text-gray-600 mt-1">Здесь будут виджеты</p>
      </div>
      <div class="flex-1 p-4">
        <h2 class="font-semibold text-gray-900 mb-2">Command Log</h2>
        <div class="text-sm text-gray-700 font-mono">
          <p class="text-green-700">> system ready</p>
        </div>
      </div>
    </aside>
  </div>
</div>
