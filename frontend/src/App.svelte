<script lang="ts">
  import { onMount } from 'svelte'
  import { theme } from './stores/theme'
  import { currentPage } from './stores/ui'
  import { auth } from './stores/auth'
  import Home from './routes/Home.svelte'
  import Config from './routes/Config.svelte'
  import LoginModal from './components/LoginModal.svelte'

  onMount(async () => {
    theme.init()
    // Инициализировать состояние аутентификации
    await auth.init()
  })
</script>

<main class="h-screen">
  {#if !$auth.isAuthenticated && !$auth.isLoading}
    <LoginModal />
  {:else if $currentPage === 'operator'}
    <Home />
  {:else if $currentPage === 'config'}
    <Config />
  {:else}
    <Home />
  {/if}
</main>
