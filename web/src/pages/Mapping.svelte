<script>
  import { i18n } from '../lib/i18n.svelte.js'
  import { st, confirmMapping, reloadSheet } from '../lib/store.svelte.js'
  import Page from '../lib/Page.svelte'
  const t = i18n.t
  const ROLES = ['date', 'invoice', 'region', 'branch', 'outlet_id', 'outlet_name', 'outlet_type', 'salesman', 'brand', 'sku', 'qty', 'price', 'gross', 'discount', 'net']
  const REQ = ['date', 'outlet_id', 'net']
  let busy = $state(false)
  const cols = $derived(st.info?.columns ?? [])
  const missing = $derived([!st.mapping.date && 'date', !(st.mapping.outlet_id || st.mapping.outlet_name) && 'outlet_id', !(st.mapping.net || st.mapping.gross) && 'net'].filter(Boolean))
  const conf = (r) => { const g = st.info.mapping[r]; return st.mapping[r] ? (g && g.column === st.mapping[r] ? g.confidence : 1) : null }
  const sample = (r) => { const c = st.mapping[r]; return c ? [...new Set(st.info.preview.map((p) => p[c]).filter(Boolean))].slice(0, 3).join(' · ') : '' }
  const go = async () => { busy = true; try { await confirmMapping() } finally { busy = false } }
</script>
<Page wide title={t('m_title')} lead={t('m_p')} asideTitle={t('m_preview')} asideSub={st.info ? `${st.info.name} · ${st.info.rows.toLocaleString('id-ID')} ${t('c_rows')}` : ''}>
{#if st.info}
{#if st.info.sheets.length > 1}
  <label class="sheet">{t('d_sheet')}: <select onchange={(e) => reloadSheet(e.currentTarget.value)}>{#each st.info.sheets as s}<option>{s}</option>{/each}</select></label>
{/if}
<div class="tw"><table>
  <thead><tr><th>{t('m_role')}</th><th>{t('m_col')}</th><th>{t('m_conf')}</th><th class="ex">{t('m_example')}</th></tr></thead>
  <tbody>
    {#each ROLES as r}
      {@const c = conf(r)}
      <tr>
        <td><b>{t('r_' + r)}</b>{#if REQ.includes(r)}<small> · {t('m_req') ?? ''}</small>{/if}</td>
        <td><select bind:value={st.mapping[r]} aria-label={t('r_' + r)}><option value="">{t('m_none')}</option>{#each cols as col}<option>{col}</option>{/each}</select></td>
        <td>{#if c == null}<span class="b {REQ.includes(r) ? 'bad' : 'mut'}">{REQ.includes(r) ? '▲ ' + t('m_missing').replace(': ', '') : '—'}</span>{:else if c >= 0.9}<span class="b ok">✓ {Math.round(c * 100)}%</span>{:else}<span class="b bad">▲ {Math.round(c * 100)}%</span>{/if}</td>
        <td class="ex">{sample(r)}</td>
      </tr>
    {/each}
  </tbody>
</table></div>
<p class="mut">{t('m_hidden')}{ROLES.filter((r) => !st.mapping[r] && !REQ.includes(r)).map((r) => t('r_' + r)).join(', ') || '—'}</p>
{/if}

{#snippet aside()}
  {#if st.info}<p class="mut">{st.info.name} · {st.info.rows.toLocaleString('id-ID')} {t('c_rows')} · {cols.length} {t('m_cols')}</p>
  <div class="tw"><table class="pv"><thead><tr>{#each cols as c}<th>{c}</th>{/each}</tr></thead><tbody>{#each st.info.preview.slice(0, 15) as r}<tr>{#each cols as c}<td>{r[c] ?? ''}</td>{/each}</tr>{/each}</tbody></table></div>{/if}
{/snippet}
{#snippet footer()}
  {#if missing.length}<span class="err" role="alert">▲ {t('m_missing')}{missing.map((m) => t('r_' + m)).join(', ')}</span>{/if}
  <span class="sp"></span>
  <button class="btn" disabled={missing.length > 0 || busy || !st.info} onclick={go}>{t('m_confirm')}</button>
{/snippet}
</Page>
<style>
  h1{font-size:26px;margin:0 0 var(--s2)}.lead{color:var(--grey-600);margin:0 0 var(--s6)}.sheet{display:block;margin-bottom:var(--s4)}
  .tw{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;color:var(--grey-600);font-weight:500;padding:8px}td{padding:8px;border-top:var(--border);vertical-align:middle}
  select{min-height:40px;border:1px solid var(--grey-200);border-radius:6px;padding:0 8px;font:inherit;background:var(--paper);max-width:100%}select:focus{border-color:var(--ink);outline:none}
  small,.mut,.ex{color:var(--grey-600)}.ex{font-size:12.5px;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .b{font-size:13px;font-weight:500}.ok{color:var(--ok-green)}.bad{color:var(--alert-red)}.err{color:var(--alert-red);font-weight:500}
  .btn{margin-top:var(--s4)}.btn:disabled{opacity:.35;cursor:not-allowed}
  @media (max-width:700px){.ex{display:none}}
  .pv{font-size:12.5px;white-space:nowrap}.pv th,.pv td{padding:5px 8px}
</style>
