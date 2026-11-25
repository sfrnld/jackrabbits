<script>
  import { onMount } from 'svelte'
  import { i18n } from '../lib/i18n.svelte.js'
  import { st, guard, say } from '../lib/store.svelte.js'
  import { L } from '../lib/i18n.svelte.js'
  import { api } from '../lib/api.js'
  import TokenSetup from '../lib/TokenSetup.svelte'
  import Pairing from '../lib/Pairing.svelte'
  import Page from '../lib/Page.svelte'
  import { router } from '../lib/router.svelte.js'
  const t = i18n.t
  let acts = $state([]), tg = $state(null), recs = $state([]), roles = $state([]), sel = $state({}), mode = $state('per_owner')
  let adding = $state(false), draft = $state({ name: '', role: 'Salesman', region: '', owner: '' }), invite = $state(null)
  let prevFor = $state(''), prev = $state(null), prevErr = $state(''), confirming = $state(false), dm = $state(false), sending = $state(false)
  let res = $state(null), hist = $state([]), copied = $state('')
  const rcv = $derived(recs.find((x) => x.id === prevFor))
  const key = (x) => (x ?? '').trim().toLowerCase()
  const open = (r) => acts.filter((i) => i.status !== 'done' && (mode === 'per_owner' ? key(i.owner) === key(r.owner || r.name) : mode === 'per_region' && r.region ? i.region === r.region : true))
  const sendable = $derived(chosen.filter((r) => mode !== 'per_owner' || open(r).length))
  const orphans = $derived([...new Set(acts.filter((i) => i.status !== 'done' && i.owner && i.owner !== 'Belum ditentukan' && !recs.some((r) => key(r.owner || r.name) === key(i.owner))).map((i) => i.owner))])
  const owners = $derived([...new Set([...(st.options?.salesman ?? []), ...acts.map((i) => i.owner)])].filter((o) => o && o !== 'Tidak diketahui' && o !== 'Belum ditentukan'))
  let oprev = $state(null), prevOwner = $state('')
  const unassigned = $derived(acts.filter((i) => i.status !== 'done' && (!i.owner || i.owner === 'Belum ditentukan')).length)
  const regions = $derived(st.options?.region ?? [])
  const chosen = $derived(recs.filter((r) => sel[r.id]))
  const canDemo = $derived(!!(tg?.configured && tg.online && recs.length && orphans.length && !sending))
  const canSend = $derived(tg?.configured && tg.online && sendable.length > 0 && !sending)
  const fsum = $derived(Object.entries(st.filters).map(([k, v]) => `${k}: ${v.join(', ')}`).join(' · ') || t('sh_all_regions'))

  async function load() {
    const r = await api('/recipients'); recs = r.items; roles = r.roles
    for (const x of recs) if (!(x.id in sel)) sel[x.id] = true
    if (!prevFor || !recs.some((x) => x.id === prevFor)) prevFor = recs[0]?.id ?? ''
    hist = (await api('/share/history')).items
    acts = (await api('/actions').catch(() => ({ items: [] }))).items
  }
  onMount(load)
  const regionFor = (r) => (mode === 'per_region' ? r?.region || null : null)
  async function loadPreview() {
    prevErr = ''
    const r = recs.find((x) => x.id === prevFor)
    if (mode === 'per_owner') { const o = prevOwner || orphans[0]; oprev = r ? await guard(() => api('/share/preview-owner', { recipient_id: r.id })) : o ? await guard(() => api('/share/preview-owner', { owner: o })) : null; prev = null; return }
    oprev = null
    const p = await guard(() => api('/share/preview', { filters: $state.snapshot(st.filters), region: regionFor(r) }))
    if (p) prev = p; else prevErr = st.notice
  }
  $effect(() => { prevFor; prevOwner; orphans.length; mode; acts.length; JSON.stringify(st.filters); if (st.options && st.session?.confirmed) loadPreview() })
  async function startInvite() { invite = { ...draft }; }
  async function paired() { await load(); setTimeout(() => { invite = null; adding = false; draft = { name: '', role: 'Salesman', region: '', owner: '' } }, 1600) }
  async function remove(id) { await api('/recipients/' + id, undefined, 'DELETE'); delete sel[id]; await load() }
  async function send() {
    sending = true; confirming = false; res = null
    try { res = await api('/share/send', { recipient_ids: dm ? [recs[0].id] : sendable.map((r) => r.id), mode: dm ? 'demo_me' : mode, filters: $state.snapshot(st.filters), confirm: true }) }
    catch (e) { res = { error: e.detail?.message ?? e.detail ?? 'Gagal mengirim', results: [], fallbacks: {} } }
    finally { sending = false; dm = false; await load(); const ok = res?.results?.filter((x) => x.status === 'sent').length ?? 0, bad = res?.results?.filter((x) => x.status === 'failed').length ?? 0; say(res?.error ? L(`Pengiriman gagal: ${res.error}`, `Sending failed: ${res.error}`) : bad ? L(`${ok} terkirim, ${bad} gagal. Untuk yang gagal, salin pesan atau unduh gambarnya dan kirim manual.`, `${ok} sent, ${bad} failed. For the failed ones, copy the message or download the image and send it manually.`) : (res?.results?.[0]?.scope ?? '').startsWith('demo:') ? L(`Demo terkirim: ${ok} pesan pemilik masuk ke chat Telegram-mu. Cek HP-mu.`, `Demo sent: ${ok} owner messages arrived in your Telegram chat. Check your phone.`) : L(`Terkirim ke ${ok} penerima. Riwayat ada di panel Detail.`, `Sent to ${ok} recipients. The history is in the Detail panel.`)) }
  }
  async function copyText(p, key) { await navigator.clipboard?.writeText([p.summary, p.actions_text].filter(Boolean).join('\n\n')); copied = key; setTimeout(() => (copied = ''), 1500) }
  const fname = (p) => `laporan-${(p?.scope_label ?? 'semua').toLowerCase().replace(/\s+/g, '-')}.png`
</script>
<Page wide title={t('sh_title')} lead={t('sh_lead')} asideTitle={t('sh_preview')} asideSub={rcv ? `${t('sh_for')} ${rcv.name}` : ''}>

<section class="card sec" aria-label="Telegram"><TokenSetup bind:status={tg} /></section>

<section class="card sec" aria-label={t('sh_recipients')}>
  <header><h2>{t('sh_recipients')}</h2><button class="btn secondary" onclick={() => (adding = !adding)} disabled={!tg?.configured || !tg.online}>+ {t('sh_add')}</button></header>
  {#if adding}
    <div class="add">
      {#if !invite}
        <label>{t('sh_name')}<input bind:value={draft.name} /></label>
        <label>{t('sh_role')}<select bind:value={draft.role}>{#each roles.filter((r) => r !== 'Admin') as r}<option>{r}</option>{/each}</select></label>
        <label>{t('sh_owner')}<select bind:value={draft.owner}><option value="">{t('sh_owner_same')}</option>{#each owners as o}<option>{o}</option>{/each}</select></label>
        <label>{t('sh_region')}<select bind:value={draft.region}><option value="">{t('sh_all_regions')}</option>{#each regions as r}<option>{r}</option>{/each}</select></label>
        <button class="btn" onclick={startInvite} disabled={!draft.name.trim()}>{t('sh_invite')}</button>
      {:else}<Pairing draft={invite} onpaired={paired} />{/if}
    </div>
  {/if}
  {#if recs.length}
    <ul class="recs">{#each recs as r (r.id)}
      <li class:cur={prevFor === r.id}><label><input type="checkbox" bind:checked={sel[r.id]} /> <b>{r.name}</b>{#if r.owner && r.owner !== r.name}<small class="mut"> → {r.owner}</small>{/if}</label><span class="mut">{r.role}</span><button class="lk2" onclick={() => (prevFor = r.id)}>{t('sh_see')}</button><span class="cnt" class:zero={!open(r).length}>{open(r).length} {open(r).length === 1 ? t('a_item1') : t('a_items')}</span><span class="chip">{r.region || t('sh_all_regions')}</span>
        <button class="x" onclick={() => remove(r.id)} aria-label="Hapus {r.name}">✕</button></li>{/each}</ul>
  {:else}<p class="mut">{t('sh_none')}</p>{/if}
  {#if orphans.length}<div class="warn" role="note"><p><b>{orphans.length} {t('sh_orphans_n')}</b> <span class="mut">{t('sh_orphans_why')}</span></p>
    <details><summary>{t('sh_who')}</summary>{#each orphans as o}<span class="ow"><button class="lk2" onclick={() => { adding = true; draft.name = o; draft.owner = ''; invite = null }}>{o}</button> <button class="lk2 see" onclick={() => { prevFor = ''; prevOwner = o }}>{t('sh_see')}</button></span> {/each}</details>
    <div class="wa">{#if canDemo}<button class="btn secondary" onclick={() => { dm = true; confirming = true }}>{t('sh_demo_btn')}</button>{:else if !recs.length}<button class="btn secondary" onclick={() => { adding = true; draft.name = L('Saya', 'Me'); draft.owner = ''; invite = null }} disabled={!tg?.configured || !tg.online}>{t('sh_invite_me')}</button>{/if}</div></div>{/if}
  {#if unassigned}<p class="warn">⚠️ {unassigned} {t('sh_unassigned')} <button class="lk2" onclick={() => router.go('/studio/actions')}>{t('sh_edit_actions')}</button></p>{/if}
</section>

<section class="card sec" aria-label={t('sh_mode')}>
  <h2>{t('sh_mode')}</h2>
  <label class="opt"><input type="radio" bind:group={mode} value="per_owner" /> {t('sh_per_owner')}</label>
  <label class="opt"><input type="radio" bind:group={mode} value="per_region" /> {t('sh_per_region')}</label>
  <label class="opt"><input type="radio" bind:group={mode} value="same" /> {t('sh_same')} <span class="mut">({fsum})</span></label>
</section>


<section class="sec" aria-live="polite">
  {#if res}
    <div class="card out">
      {#if res.error}<p class="err" role="alert">▲ {res.error}</p>{/if}
      <ul>{#each res.results as x}
        <li><span class="chip {x.status === 'sent' ? 'ok' : x.status === 'skipped' ? '' : 'bad'}">{x.status === 'sent' ? '✓ ' + t('sh_sent') : x.status === 'skipped' ? '– ' + t('sh_skipped') : '▲ ' + t('sh_failed')}</span> <b>{x.name}</b> <span class="mut">{x.scope}</span>
          {#if x.status === 'failed' && res.fallbacks[x.fallback]}
            <p class="err">{x.error}</p><p class="mut">{t('sh_fallback')}</p>
            {@const fb = res.fallbacks[x.fallback]}
            <div class="row"><button class="btn secondary" onclick={() => copyText(fb, x.recipient_id)}>{copied === x.recipient_id ? '✓ ' + t('db_copied') : t('sh_copy')}</button>{#if fb.card}<a class="btn secondary" href={fb.card} download={fname(fb)}>{t('sh_dl')}</a>{/if}</div>
          {/if}</li>{/each}</ul>
    </div>
  {/if}
</section>



{#snippet aside()}
<section class="sec" aria-label={t('sh_preview')}>
  <header>
    {#if recs.length}<label class="inl">{t('sh_for')} <select bind:value={prevFor}>{#each recs as r}<option value={r.id}>{r.name}{mode === 'per_region' && r.region ? ' · ' + r.region : ''}</option>{/each}</select></label>{/if}</header>
  {#if prevErr}<p class="err">▲ {prevErr}</p>{/if}
  {#if oprev}
    <div class="pv">{#if oprev.card}<figure class="oc"><img src={oprev.card} alt={L('Gambar data yang ikut terkirim', 'The data picture that is sent with the message')} /><figcaption class="mut">{L('Gambar ini dikirim lebih dulu', 'This picture is sent first')}</figcaption></figure>{/if}<blockquote class="quote"><p style="white-space:pre-wrap">{oprev.text || t('sh_no_actions')}</p><cite>{oprev.scope_label}</cite></blockquote>
      {#if oprev.actions.length}<ol class="al">{#each oprev.actions as a}<li><span class="stat {a.priority === 'urgent' ? 'bad' : a.priority === 'opportunity' ? 'ok' : ''}">{a.priority === 'urgent' ? '▲ ' + t('a_urgent') : a.priority === 'opportunity' ? '✓ ' + t('a_opp') : '• ' + t('a_watch')}</span> <b>{a.outlet}</b><br />{a.action}<br /><small>{a.due}</small></li>{/each}</ol>
      <div class="row"><button class="btn secondary" onclick={() => copyText({ summary: '', actions_text: oprev.text }, 'o')}>{copied === 'o' ? '✓ ' + t('db_copied') : t('sh_copy')}</button><button class="lk2" onclick={() => router.go('/studio/actions')}>{t('sh_edit_actions')}</button></div>{/if}</div>
  {:else if prev}
    <div class="pv">
      <figure><img src={prev.card} alt="Kartu laporan {prev.scope_label}" /><figcaption>{t('sh_msg1')}</figcaption></figure>
      <div class="txt">
        <blockquote class="quote"><p>{prev.summary}</p><cite>{t('sh_msg2')}</cite></blockquote>
        <h3>{t('sh_msg3')} <span class="mut">· {prev.actions.length}</span> <button class="lk2" onclick={() => router.go('/studio/actions')}>{t('sh_edit_actions')}</button></h3>
        {#if prev.actions.length}<ol class="al">{#each prev.actions as a}<li class="a-{a.priority}"><span class="stat {a.priority === 'urgent' ? 'bad' : a.priority === 'opportunity' ? 'ok' : ''}">{a.priority === 'urgent' ? '▲ ' + t('a_urgent') : a.priority === 'opportunity' ? '✓ ' + t('a_opp') : '• ' + t('a_watch')}</span> <b>{a.outlet}</b><br />{a.action}<br /><small>{a.owner} · {a.due}</small></li>{/each}</ol>{:else}<p class="mut">{t('sh_no_actions')}</p>{/if}
        <div class="row"><button class="btn secondary" onclick={() => copyText(prev, 'p')}>{copied === 'p' ? '✓ ' + t('db_copied') : t('sh_copy')}</button>
          <a class="btn secondary" href={prev.card} download={fname(prev)}>{t('sh_dl')}</a></div>
      </div>
    </div>
  {/if}
</section>
<section class="sec" aria-label={t('sh_history')}>
  <h2>{t('sh_history')}</h2>
  {#if hist.length}
    <div class="tw"><table><thead><tr><th>{t('sh_time')}</th><th>{t('sh_to')}</th><th>{t('sh_scope')}</th><th>{t('sh_status')}</th></tr></thead>
      <tbody>{#each hist.slice(0, 20) as h}<tr><td class="num">{h.t}</td><td>{h.name}</td><td>{h.scope}</td><td><span class="chip {h.status === 'sent' ? 'ok' : 'bad'}">{h.status === 'sent' ? '✓ ' + t('sh_sent') : '▲ ' + t('sh_failed')}</span></td></tr>{/each}</tbody></table></div>
  {:else}<p class="mut">{t('sh_nohist')}</p>{/if}
</section>
{/snippet}
{#snippet footer()}
  {#if !confirming}
    <button class="btn big" onclick={() => (confirming = true)} disabled={!canSend}>{sending ? '…' : `${t('sh_send')} (${sendable.length})`}</button>
    {#if !(tg?.configured && tg.online)}<span class="mut">{t('sh_need_tg')}</span>{/if}
  {:else}
    <span>{#if dm}<b>{t('sh_demo_to')} {recs[0]?.name}</b> <span class="mut">· {t('sh_demo_note')}</span>{:else}<b>{sendable.length} · {sendable.map((r) => r.name).join(', ')}</b> <span class="mut">· {mode === 'per_owner' ? t('sh_per_owner') : mode === 'per_region' ? t('sh_per_region') : t('sh_same')}. Pesan tidak bisa ditarik kembali.</span>{/if}</span><span class="sp"></span>
    <button class="btn secondary" onclick={() => { confirming = false; dm = false }}>{t('sh_cancel')}</button>
    <button class="btn" onclick={send}>{t('sh_send_now')}</button>
  {/if}
{/snippet}
</Page>
<style>
  h1{font-size:26px;margin:0 0 var(--s2)}.lead{color:var(--grey-600);max-width:64ch;margin:0 0 var(--s6)}
  .sec{margin-bottom:var(--s4)}header{display:flex;align-items:center;justify-content:space-between;gap:var(--s3);flex-wrap:wrap;margin-bottom:var(--s3)}h2{margin:0;font-size:17px}h3{font-size:13px;color:var(--grey-600);font-weight:500;margin:var(--s3) 0 var(--s2)}
  .btn{padding:0 var(--s6);display:inline-flex;align-items:center;text-decoration:none}.btn:disabled{opacity:.35;cursor:not-allowed}.big{min-height:52px;font-size:16px}
  .mut{color:var(--grey-600)}.err{color:var(--alert-red)}.row{display:flex;gap:var(--s3);flex-wrap:wrap;margin-top:var(--s3)}
  .add{display:flex;gap:var(--s3);flex-wrap:wrap;align-items:flex-end;padding:var(--s3);background:var(--grey-50);border-radius:8px;margin-bottom:var(--s3)}.add label{display:flex;flex-direction:column;gap:4px;font-size:12.5px;color:var(--grey-600)}
  input:not([type]),select{min-height:40px;border:1px solid var(--grey-200);border-radius:6px;padding:0 10px;font:inherit;background:var(--paper)}
  .recs{list-style:none;margin:0;padding:0}.recs li{display:flex;gap:var(--s4);align-items:center;padding:8px 0;border-top:var(--border);flex-wrap:wrap}.recs label{flex:1;min-width:140px;display:flex;gap:8px;align-items:center}
  .chip{font-size:12.5px;padding:2px 10px;border-radius:99px;background:var(--grey-100)}.chip.ok{background:var(--ok-green-bg);color:var(--ok-green)}.chip.bad{background:var(--alert-red-bg);color:var(--alert-red)}
  .x{background:none;border:0;cursor:pointer;color:var(--grey-600);min-width:44px;min-height:44px}.x:hover{color:var(--alert-red)}
  .opt{display:flex;gap:var(--s3);align-items:center;min-height:44px}.inl{display:flex;gap:8px;align-items:center;font-size:14px;color:var(--grey-600)}
  .pv{display:grid;grid-template-columns:1fr;gap:var(--s4)}figure{max-width:320px}figure{margin:0}img{width:100%;height:auto;border:var(--border);border-radius:8px}figcaption{font-size:13px;color:var(--grey-600);margin-top:6px}
  .bubble{background:var(--grey-50);border:var(--border);border-radius:12px;padding:12px 14px;font:inherit;font-size:14px;line-height:1.5;margin:0;white-space:pre-wrap}
  .confirm{border-color:var(--ink);margin-bottom:var(--s3)}.confirm p{margin:0 0 var(--s2)}.out{margin-top:var(--s3)}.out ul{list-style:none;margin:0;padding:0}.out li{padding:var(--s2) 0;border-top:var(--border)}.out li:first-child{border-top:0}
  .tw{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;color:var(--grey-600);font-weight:500;padding:6px 8px}td{padding:8px;border-top:var(--border)}
  @media (max-width:700px){.pv{grid-template-columns:1fr}}
  .cnt{font-size:12.5px;font-weight:600;padding:2px 10px;border-radius:99px;background:var(--grey-100)}.recs li.cur{background:var(--grey-50);box-shadow:inset 3px 0 0 var(--ink);padding-left:var(--s2)}
  .lk2{background:none;border:0;text-decoration:underline;cursor:pointer;color:var(--grey-600);font:inherit;font-size:13px;min-height:32px}
  .al{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:var(--s2)}.al li{background:var(--paper);border:var(--border);border-radius:8px;padding:var(--s2) var(--s3);font-size:13.5px;line-height:1.45}.al small{color:var(--grey-600)}
  .cnt.zero{background:none;color:var(--grey-600);border:1px dashed var(--grey-400)}.warn{margin:var(--s3) 0 0;font-size:13.5px;color:var(--alert-red);font-weight:500}
.ow{display:inline-flex;gap:var(--s2);margin-right:var(--s3)}
.oc{max-width:100%!important}.oc img{width:100%;height:auto;border:var(--border);border-radius:8px}.oc figcaption{font-size:12.5px;margin-top:4px}
</style>
