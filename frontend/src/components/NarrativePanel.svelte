<script lang="ts">
  import { messages } from '../stores/chat'
  import { User, Bot } from 'lucide-svelte'
</script>

<div class="flex-1 overflow-y-auto p-4 space-y-4">
  {#each $messages as msg (msg.id)}
    <div class="flex gap-3 {msg.role === 'user' ? 'justify-end' : ''}">
      {#if msg.role === 'assistant'}
        <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
          <Bot size={16} class="text-blue-600" />
        </div>
      {/if}
      <div class="max-w-[70%] px-4 py-2 rounded-2xl {msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'}">
        <p class="whitespace-pre-wrap">{msg.content}</p>
        <p class="text-xs mt-1 opacity-60">{new Date(msg.timestamp).toLocaleTimeString()}</p>
      </div>
      {#if msg.role === 'user'}
        <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
          <User size={16} class="text-gray-700" />
        </div>
      {/if}
    </div>
  {/each}

  {#if $messages.length === 0}
    <div class="text-center text-gray-600 mt-20">
      <Bot size={48} class="mx-auto mb-4 text-gray-400" />
      <p class="text-gray-700 font-medium">Начните диалог</p>
      <p class="text-sm text-gray-500 mt-1">Например: "привет"</p>
    </div>
  {/if}
</div>
