<script>
  import { router } from './lib/router.svelte.js'
  import Setup from './Setup.svelte'
  import Studio from './Studio.svelte'
  import Status from './pages/Status.svelte'
  import Tooltip from './lib/Tooltip.svelte'
  const p = $derived(router.path)
  $effect(() => { if (p === '/' || p === '/index.html') router.go(localStorage.getItem('setupDone') ? '/studio' : '/setup', true) })
</script>
{#if p.startsWith('/studio')}<Studio />{:else if p.startsWith('/status')}<Status />{:else}<Setup />{/if}
<Tooltip />
