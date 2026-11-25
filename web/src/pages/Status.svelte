<script>
  import { onMount, onDestroy } from 'svelte'
  import { i18n } from '../lib/i18n.svelte.js'
  import { router } from '../lib/router.svelte.js'
  import { api } from '../lib/api.js'
  const t = i18n.t
  let lines = $state([]), err = $state(false), copied = $state(false), box, tm
  async function load() {
    try { lines = (await api('/status')).log; err = false; queueMicrotask(() => box && (box.scrollTop = box.scrollHeight)) } catch { err = true }
  }
  onMount(() => { load(); tm = setInterval(load, 2000) })
  onDestroy(() => clearInterval(tm))
  async function copy() { await navigator.clipboard?.writeText(lines.join('\n')); copied = true; setTimeout(() => (copied = false), 1500) }
</script>
<header class="top"><strong>Sales Studio</strong><span class="crumb">Status</span>
  <button class="lk" onclick={() => router.go(localStorage.getItem('setupDone') ? '/studio' : '/setup')}>← {t('s_dashboard') === 'Dashboard' ? 'Kembali' : 'Back'}</button></header>
<main>
  <h1>Status</h1>
  <p class="lead">{t('st_p')}</p>
  {#if err}<p class="err" role="alert">▲ {t('st_down')}</p>{:else}<p class="ok">✓ {t('st_up')}</p>{/if}
  <pre bind:this={box} aria-label="Log" aria-live="off">{lines.length ? lines.join('\n') : '—'}</pre>
  <button class="btn secondary" onclick={copy}>{copied ? '✓ ' + t('db_copied') : t('sh_copy')}</button>
</main>
<style>
  .top{display:flex;gap:var(--s4);align-items:center;padding:0 var(--s6);min-height:56px;border-bottom:var(--border)}.crumb{flex:1;color:var(--grey-600)}
  .lk{background:none;border:0;cursor:pointer;color:var(--grey-600);font:inherit;min-height:44px}.lk:hover{color:var(--ink)}
  main{max-width:820px;margin:0 auto;padding:var(--s8) var(--s6)}h1{font-size:26px;margin:0 0 var(--s2)}.lead{color:var(--grey-600)}
  pre{background:var(--grey-50);border:var(--border);border-radius:8px;padding:var(--s4);font:12.5px/1.6 var(--mono);height:50vh;overflow:auto;white-space:pre-wrap;margin:var(--s4) 0}
  .ok{color:var(--ok-green);font-weight:500}.err{color:var(--alert-red);font-weight:500}.btn{padding:0 var(--s6)}
</style>
