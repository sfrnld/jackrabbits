<script>
  import { i18n } from '../lib/i18n.svelte.js'
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { L } from '../lib/i18n.svelte.js'
  import { st, pickSample, uploadFile } from '../lib/store.svelte.js'
  import Page from '../lib/Page.svelte'
  const t = i18n.t
  let drag = $state(false), busy = $state(false), input, hasSample = $state(true)
  onMount(async () => { hasSample = (await api('/data/sample').catch(() => ({ available: true }))).available })
  async function go(file) { if (!file) return; busy = true; try { await uploadFile(file) } catch {} finally { busy = false } }
</script>
<Page title={t('s_data')} lead={t('d_privacy')}>
{#if st.notice}<p class="err" role="alert">▲ {t('d_err')}: {st.notice}</p>{/if}
<div class="two">
  {#if hasSample}
  <button class="card pick" onclick={pickSample} disabled={busy}>
    <h2>{t('d_sample_t')}</h2><p>{t('d_sample_p')}</p><span class="btn">{t('start')}</span>
  </button>
  {:else}
  <div class="card nosample" role="note">
    <h2>{L('Data contoh tidak ditemukan', 'Sample data not found')}</h2>
    <p>{L('File data/sales.csv tidak ada di folder aplikasi ini (mungkin tidak ikut di-download). Tidak masalah: unggah file penjualanmu sendiri di samping (CSV, Excel, JSON, atau Parquet).', 'The file data/sales.csv is not in this app folder (it may not have been downloaded). No problem: upload your own sales file next to it (CSV, Excel, JSON or Parquet).')}</p>
  </div>
  {/if}
  <div class="card drop" class:drag role="group" aria-label={t('d_upload_t')}
       ondragover={(e) => { e.preventDefault(); drag = true }} ondragleave={() => (drag = false)}
       ondrop={(e) => { e.preventDefault(); drag = false; go(e.dataTransfer.files[0]) }}>
    <h2>{t('d_upload_t')}</h2><p>{drag ? t('d_drop') : t('d_upload_p')}</p>
    <button class="btn secondary" onclick={() => input.click()} disabled={busy}>{t('d_choose')}</button>
    <input bind:this={input} type="file" hidden accept=".csv,.tsv,.txt,.xlsx,.xls,.json,.parquet" onchange={(e) => go(e.currentTarget.files[0])} />
  </div>
</div>
</Page>
<style>
  h1{font-size:26px;margin:0 0 var(--s2)}.lead{color:var(--grey-600);max-width:60ch;margin:0 0 var(--s6)}
  .two{display:grid;grid-template-columns:1fr 1fr;gap:var(--s4)}
  .card{text-align:left;font:inherit;color:var(--ink);display:flex;flex-direction:column;gap:var(--s3);align-items:flex-start;min-height:200px}
  .pick{cursor:pointer;transition:border-color var(--t-fast)}.pick:hover{border-color:var(--ink)}
  .card h2{font-size:18px;margin:0}.card p{margin:0;color:var(--grey-600);flex:1}
  .drop{border-style:dashed}.drop.drag{border-color:var(--ink);background:var(--grey-50)}
  .btn.secondary{display:inline-flex;align-items:center}.pick .btn{display:inline-flex;align-items:center}
  .err{color:var(--alert-red);font-weight:500}
  @media (max-width:700px){.two{grid-template-columns:1fr}}
.nosample{border-style:dashed;background:var(--grey-50)}
</style>
