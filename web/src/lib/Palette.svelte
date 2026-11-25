<script>
  import { i18n } from './i18n.svelte.js'
  import { st, setFilters, ask } from './store.svelte.js'
  import { router } from './router.svelte.js'
  const t = i18n.t
  let q = $state(''), idx = $state(0), input = $state()
  const steps = ['data', 'mapping', 'clean', 'health', 'dashboard', 'actions', 'share']
  const cmds = $derived([
    ...steps.map((s) => ({ label: `${t('cmd_go')} ${t('s_' + s)}`, run: () => router.go('/studio/' + s) })),
    { label: t('cmd_dq'), run: () => router.go('/studio/health') },
    { label: t('cmd_reset'), run: () => setFilters({}) },
    { label: t('cmd_lang'), run: () => i18n.toggle() },
    { label: '5 outlet terlemah', run: () => ask('5 outlet terlemah') },
    { label: 'Top 10 outlet', run: () => ask('top 10 outlet') },
    { label: 'Bandingkan Sep vs Okt', run: () => ask('bandingkan sep vs okt') },
  ])
  const list = $derived(cmds.filter((c) => c.label.toLowerCase().includes(q.toLowerCase())))
  $effect(() => { if (st.palette) { q = ''; idx = 0; queueMicrotask(() => input?.focus()) } })
  $effect(() => { q; idx = 0 })
  function key(e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); st.palette = !st.palette; return }
    if (!st.palette) return
    if (e.key === 'Escape') st.palette = false
    else if (e.key === 'ArrowDown') { e.preventDefault(); idx = Math.min(idx + 1, list.length - 1) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); idx = Math.max(idx - 1, 0) }
    else if (e.key === 'Enter' && list[idx]) { e.preventDefault(); st.palette = false; list[idx].run() }
  }
</script>
<svelte:window onkeydown={key} />
{#if st.palette}
  <button class="scrim" aria-label={t('close')} onclick={() => (st.palette = false)}></button>
  <div class="pal" role="dialog" aria-label={t('palette')}>
    <input bind:this={input} bind:value={q} placeholder="{t('palette')}…" aria-label={t('palette')} />
    <ul role="listbox">
      {#each list as c, i}<li role="option" aria-selected={i === idx}><button class:on={i === idx} onclick={() => { st.palette = false; c.run() }}>{c.label}</button></li>{:else}<li class="mut">{t('cmd_none')}</li>{/each}
    </ul>
  </div>
{/if}
<style>
  .scrim{position:fixed;inset:0;background:rgba(0,0,0,.25);border:0;z-index:40}
  .pal{position:fixed;z-index:41;top:14vh;left:50%;transform:translateX(-50%);width:min(520px,92vw);background:var(--paper);border:var(--border);border-radius:12px;overflow:hidden}
  input{width:100%;border:0;border-bottom:var(--border);padding:16px 18px;font:inherit;font-size:16px;outline:none}
  ul{list-style:none;margin:0;padding:6px;max-height:50vh;overflow:auto}li button{width:100%;text-align:left;background:none;border:0;padding:12px;border-radius:8px;font:inherit;cursor:pointer;min-height:44px}
  li button.on,li button:hover{background:var(--grey-100)}.mut{color:var(--grey-600);padding:12px}
</style>
