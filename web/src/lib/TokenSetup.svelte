<script>
  // Shows Telegram connection state; asks for the BotFather token when none is configured.
  import { onMount } from 'svelte'
  import { i18n } from './i18n.svelte.js'
  import { api } from './api.js'
  let { status = $bindable(null), onchange = () => {} } = $props()
  const t = i18n.t
  let token = $state(''), busy = $state(false), err = $state('')
  export async function refresh() { try { status = await api('/telegram/status') } catch { status = { configured: false, online: false, bot: null } } onchange(status) }
  onMount(refresh)
  async function save() {
    busy = true; err = ''
    try { await api('/telegram/token', { token }); token = ''; await refresh() }
    catch (e) { err = e.detail?.message ?? 'Token tidak valid'; if (e.detail?.offline) await refresh() } finally { busy = false }
  }
</script>
{#if !status}<p class="mut">{t('tg_checking')}</p>
{:else if !status.configured}
  <div class="box"><h3>{t('tg_token_h')}</h3><p class="mut">{t('tg_token_p')}</p>
    <form onsubmit={(e) => { e.preventDefault(); save() }}>
      <input type="password" bind:value={token} placeholder={t('tg_token_ph')} aria-label={t('tg_token_ph')} autocomplete="off" spellcheck="false" />
      <button class="btn" disabled={!token.trim() || busy}>{t('tg_token_save')}</button>
    </form>
    {#if err}<p class="err" role="alert">▲ {err}</p>{/if}<p class="note">{t('tg_token_note')}</p></div>
{:else if !status.online}
  <p class="err" role="alert">▲ {t('tg_offline')}</p><button class="btn secondary" onclick={refresh}>{t('retry')}</button>
{:else}
  <p class="ok">✓ {t('tg_connected')} · {t('tg_bot')} @{status.bot.username}</p>
{/if}
<style>
  .box{border:var(--border);border-radius:var(--radius);padding:var(--s4)}h3{margin:0 0 var(--s2);font-size:16px}
  form{display:flex;gap:var(--s2);flex-wrap:wrap}input{flex:1;min-width:200px;min-height:44px;border:1px solid var(--grey-200);border-radius:var(--radius);padding:0 var(--s3);font:inherit}input:focus{border-color:var(--ink);outline:none}
  .btn{padding:0 var(--s6)}.btn:disabled{opacity:.35;cursor:not-allowed}.mut,.note{color:var(--grey-600)}.note{font-size:13px;margin:var(--s3) 0 0}.err{color:var(--alert-red)}.ok{color:var(--ok-green);font-weight:500;margin:0}
</style>
