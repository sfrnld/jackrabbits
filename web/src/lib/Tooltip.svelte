<script>
  import { tip } from './tip.svelte.js'
  const left = $derived(Math.min(tip.x + 14, innerWidth - 240))
</script>
{#if tip.show}
  <div class="tip" role="tooltip" style="left:{left}px;top:{tip.y + 14}px">
    {#each tip.lines as l, i}<div class:h={i === 0}>{l}</div>{/each}
  </div>
{/if}
<style>
  .tip{position:fixed;z-index:50;pointer-events:none;background:var(--ink);color:var(--paper);padding:8px 12px;border-radius:6px;font-size:13px;line-height:1.4;max-width:230px}
  .h{font-weight:600}
</style>
