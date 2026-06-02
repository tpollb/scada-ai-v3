<script lang="ts">
  import { onMount } from 'svelte'
  import { theme } from './stores/theme'
  import { currentPage } from './stores/ui'
  import Home from './routes/Home.svelte'
  import Config from './routes/Config.svelte'

  onMount(() => {
    theme.init()
  })
</script>

<main class="h-screen">
  {#if $currentPage === 'operator'}
    <Home />
  {:else if $currentPage === 'config'}
    <Config />
  {:else}
    <Home />
  {/if}
</main>
