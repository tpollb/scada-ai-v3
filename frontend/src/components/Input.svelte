<script lang="ts">
  import { Send, Mic, MicOff } from 'lucide-svelte'
  import { isVoiceActive } from '../stores/ui'

  export let onSend: (message: string) => void
  let message = ''

  function handleSubmit() {
    if (!message.trim()) return
    onSend(message)
    message = ''
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }
</script>

<div class="flex gap-2 p-4 border-t border-gray-200 bg-white">
  <button
    class="p-2 rounded-lg hover:bg-gray-100 transition"
    on:click={() => isVoiceActive.update(v => !v)}
    title={$isVoiceActive ? 'Выключить голос' : 'Включить голос'}
  >
    {#if $isVoiceActive}
      <Mic size={20} class="text-blue-600" />
    {:else}
      <MicOff size={20} class="text-gray-600" />
    {/if}
  </button>
  <input
    type="text"
    bind:value={message}
    on:keydown={handleKeydown}
    placeholder="Введите команду или вопрос..."
    class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
  />
  <button
    on:click={handleSubmit}
    disabled={!message.trim()}
    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
  >
    <Send size={20} class="text-white" />
  </button>
</div>
