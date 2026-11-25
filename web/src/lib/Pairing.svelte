<script>
  // Creates a Telegram invite (QR + deep link) and polls until the person presses Start.
  import { onMount, onDestroy } from 'svelte'
  import { i18n } from './i18n.svelte.js'
  import { api } from './api.js'
  let { draft, onpaired = () => {} } = $props()
  const t = i18n.t
  let inv = $state(null), phase = $state('creating'), rec = $state(null), err = $state(''), copied = $state(false), timer
  onMount(async () => {
    try { inv = await api('/telegram/invite', draft); phase = 'waiting'; timer = setInterval(poll, 2000) }
    catch (e) { err = e.detail?.message ?? 'Gagal membuat undangan'; phase = 'error' }
  })
  async function poll() {
    try {
      const r = await api('/telegram/invite/' + inv.code)
      if (r.status === 'paired') { clearInterval(timer); rec = r.recipient; phase = 'paired'; onpaired(rec) }
      else if (r.status === 'expired') { clearInterval(timer); phase = 'error'; err = 'Undangan kedaluwarsa' }
    } catch {}
  }
  onDestroy(() => clearInterval(timer))
  async function copy() { await navigator.clipboard?.writeText(inv.link); copied = true; setTimeout(() => (copied = false), 1500) }
</script>
<div class="pr" aria-live="polite">
  {#if phase === 'creating'}<p class="mut">{t('tg_checking')}</p>
  {:else if phase === 'error'}<p class="err" role="alert">▲ {err}</p>
  {:else if phase === 'waiting'}
    <img src={inv.qr} alt="QR Telegram" width="180" height="180" />
    <div class="side"><a class="btn" href={inv.link} target="_blank" rel="noopener noreferrer">{t('tg_open')}</a>
      <button class="btn secondary" onclick={copy}>{copied ? '✓ ' + t('db_copied') : t('tg_copy_link')}</button>
      <p class="mut"><span class="pulse" aria-hidden="true"></span> {t('tg_waiting')}</p></div>
  {:else}
    <div class="ok"><b>✓ {t('tg_found')}{rec.first_name || rec.name}</b><p>{t('tg_found_p')}</p></div>
  {/if}
</div>
<style>
  .pr{display:flex;gap:var(--s6);align-items:center;flex-wrap:wrap;padding:var(--s4);border:var(--border);border-radius:var(--radius)}
  img{border:var(--border);border-radius:8px}.side{display:flex;flex-direction:column;gap:var(--s3);align-items:flex-start}
  .btn{display:inline-flex;align-items:center;text-decoration:none;padding:0 var(--s6)}.btn.secondary{padding:0 var(--s6)}
  .mut{color:var(--grey-600);margin:0}.err{color:var(--alert-red);margin:0}.ok{color:var(--ok-green)}.ok p{margin:4px 0 0;color:var(--grey-600)}
  .pulse{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--ink);animation:p 1.2s ease-in-out infinite}
  @keyframes p{50%{opacity:.25}}@media (prefers-reduced-motion:reduce){.pulse{animation:none}}
</style>
