<script lang="ts">
  import { navigate } from '../stores/ui'
  import { ArrowLeft, Settings } from 'lucide-svelte'
</script>

<div class="flex flex-col h-screen bg-gray-50">
  <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4">
    <button
      on:click={() => navigate('operator')}
      class="p-2 rounded-lg hover:bg-gray-100 transition text-gray-700"
      title="Вернуться к работе"
    >
      <ArrowLeft size={20} class="text-gray-700" />
    </button>
    <div class="flex items-center gap-3">
      <Settings size={24} class="text-gray-700" />
      <h1 class="text-xl font-bold text-gray-900">Конфигуратор</h1>
    </div>
  </header>

  <div class="flex-1 p-8 max-w-4xl mx-auto w-full">
    <div class="bg-white rounded-lg shadow p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4 text-gray-900">Модули</h2>
      <div class="space-y-2">
        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
          <div>
            <p class="font-medium text-gray-900">hello</p>
            <p class="text-sm text-gray-600">Тестовый модуль v1.0.0</p>
          </div>
          <span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded font-medium">active</span>
        </div>
        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
          <div>
            <p class="font-medium text-gray-900">health</p>
            <p class="text-sm text-gray-600">Анализ здоровья здания</p>
          </div>
          <span class="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded font-medium">coming soon</span>
        </div>
        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
          <div>
            <p class="font-medium text-gray-900">schedules</p>
            <p class="text-sm text-gray-600">Управление расписаниями</p>
          </div>
          <span class="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded font-medium">coming soon</span>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4 text-gray-900">Система</h2>
      <div class="space-y-3 text-sm">
        <div class="flex justify-between items-center">
          <span class="text-gray-700 font-medium">Версия:</span>
          <span class="font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">3.0.0</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-gray-700 font-medium">SCADA API:</span>
          <span class="font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">http://localhost:9002</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-gray-700 font-medium">LLM:</span>
          <span class="font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">yandexgpt/latest</span>
        </div>
      </div>
    </div>
  </div>
</div>
