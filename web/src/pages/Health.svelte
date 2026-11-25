<script>
  import { i18n } from '../lib/i18n.svelte.js'
  import { st } from '../lib/store.svelte.js'
  import { router } from '../lib/router.svelte.js'
  import { num, rpFull } from '../lib/fmt.js'
  import HealthSummary from '../lib/HealthSummary.svelte'
  import DataTable from '../lib/DataTable.svelte'
  import Page from '../lib/Page.svelte'
  const t = i18n.t
  const label = (f) => f.options.find((o) => o.id === f.decision?.option)?.label
</script>
<Page wide title={t('h_title')} lead={t('h_lead')} asideTitle={t('c_tbl_involved')} asideSub={t('h_aside_sub')}>
<div class="card wrap"><HealthSummary /></div>

{#if st.fs?.findings.length}
  <h2>{t('h_detail')}</h2>
  {#each st.fs.findings as f (f.id)}
    <article class="card f" class:pend={!f.decision}>
      <header>
        <h3>{f.title}</h3>
        <span class="chip {f.decision ? 'ok' : 'bad'}">{f.decision ? '✓ ' + t('c_applied') : '⚠️ ' + t('c_pending')}</span>
      </header>
      <p class="imp"><b>{num(f.impact_rows)} {t('c_rows')}</b>{#if f.impact_rp}&nbsp;· <span class="num">{rpFull(f.impact_rp)}</span>{/if}
        {#if f.decision}&nbsp;· {t('h_decision')}: <b>{label(f)}</b>{/if}</p>
      {#if !f.decision}<p class="und">⚠️ {t('h_undecided')} <button class="lk" onclick={() => router.go('/studio/clean')}>{t('h_goto')}</button></p>{/if}
    </article>
  {/each}
{/if}

{#snippet aside()}
  {#each st.fs?.findings ?? [] as f (f.id)}<h3 class="at">{f.title} <span class="stat {f.decision ? 'ok' : 'bad'}">{f.decision ? '✓ ' + t('c_applied') : '⚠️ ' + t('c_pending')}</span></h3><DataTable table={f.table} chosen={f.decision?.option} mode={f.decision ? 'result' : 'decide'} />{/each}
{/snippet}
{#snippet footer()}
  <span class="sp"></span>
  <button class="btn" onclick={() => router.go('/studio/dashboard')}>{t('h_open')}</button>
{/snippet}
</Page>
<style>
  h1{font-size:26px;margin:0 0 var(--s6)}h2{font-size:18px;margin:var(--s8) 0 var(--s3)}h3{margin:0;font-size:16px}.wrap{margin-bottom:var(--s4)}
  .f{margin-bottom:var(--s4)}.f.pend{border-left:3px solid var(--alert-red)}
  header{display:flex;justify-content:space-between;align-items:center;gap:var(--s3);flex-wrap:wrap}
  .chip{font-size:12.5px;font-weight:500;padding:3px 10px;border-radius:99px}.chip.ok{background:var(--ok-green-bg);color:var(--ok-green)}.chip.bad{background:var(--alert-red-bg);color:var(--alert-red)}
  .imp{margin:var(--s2) 0}.und{margin:var(--s2) 0 0;font-size:13.5px;color:var(--alert-red)}.lk{background:none;border:0;text-decoration:underline;cursor:pointer;color:var(--ink);font:inherit;min-height:32px}
  .btn{margin-top:var(--s4)}
  .at{font-size:14px;margin:var(--s4) 0 var(--s2);display:flex;gap:var(--s2);align-items:center;flex-wrap:wrap}.at:first-child{margin-top:0}
</style>
