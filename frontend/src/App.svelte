<script lang="ts">
  import { currentPage } from './stores/ui'
  import Home from './routes/Home.svelte'
  import Config from './routes/Config.svelte'
  import './app.css'
</script>

{#if $currentPage === 'operator'}
  <Home />
{:else if $currentPage === 'config'}
  <Config />
{:else}
  <Home />
{/if}
