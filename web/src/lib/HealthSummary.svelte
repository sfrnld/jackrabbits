<script>
  import { i18n } from './i18n.svelte.js'
  import { st } from './store.svelte.js'
  import { rpFull, num } from './fmt.js'
  const t = i18n.t
  const s = $derived(st.fs?.summary)
  const row = (k, f) => [t(k), f(s.before), f(s.after), s.before && s.after]
</script>
{#if s}
  <table class="ba">
    <thead><tr><th></th><th>{t('h_before')}</th><th>{t('h_after')}</th><th>{t('h_change')}</th></tr></thead>
    <tbody>
      {#each [['h_rows', 'h_d_rows', 'rows', num, num], ['h_net', 'h_d_net', 'net', rpFull, rpFull], ['h_regions', 'h_d_regions', 'regions', (x) => x, (x) => x], ['h_outlets', 'h_d_outlets', 'outlets', (x) => x, (x) => x]] as [k, d, f, fmt, dfmt]}
        {@const dv = s.after[f] - s.before[f]}
        <tr class:big={f === 'net'}><td><b>{t(k)}</b><small class="d">{t(d)}</small></td><td class="num">{fmt(s.before[f])}</td><td class="num"><b>{fmt(s.after[f])}</b></td>
          <td class="num ch" class:zero={dv === 0}>{dv === 0 ? '—' : (dv > 0 ? '+' : '−') + dfmt(Math.abs(dv))}</td></tr>
      {/each}
    </tbody>
  </table>
  <div class="means"><b>{t('h_means')}</b><p>{t('h_means_txt')}</p></div>
  {#if st.fs.pending.length}<p class="warn">▲ {st.fs.pending.length} {t('h_pending')}</p>{/if}
  <h3>{t('h_trail')}</h3>
  {#if st.fs.trail.length}
    <ol class="trail">{#each st.fs.trail as x}<li><b>{x.title}</b><br /><span>{x.label}</span> <small>· {x.rows_changed} {t('c_rows')}</small></li>{/each}</ol>
  {:else}<p class="mut">{t('h_none')}</p>{/if}
{/if}
<style>
  .ba{width:100%;border-collapse:collapse;font-size:14px}th{text-align:right;color:var(--grey-600);font-weight:500;padding:6px 8px}
  td{padding:10px 8px;border-top:var(--border)}td.num{text-align:right}.big td{font-size:15px}
  .warn{color:var(--alert-red);font-weight:500}.mut,small,span{color:var(--grey-600)}h3{font-size:14px;margin:var(--s6) 0 var(--s2)}
  .trail{padding-left:20px;font-size:14px}.trail li{margin-bottom:var(--s3)}
.d{display:block;font-size:12.5px;font-weight:400;color:var(--grey-600)}.ch{font-weight:600;white-space:nowrap}.ch.zero{color:var(--grey-400);font-weight:400}.means{margin:var(--s4) 0 0;padding:var(--s3) var(--s4);background:var(--grey-100);border-left:3px solid var(--ink);border-radius:6px}.means b{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--grey-600)}.means p{margin:var(--s1) 0 0;font-size:14px;line-height:1.55}
</style>
