<script>
  import { glossHtml } from '../lib/glossary.js'
  import { onMount } from 'svelte'
  import { i18n } from '../lib/i18n.svelte.js'
  import { st, guard, say } from '../lib/store.svelte.js'
  import { L } from '../lib/i18n.svelte.js'
  import { router } from '../lib/router.svelte.js'
  import { api } from '../lib/api.js'
  import Page from '../lib/Page.svelte'
  const t = i18n.t
  let sumOpen = $state(false), recs = $state([]), sel = $state(null), items = $state([]), saved = $state(false), loaded = $state(false), tm
  const PR = { urgent: ['a_urgent', 'bad', '▲'], opportunity: ['a_opp', 'ok', '✓'], watch: ['a_watch', 'mut', '•'] }
  onMount(async () => { const r = await guard(() => api('/actions')); if (r) items = r.items; loaded = true; recs = (await api('/recipients').catch(() => ({ items: [] }))).items })
  function save() { clearTimeout(tm); saved = false; tm = setTimeout(async () => { await guard(() => api('/actions', { items: $state.snapshot(items) }, 'PUT')); saved = true }, 500) }
  const add = () => { items.push({ id: 'm' + Date.now(), outlet_id: '', outlet: '', branch: '', region: '', owner: '', action: '', reason: '', due: new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10), priority: 'watch' }); save() }
  const del = (i) => { items.splice(i, 1); save() }
  async function regen() { const r = await guard(() => api('/actions/regenerate', {})); if (r) { items = r.items; saved = false } }
  const ST = [['todo', 'as_todo', '○'], ['doing', 'as_doing', '◐'], ['done', 'as_done', '✓']]
  const stOf = (it) => it.status ?? 'todo'
  const today = new Date().toISOString().slice(0, 10)
  const late = (it) => stOf(it) !== 'done' && it.due && it.due < today
  const cnt = $derived(Object.fromEntries(ST.map(([k]) => [k, items.filter((i) => stOf(i) === k).length])))
  const pctDone = $derived(items.length ? Math.round((cnt.done / items.length) * 100) : 0)
  const attention = $derived(items.filter((i) => stOf(i) !== 'done' && (i.priority === 'urgent' || late(i))))
  const cur = $derived(items.find((i) => i.id === sel) ?? items[0])
  $effect(() => { if (loaded) st.act = { total: items.length, done: cnt.done, urgent: items.filter((i) => i.priority === 'urgent' && stOf(i) !== 'done').length } })
  // who receives what: a recipient with a region gets that region's open items; one without a region gets all
  const key = (x) => (x ?? '').trim().toLowerCase()
  const toWho = (it) => recs.filter((r) => key(r.owner || r.name) === key(it.owner))
  const routes = $derived([...new Set(items.filter((i) => stOf(i) !== 'done').map((i) => i.owner || ''))].map((ow) => ({ ow, n: items.filter((i) => (i.owner || '') === ow && stOf(i) !== 'done').length, who: recs.filter((r) => key(r.owner || r.name) === key(ow)) })))
  const setStatus = (it, k) => { it.status = k; save(); say(`${it.outlet || t('a_action')}: ${t('as_' + k)}. ${k === 'done' ? L('Aksi selesai tidak ikut dikirim ke Telegram.', 'Finished actions are not sent to Telegram.') : toWho(it).length ? L(`Akan dikirim ke ${toWho(it).map((r) => r.name).join(', ')}.`, `Will be sent to ${toWho(it).map((r) => r.name).join(', ')}.`) : L('Pemilik aksi ini belum punya akun Telegram.', 'This action\'s owner has no Telegram account yet.')}`) }
  // invite one salesperson: make a personal Telegram link to share or copy, then wait until they press Start
  let conn = $state({}), copied = $state('')
  const msg = (ow, link) => L(`Halo ${ow}, tolong gabung Telegram Sales Studio supaya kamu menerima aksi dari tim: ${link}`, `Hi ${ow}, please join the Sales Studio Telegram so you receive your actions from the team: ${link}`)
  async function invite(ow) {
    conn[ow] = { state: 'making' }
    const inv = await guard(() => api('/telegram/invite', { name: ow, role: 'Salesman', region: '', owner: ow }))
    if (!inv) { conn[ow] = { state: 'err' }; return }
    conn[ow] = { state: 'wait', link: inv.link }
    say(L(`Tautan undangan untuk ${ow} siap. Salin atau bagikan; aku menunggu sampai ${ow} menekan Start di bot.`, `The invite link for ${ow} is ready. Copy or share it; I will wait until ${ow} presses Start in the bot.`))
    for (let i = 0; i < 450; i++) {                  // keep listening for up to ~15 minutes
      await new Promise((r) => setTimeout(r, 2000))
      if (conn[ow]?.link !== inv.link) return
      const r = await api('/telegram/invite/' + inv.code).catch(() => null)
      if (r?.status === 'paired') { recs = (await api('/recipients').catch(() => ({ items: recs }))).items; conn[ow] = { state: 'ok' }; say(L(`${ow} sudah tersambung ke Telegram.`, `${ow} is now connected to Telegram.`)); return }
      if (r?.status === 'expired') break
    }
    conn[ow] = { state: 'err' }
  }
  async function copyLink(ow) { await navigator.clipboard?.writeText(conn[ow].link); copied = ow; setTimeout(() => (copied = ''), 1600) }
  async function shareLink(ow) {
    const text = msg(ow, conn[ow].link)
    if (navigator.share) { try { await navigator.share({ title: 'Sales Studio', text, url: conn[ow].link }); return } catch { return } }
    window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank')        // no share sheet: WhatsApp as the common fallback
  }
  const orphanN = $derived(routes.filter((r) => !r.who.length && r.ow && r.ow !== 'Belum ditentukan').length)
  const owners = $derived([...new Set([...(st.options?.salesman ?? []), ...items.map((i) => i.owner)])].filter((o) => o && o !== 'Tidak diketahui'))
</script>
<Page wide title={t('a_title')} lead={t('a_lead')} asideTitle={t('as_overview')} asideSub={`${items.length} ${items.length === 1 ? t('a_item1') : t('a_items')}`}>

<datalist id="owners">{#each owners as o}<option value={o}></option>{/each}</datalist>
{#if sel}<p class="fo"><button class="lk3" onclick={() => (sel = null)}>✕ {t('a_show_all')}</button></p>{/if}
<ol class="list">
  {#each items as it, i (it.id)}
    <li class="card it {it.priority} st-{stOf(it)}" class:cur={sel === it.id} class:dim={sel && sel !== it.id} onclick={() => (sel = it.id)} onfocusin={() => (sel = it.id)}>
      {#if sel === it.id}
      <div class="top"><span class="stat {stOf(it) === 'done' ? 'ok' : stOf(it) === 'doing' ? 'doing' : late(it) ? 'bad' : ''}">{ST.find((x) => x[0] === stOf(it))[2]} {t(ST.find((x) => x[0] === stOf(it))[1])}</span>{#if late(it)}<span class="stat bad">▲ {t('as_late')}</span>{/if}<span class="pr {PR[it.priority][1]}">{PR[it.priority][2]} {t(PR[it.priority][0])}</span>
        {#if it.outlet}<b>{it.outlet}</b><span class="mut">{[it.branch, it.region].filter(Boolean).join(' · ')}</span>{/if}
        <span class="sp"></span><button class="del" onclick={() => del(i)} aria-label="{t('a_del')} {it.outlet}">✕</button></div>
      {#if it.reason}<div class="why"><span class="wl">{t('a_why')}</span><blockquote class="quote {it.priority === 'opportunity' ? 'ok' : it.priority === 'urgent' ? 'bad' : ''}"><p>{@html glossHtml(it.reason)}</p></blockquote></div>{/if}
      <label>{t('a_action')}<textarea rows="2" value={it.action} oninput={(e) => { it.action = e.currentTarget.value; save() }}></textarea></label>
      <p class="to {toWho(it).length ? 'ok' : 'quiet'}">{#if stOf(it) === 'done'}✓ {t('a_not_sent')}{:else if toWho(it).length}➤ {t('a_goes_to')} {toWho(it).map((r) => r.name).join(', ')}{:else}{it.owner && it.owner !== 'Belum ditentukan' ? '○ ' + t('a_not_linked') : '⚠️ ' + t('a_assign')}{/if}</p>
      <div class="seg" role="group" aria-label={t('as_status')}>{#each ST as [k, lab, ic]}<button class:on={stOf(it) === k} class="s-{k}" aria-pressed={stOf(it) === k} onclick={() => setStatus(it, k)}>{ic} {t(lab)}</button>{/each}</div>
      <div class="row">
        <label>{t('a_owner')}<input list="owners" value={it.owner} oninput={(e) => { it.owner = e.currentTarget.value; save() }} /></label>
        <label>{t('a_due')}<input type="date" value={it.due} oninput={(e) => { it.due = e.currentTarget.value; save() }} /></label>
        <label>Prioritas<select value={it.priority} onchange={(e) => { it.priority = e.currentTarget.value; save() }}>{#each Object.keys(PR) as p}<option value={p}>{t(PR[p][0])}</option>{/each}</select></label>
      </div>
      {:else}
      <div class="crow"><span class="pd {it.priority}" title={t(PR[it.priority]?.[0] ?? 'a_watch')}></span><b>{it.outlet || it.action.slice(0, 44) || t('a_action')}</b><span class="sp"></span>{#if it.owner}<span class="mut own">{it.owner}</span>{/if}<span class="ic st-{stOf(it)}" title={t(ST.find((x) => x[0] === stOf(it))[1])}>{ST.find((x) => x[0] === stOf(it))[2]}</span><span class="chv" aria-hidden="true">▾</span></div>
      {/if}
    </li>
  {:else}{#if loaded}<li class="mut">—</li>{/if}{/each}
</ol>

{#snippet aside()}
  <div class="ov">
    <section class="blk sumblk">
      <button class="bh" onclick={() => (sumOpen = !sumOpen)} aria-expanded={sumOpen}><span><small>{t('as_overview')}</small><b class="num">{pctDone}% {t('as_complete')} · {cnt.done}/{items.length}</b></span><span aria-hidden="true">{sumOpen ? '▴' : '▾'}</span></button>
          <div class="pb" role="progressbar" aria-valuenow={pctDone} aria-valuemin="0" aria-valuemax="100"><span style="width:{pctDone}%"></span></div>
      <p class="mini num">{cnt.todo} {t('as_todo')} · {cnt.doing} {t('as_doing')} · {cnt.done} {t('as_done')}{#if attention.length} · <b class="neg">{attention.length} {t('as_attention')}</b>{/if}</p>
      {#if !sumOpen && orphanN}<button class="cbtn wide" onclick={() => (sumOpen = true)}>{orphanN} {t('sh_orphans_n')} · {L('Undang', 'Invite')} ↗</button>{/if}
      {#if sumOpen}
          <div class="tiles">{#each ST as [k, lab, ic]}<div class="tile t-{k}"><b class="num">{cnt[k]}</b><span>{ic} {t(lab)}</span></div>{/each}</div>
    <h3>{t('a_routing')}</h3>
    {#if routes.some((r) => !r.who.length && r.ow && r.ow !== 'Belum ditentukan')}<div class="nb"><b>{routes.filter((r) => !r.who.length && r.ow && r.ow !== 'Belum ditentukan').length} {t('sh_orphans_n')}</b> <button class="lk" onclick={() => router.go('/studio/share')}>{t('a_add_recv')} →</button></div>{/if}
    {#each routes as r}<div class="rt"><b>{r.ow && r.ow !== 'Belum ditentukan' ? r.ow : t('a_no_owner')}</b> <span class="mut">· {r.n} {r.n === 1 ? t('a_item1') : t('a_items')}</span><br />{#if r.who.length}<span class="ok">➤ {r.who.map((x) => x.name).join(', ')}</span>{:else}{#if r.ow && r.ow !== 'Belum ditentukan'}<span class="mut">○ {t('a_not_linked')}</span>
        {#if conn[r.ow]?.state === 'wait'}
          <div class="inv"><input readonly value={conn[r.ow].link} onfocus={(e) => e.currentTarget.select()} aria-label={L('Tautan undangan', 'Invite link')} />
            <span class="ib"><button class="cbtn" onclick={() => copyLink(r.ow)}>{copied === r.ow ? '✓ ' + L('Tersalin', 'Copied') : L('Salin tautan', 'Copy link')}</button><button class="cbtn" onclick={() => shareLink(r.ow)}>{L('Bagikan', 'Share')} ↗</button></span>
            <small class="mut">{L('Menunggu', 'Waiting for')} {r.ow} {L('menekan Start di Telegram…', 'to press Start in Telegram…')}</small></div>
        {:else}<button class="cbtn" onclick={() => invite(r.ow)} disabled={conn[r.ow]?.state === 'making'}>{conn[r.ow]?.state === 'making' ? '…' : conn[r.ow]?.state === 'err' ? L('Coba lagi', 'Try again') : L('Undang', 'Invite')}</button>{/if}{:else}<span class="mut">{t('a_assign')}</span>{/if}{/if}</div>{/each}
    <h3>{t('as_attention')}</h3>
    {#if attention.length}<ul class="att">{#each attention as it}<li><button onclick={() => (sel = it.id)}><span class="stat bad">▲ {late(it) ? t('as_late') : t('a_urgent')}</span> <b>{it.outlet || it.action.slice(0, 30)}</b> <span class="mut">{it.owner} · {it.due}</span></button></li>{/each}</ul>
    {:else}<p class="ok">✓ {t('as_none')}</p>{/if}
      {/if}
    </section>
    {#if sel && cur}
    <section class="blk selblk" aria-label={L('Aksi terpilih', 'Selected action')}>
      <p class="sl"><small>{L('Aksi terpilih', 'Selected action')}</small><b>{cur.outlet || t('a_action')}</b></p>
      <p class="mut sm">{cur.owner || t('a_no_owner')} · {cur.due}</p>
      <h4>{t('as_why')}</h4>
    {#if cur}
      {#if cur.reason}<blockquote class="quote {cur.priority === 'urgent' ? 'bad' : cur.priority === 'opportunity' ? 'ok' : ''}"><p>{cur.reason}</p><cite>{cur.owner} · {cur.due}</cite></blockquote>{:else}<p class="mut">—</p>{/if}{/if}
      <p class="mut sm">{L('Klik kartu lain di kiri untuk berganti.', 'Click another card on the left to switch.')}</p>
    </section>
    {/if}
  </div>
{/snippet}
{#snippet footer()}
  <button class="btn secondary" onclick={add}>+ {t('a_add')}</button>
  <button class="btn secondary" onclick={regen}>{t('a_regen')}</button>
  <span class="ok" aria-live="polite">{saved ? '✓ ' + t('a_saved') : ''}</span><span class="sp"></span>
  <button class="btn" onclick={() => router.go('/studio/share')}>{t('a_next2')}</button>
{/snippet}
</Page>
<style>
  .ov h3{font-size:13px;color:var(--grey-600);font-weight:600;margin:var(--s6) 0 var(--s2)}.pb{height:10px;background:var(--grey-200);border-radius:99px;overflow:hidden}.pb span{display:block;height:100%;background:var(--ok-green);transition:width var(--t-base)}.pt{margin:var(--s2) 0 var(--s4)}
  .tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--s2)}.tile{border:1.5px solid var(--grey-200);border-radius:8px;padding:var(--s3);background:var(--paper);display:flex;flex-direction:column}.tile b{font-size:26px}.tile span{font-size:12.5px;color:var(--grey-600)}.t-doing{border-color:var(--ink)}.t-done{border-color:var(--ok-green)}.t-done b{color:var(--ok-green)}
  .att{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px}.att button{background:var(--paper);border:1px solid var(--grey-200);border-radius:8px;padding:8px 10px;width:100%;text-align:left;font:inherit;font-size:13.5px;cursor:pointer;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.att button:hover{border-color:var(--ink)}
  .seg{display:flex;gap:0;margin-top:var(--s3);border:1.5px solid var(--grey-200);border-radius:8px;overflow:hidden}.seg button{flex:1;min-height:44px;background:var(--paper);border:0;border-right:1px solid var(--grey-200);font:500 14px var(--font);cursor:pointer;color:var(--grey-600)}.seg button:last-child{border-right:0}.seg button.on.s-todo{background:var(--grey-100);color:var(--ink)}.seg button.on.s-doing{background:var(--ink);color:var(--paper)}.seg button.on.s-done{background:var(--ok-green);color:#fff}
  .it{cursor:pointer;transition:opacity var(--t-base),box-shadow var(--t-base)}.it.cur{box-shadow:0 0 0 2px var(--ink)}.it.st-done{opacity:.72}.it.dim{opacity:.32}.it.dim:hover{opacity:.7}
  .fo{margin:0 0 var(--s3)}.lk3{background:none;border:1px solid var(--grey-200);border-radius:99px;padding:0 14px;min-height:36px;font:inherit;font-size:13px;cursor:pointer}.lk3:hover{border-color:var(--ink)}
  h1{font-size:26px;margin:0 0 var(--s2)}.lead{color:var(--grey-600);max-width:64ch;margin:0 0 var(--s4)}
  .bar{display:flex;align-items:center;gap:var(--s3);margin-bottom:var(--s4);flex-wrap:wrap}.sp{flex:1}.btn{padding:0 var(--s4)}.ok{color:var(--ok-green);font-size:13px}.mut{color:var(--grey-600)}
  .list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:var(--s3)}.it{padding:var(--s4)}.it.urgent{border-left:3px solid var(--alert-red)}.it.opportunity{border-left:3px solid var(--ok-green)}
  .top{display:flex;gap:var(--s3);align-items:center;flex-wrap:wrap;margin-bottom:var(--s2)}.pr{font-size:12.5px;font-weight:500;padding:2px 10px;border-radius:99px}.pr.bad{background:var(--alert-red-bg);color:var(--alert-red)}.pr.ok{background:var(--ok-green-bg);color:var(--ok-green)}.pr.mut{background:var(--grey-100)}
  .del{background:none;border:0;cursor:pointer;color:var(--grey-600);min-width:44px;min-height:44px}.del:hover{color:var(--alert-red)}
  label{display:flex;flex-direction:column;gap:4px;font-size:12.5px;color:var(--grey-600);flex:1;min-width:140px}textarea,input,select{font:inherit;font-size:14px;color:var(--ink);border:1px solid var(--grey-200);border-radius:6px;padding:8px 10px;min-height:40px;background:var(--paper)}textarea{resize:vertical}textarea:focus,input:focus,select:focus{border-color:var(--ink);outline:none}
  .why{font-size:13px;color:var(--grey-600);margin:var(--s2) 0}.row{display:flex;gap:var(--s3);flex-wrap:wrap;margin-top:var(--s2)}
  .to{margin:var(--s2) 0 0;font-size:13px;font-weight:500}.to.ok{color:var(--ok-green)}.to.bad{color:var(--alert-red)}
  .rt{margin:0 0 var(--s3);font-size:14px;line-height:1.5}.rt .lk{background:none;border:0;text-decoration:underline;cursor:pointer;color:var(--ink);font:inherit;font-size:13px}
.to.quiet{color:var(--grey-600)}.nb{background:var(--grey-100);border-left:3px solid var(--alert-red);border-radius:6px;padding:var(--s2) var(--s3);margin-bottom:var(--s3);font-size:13.5px}
.why{margin:var(--s3) 0}.wl{display:block;font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600);margin-bottom:var(--s1)}.why .quote{margin:0;font-size:15px}.why .quote p{margin:0}
.why.clamp .quote p{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.sumline{display:flex;align-items:center;gap:var(--s3);flex-wrap:wrap;margin:var(--s2) 0 0;font-size:13.5px}.sumline .sp{flex:1}.sumline .open{color:var(--grey-600);font-size:13px}.it:not(.cur){cursor:pointer}.it:not(.cur):hover{border-color:var(--ink)}
.cbtn{margin-left:var(--s2);background:var(--paper);border:1.5px solid var(--ink);border-radius:8px;padding:0 12px;min-height:36px;font:500 13px var(--font);cursor:pointer}.cbtn:disabled{opacity:.55;cursor:progress}.cbtn:hover:not(:disabled){background:var(--ink);color:#fff}
.blk{border-radius:12px;padding:var(--s4);margin-bottom:var(--s4)}.sumblk{background:var(--paper);border:1px solid var(--grey-200)}.selblk{background:var(--paper);border:2px solid var(--ink)}.bh{width:100%;display:flex;justify-content:space-between;align-items:center;gap:var(--s3);background:none;border:0;padding:0 0 var(--s3);font:inherit;color:var(--ink);cursor:pointer;text-align:left}.bh small,.sl small{display:block;font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600)}.bh b{font-size:17px}.mini{margin:var(--s2) 0 0;font-size:13.5px;color:var(--grey-800)}.sl{margin:0}.sl b{font-size:17px}.sm{font-size:13px;margin:2px 0 var(--s2)}.selblk h4{margin:var(--s3) 0 var(--s1);font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600)}.sumblk .pt{display:none}
.cbtn.wide{display:block;margin:var(--s3) 0 0;width:100%;text-align:left;padding:var(--s2) var(--s3)}
.crow{display:flex;align-items:center;gap:var(--s3);min-height:28px}.crow b{font-size:15.5px}.crow .own{font-size:13px}.crow .sp{flex:1}.pd{width:10px;height:10px;border-radius:50%;background:var(--grey-400);flex:none}.pd.urgent{background:var(--alert-red)}.pd.opportunity{background:var(--ok-green)}.ic{font-size:14px;color:var(--grey-600)}.ic.st-done{color:var(--ok-green)}.chv{color:var(--grey-600)}.it:has(.crow){padding:var(--s3) var(--s4)}.it:has(.crow){border-left-width:3px}
.inv{display:flex;flex-direction:column;gap:var(--s2);margin-top:var(--s2)}.inv input{width:100%;min-height:36px;border:1px solid var(--grey-200);border-radius:8px;padding:0 var(--s3);font:13px var(--font);color:var(--grey-800);background:var(--paper)}.ib{display:flex;gap:var(--s2);flex-wrap:wrap}.ib .cbtn{margin:0}
.rt{margin:var(--s3) 0}
</style>
