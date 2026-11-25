<script>
  import { onMount } from 'svelte'
  import { i18n, L } from './lib/i18n.svelte.js'
  import { api } from './lib/api.js'
  import { st, loadSession, say, sayOnce, resetAll, saveUi } from './lib/store.svelte.js'
  import { router } from './lib/router.svelte.js'
  import Rabbit from './lib/Rabbit.svelte'
  import { STEPS as ORDER } from './lib/steps.js'
  import { rpShort } from './lib/fmt.js'
  import About from './lib/About.svelte'
  import Palette from './lib/Palette.svelte'
  import DataSource from './pages/DataSource.svelte'
  import Mapping from './pages/Mapping.svelte'
  import Findings from './pages/Findings.svelte'
  import Health from './pages/Health.svelte'
  import Dashboard from './pages/Dashboard.svelte'
  import Actions from './pages/Actions.svelte'
  import Share from './pages/Share.svelte'
  const t = i18n.t
  const STEPS = [['data', 'B1'], ['mapping', 'B2'], ['clean', 'B3'], ['health', 'B4'], ['dashboard', 'B5'], ['actions', 'B6'], ['share', 'B7']]
  // [label key, left shown, right shown]. A page without a detail column offers only: centre alone, or journey + centre.
  const LAYOUTS = $derived(st.solo ? [['1', false, false], ['2s', true, false]] : [['1', false, false], ['2', false, true], ['3', true, true]])
  const isOn = (left, right) => st.ui.leftOff === !left && (st.solo || st.ui.rightOff === !right)
  const setLayout = (left, right) => { st.ui.leftOff = !left; if (!st.solo) st.ui.rightOff = !right; saveUi() }
  const mql = matchMedia('(max-width:900px)')
  let ldrag = $state(false), askReset = $state(false), mobile = $state(mql.matches), menu = $state(false), ready = $state(false)
  mql.addEventListener('change', (e) => { mobile = e.matches; menu = false })
  const sub = $derived(router.path.split('/')[2] || '')
  const allowed = (id) => id === 'data' || (id === 'mapping' ? !!st.info : !!st.session?.confirmed)
  onMount(async () => { await loadSession().catch(() => (st.session = { loaded: false, confirmed: false })); ready = true; localStorage.setItem('setupDone', '1') })
  $effect(() => {
    if (!ready) return
    if (!sub) return router.go(st.session.confirmed ? '/studio/dashboard' : '/studio/data', true)
    if (!STEPS.some(([s]) => s === sub)) return router.go('/studio/data', true)
    if (!allowed(sub)) return router.go('/studio/data', true)
    if (!st.reached.includes(sub)) { st.reached.push(sub); localStorage.setItem('reached', JSON.stringify(st.reached)) }
    const n = st.fs?.findings.length ?? 0
    if (sub === 'data') sayOnce('data', L('Halo! Pilih data yang mau kita olah: pakai data contoh Dua Kelinci untuk mulai cepat, atau unggah file kamu sendiri.', 'Hi! Pick the data to work with: use the Dua Kelinci sample to start fast, or upload your own file.'))
    if (sub === 'mapping' && st.info) {
      const low = Object.entries(st.info.mapping).filter(([, v]) => v.confidence < 0.9).length, rows = st.info.rows.toLocaleString('id-ID')
      sayOnce('mapping:' + st.info.name, L(`Aku sudah baca ${rows} baris dari ${st.info.name}. ${st.info.remembered ? t('m_remembered') : low ? `Ada ${low} kolom yang aku kurang yakin; cek bagian yang bertanda ▲.` : 'Aku yakin dengan semua prediksi kolom ini, tapi cek dulu ya.'} Di kanan ada pratinjau isi filenya.`,
        `I read ${rows} rows from ${st.info.name}. ${st.info.remembered ? t('m_remembered') : low ? `I am unsure about ${low} columns; check the ones marked ▲.` : 'I am confident about every column guess, but please check.'} The file preview is on the right.`))
    }
    if (sub === 'clean' && st.fs && !st.analysing) sayOnce('clean', n ? L(`Aku menemukan ${n} hal yang perlu dirapikan, satu per layar. Pilih opsi di tengah; baris aslinya jadi bukti di kanan. Tidak ada yang kuubah diam-diam, atau terapkan semua rekomendasi sekaligus.`, `I found ${n} things to tidy, one per screen. Choose an option in the middle; the original rows are the evidence on the right. I change nothing silently, or apply every recommendation at once.`) : L('Data kamu sudah bersih. Tidak ada temuan.', 'Your data is already clean. No findings.'))
    if (sub === 'health' && st.fs) sayOnce('health', st.fs.pending.length ? L(`Masih ada ${st.fs.pending.length} temuan yang belum diputuskan, jadi angkanya masih mentah.`, `${st.fs.pending.length} findings are still undecided, so the numbers are still raw.`) : L(`Selesai. Total net bersih ${st.fs.summary.after.net.toLocaleString('id-ID')} dari ${st.fs.summary.after.rows} baris. Layar ini menunjukkan apa yang berubah di datamu (sebelum dan sesudah) dan dampaknya ke angka. Cek dulu, termasuk baris aslinya di panel kanan, baru lanjut ke Dashboard.`, `Done. Clean net total ${st.fs.summary.after.net.toLocaleString('id-ID')} from ${st.fs.summary.after.rows} rows. This screen shows what changed in your data (before and after) and its effect on the numbers. Check it first, including the original rows in the right panel, then continue to the Dashboard.`))
    if (sub === 'dashboard') sayOnce('dashboard', L('Mulai dari ceritanya di tengah. Klik Brand untuk melihat brand yang naik atau turun, Outlet untuk 5 outlet terlemah dibanding sesama tipenya, Salesman untuk kontribusi tiap orang. Filter dan rincian ada di kanan. Kalau sudah paham, lanjut ke Action items.', 'Start with the story in the middle. Click Brand to see which brands rise or fall, Outlet for the 5 weakest outlets against their own type, Salesman for each person\'s contribution. Filters and details are on the right. When you are done, move on to Action items.'),
      { guide: true, chips: [{ label: 'Brand', run: () => (st.tab = 'brand') }, { label: 'Outlet', run: () => (st.tab = 'outlet') }, { label: 'Salesman', run: () => (st.tab = 'sales') }, { label: L('Action items →', 'Action items →'), run: () => router.go('/studio/actions') }] })
    if (sub === 'actions') sayOnce('actions', L('Ini aksi yang kubuat dari temuan. Klik satu kartu untuk fokus; yang lain meredup. Ubah teks, pemilik, tenggat, dan status. Di kanan kamu lihat siapa menerima apa. Setelah itu lanjut memilih penerima.', 'These are the actions I drafted from the findings. Click a card to focus it; the others dim. Edit the text, owner, due date and status. The right column shows who receives what. Then move on to choosing recipients.'))
    if (sub === 'share') sayOnce('share', L('Pilih penerima. Mode "setiap aksi ke pemiliknya" mengirim tiap orang hanya aksi miliknya. "Lihat pesan" ada di samping nama tiap penanggung jawab (buka "Lihat siapa saja") dan di baris tiap penerima; hasilnya tampil di panel kanan.', 'Choose recipients. "Each action to its owner" sends every person only their own actions. "See message" sits next to each owner name (open "See who") and on each recipient row; the preview shows in the right panel.'))
  })
  const pending = $derived(st.fs?.pending.length ?? 0)
  // status of every step: what is done, what needs attention, what is locked
  let sent = $state(null)
  $effect(() => { sub; if (ready && st.session?.confirmed) { api('/actions').then((r) => (st.act = { total: r.items.length, done: r.items.filter((i) => i.status === 'done').length, urgent: r.items.filter((i) => i.priority === 'urgent' && i.status !== 'done').length })).catch(() => {}); api('/share/history').then((r) => (sent = r.items.filter((h) => h.status === 'sent').length)).catch(() => {}) } })
  const stat = (id) => {
    const ok = (txt) => ({ tone: 'ok', ic: '✓', txt }), bad = (txt) => ({ tone: 'bad', ic: '!', txt }), todo = (txt) => ({ tone: 'todo', ic: '○', txt }), wait = (txt) => ({ tone: 'wait', ic: '⏳', txt })
    if (id === 'mapping' && st.session?.confirmed) return ok(t('ss_confirmed'))
    if (!allowed(id)) return { tone: 'lock', ic: '🔒', txt: t('ss_locked') }
    const c = st.session?.confirmed
    if (id !== 'data' && id !== sub && !st.reached.includes(id)) return todo(t('ss_unopened'))   // never colour a step the user has not opened yet
    if (id === 'data') return st.session?.loaded ? ok(t('ss_loaded')) : todo(t('ss_choose'))
    if (id === 'mapping') return c ? ok(t('ss_confirmed')) : wait(t('ss_confirm_needed'))
    if (id === 'clean') return !st.fs ? todo('') : pending ? wait(`${pending} ${t('ss_undecided')}`) : ok(t('ss_all_decided'))
    if (id === 'health') return pending ? wait(t('ss_raw')) : ok(t('ss_clean'))
    if (id === 'dashboard') return c ? ok(t('ss_active')) : todo('')
    if (id === 'actions') return !st.act ? todo('') : st.act.total && st.act.done === st.act.total ? ok(`${st.act.done}/${st.act.total} ${t('ss_done')}`) : st.act.urgent ? bad(`${st.act.urgent} ${t('ss_urgent')} · ${st.act.done}/${st.act.total} ${t('ss_done')}`) : todo(`${st.act.done}/${st.act.total} ${t('ss_done')}`)
    if (id === 'share') return sent ? ok(`${sent} ${t('ss_sent')}`) : todo(t('ss_not_sent'))
    return todo('')
  }
</script>
{#snippet stepper(vertical)}
  <nav class="steps" class:v={vertical} aria-label="Langkah">
    {#each STEPS as [id, code]}
      {@const x = stat(id)}
      <button class="step {x.tone}" title={t('s_' + id) + (x.txt ? ' — ' + x.txt : '')} class:on={sub === id} disabled={!allowed(id)} onclick={() => router.go('/studio/' + id)} aria-current={sub === id ? 'step' : undefined}>
        <span class="si" aria-hidden="true">{x.ic}</span>
        <span class="sl"><b>{t('s_' + id)}</b>{#if x.txt}<small>{x.txt}</small>{/if}</span>
      </button>
    {/each}
  </nav>
{/snippet}
<div class="shell">
  <header class="top">
    <strong>Sales Studio</strong>
    <span class="crumb">{t('part2')} <span aria-hidden="true">›</span> {t('s_' + (sub || 'data'))}</span>
    <button class="lk more" onclick={() => (menu = !menu)} aria-expanded={menu} aria-label={t('j_menu')}>⋯</button>
    <nav class="links" class:show={menu} onclick={() => (menu = false)}>
      <div class="lay" role="group" aria-label={t('lay_title')}>
        {#each LAYOUTS as [n, left, right]}
          <button class:on={isOn(left, right)} onclick={() => setLayout(left, right)} aria-pressed={isOn(left, right)} aria-label={t('lay_' + n)} title={t('lay_' + n)}>
            <svg width="26" height="18" viewBox="0 0 26 18" aria-hidden="true"><rect x=".75" y=".75" width="24.5" height="16.5" rx="3" fill="none" stroke="currentColor" stroke-width="1.5" />
              <rect x="3" y="3" width="4.5" height="12" rx="1" fill="currentColor" opacity={left ? 1 : 0.18} /><rect x="9.5" y="3" width="7" height="12" rx="1" fill="currentColor" /><rect x="18.5" y="3" width="4.5" height="12" rx="1" fill="currentColor" opacity={right ? 1 : 0.18} /></svg>
          </button>
        {/each}
      </div>
      <button class="lk wave" onclick={() => (st.about = true)} aria-label={L('Tentang aplikasi ini', 'About this app')} title={L('Tentang aplikasi ini', 'About this app')}>👋</button>
      <button class="lk dsk" onclick={() => (st.palette = true)}>{t('palette')} <kbd>⌘K</kbd></button>
      <button class="lk" onclick={() => router.go('/status')}>{t('status')}</button>
      <button class="lk" onclick={() => (askReset = true)} aria-label={t('rs_btn')}><span aria-hidden="true">↺</span> {t('rs_btn')}</button>
      <button class="lk" onclick={() => i18n.toggle()}>{t('lang')}</button>
    </nav>
  </header>
  <Rabbit />
  <div class="body" class:lo={st.ui.leftOff} class:ldrag style={!st.ui.leftOff && st.ui.lw ? `--lw:${st.ui.lw}px` : ''}>
    {#if !mobile}
      <aside class="side" aria-label={t('j_title')}>
        {#if !st.ui.leftOff}<div class="lgrip" role="separator" aria-orientation="vertical" aria-label={t('col_resize')} title={t('col_resize')} tabindex="0" onpointerdown={(e) => { ldrag = true; e.currentTarget.setPointerCapture(e.pointerId) }} onpointermove={(e) => { if (ldrag) st.ui.lw = Math.round(Math.min(Math.max(e.clientX, 200), 460)) }} onpointerup={() => { if (ldrag) { ldrag = false; saveUi() } }} onkeydown={(e) => { const c = st.ui.lw ?? 280; if (e.key === 'ArrowLeft') st.ui.lw = Math.max(200, c - 24); else if (e.key === 'ArrowRight') st.ui.lw = Math.min(460, c + 24); else if (e.key === 'Enter') st.ui.lw = null; else return; e.preventDefault(); saveUi() }} ondblclick={() => { st.ui.lw = null; saveUi() }}></div>{/if}
        <div class="lt"><p class="lh">{t('j_title')}</p><button class="tg" onclick={() => { st.ui.leftOff = !st.ui.leftOff; saveUi() }} aria-label={st.ui.leftOff ? t('col_expand') : t('col_collapse')} title={st.ui.leftOff ? t('col_expand') : t('col_collapse')}>{st.ui.leftOff ? '›' : '‹'}</button></div>
        {@render stepper(true)}
      </aside>
    {/if}
    <main class="canvas">
      {#if mobile}{@render stepper(false)}{/if}
      <div class="pg">{#if ready}
        {#if sub === 'data'}<DataSource />{:else if sub === 'mapping'}<Mapping />{:else if sub === 'clean'}<Findings />{:else if sub === 'health'}<Health />{:else if sub === 'dashboard'}<Dashboard />{:else if sub === 'actions'}<Actions />{:else if sub === 'share'}<Share />{/if}
      {/if}</div>
    </main>
  </div>
</div>
{#if askReset}
  <div class="scrim" role="presentation" onclick={() => (askReset = false)}>
    <div class="dlg card" role="alertdialog" aria-modal="true" aria-label={t('rs_btn')} onclick={(e) => e.stopPropagation()}>
      <p><b>{t('rs_q')}</b></p>
      <div class="acts"><button class="btn secondary" onclick={() => (askReset = false)}>{t('rs_no')}</button><button class="btn danger" onclick={resetAll}>{t('rs_yes')}</button></div>
    </div>
  </div>
{/if}
<Palette /><About />
<style>
  .shell{display:flex;flex-direction:column;height:100dvh}
  .top{display:flex;align-items:center;gap:var(--s4);padding:0 var(--s4) 0 var(--s6);min-height:64px;border-bottom:var(--border);flex:none;position:relative}.links{display:flex;align-items:center;gap:var(--s4)}
  .crumb{flex:1;color:var(--grey-600);font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .lk{white-space:nowrap;background:none;border:0;cursor:pointer;color:var(--grey-600);font:inherit;font-size:14px;min-height:44px;display:flex;align-items:center;gap:6px}.lk:hover:not(:disabled){color:var(--ink)}.lk:disabled{opacity:.4}
  .lk.more{display:none;font-size:22px;min-width:44px;justify-content:center}
  .lk.strong{color:var(--ink);font-weight:600}
  kbd{font:12px var(--mono);border:var(--border);border-radius:4px;padding:1px 5px}
  .dot{background:var(--alert-red);color:#fff;border-radius:99px;font-size:11px;min-width:18px;height:18px;display:grid;place-items:center;padding:0 5px}
  .body{flex:1;display:grid;grid-template-columns:var(--lw,280px) 1fr;min-height:0;transition:grid-template-columns var(--t-base)}.body.lo{grid-template-columns:60px 1fr}
  .lt{display:flex;align-items:center;justify-content:space-between;padding-right:var(--s2)}.tg{background:none;border:0;cursor:pointer;font-size:20px;color:var(--grey-600);min-width:40px;min-height:40px;border-radius:6px}.tg:hover{background:var(--grey-100);color:var(--ink)}
  .lo .steps.v .step:not(:last-child)::after{left:50%;margin-left:-1px}
  .lo .lh,.lo .sl,.lo .ctx{display:none}.lo .lt{justify-content:center;padding:var(--s2) 0 0}.lo .step{justify-content:center;padding:6px 0;border-left:0}.lo .steps.v{padding:var(--s1) var(--s1)}
  .side{padding-bottom:96px;position:relative;min-height:0;height:100%;display:flex;flex-direction:column;border-right:var(--border);background:var(--grey-50);overflow:auto}
  .lh{margin:0;padding:var(--s4) var(--s4) var(--s1);font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600)}
  .ctx{margin-top:auto;border-top:var(--border);padding-bottom:var(--s3)}.ctx .lh{padding-top:var(--s3)}.cl{margin:0;padding:var(--s1) var(--s4);display:flex;flex-direction:column;font-size:13px;line-height:1.35}.cl small{color:var(--grey-600)}.cl b{overflow-wrap:anywhere}.mut{padding:0 var(--s4);color:var(--grey-600)}
  .canvas{display:flex;flex-direction:column;overflow:hidden;min-width:0;min-height:0}.pg{flex:1;min-height:0}
  .steps{display:flex;gap:var(--s1);overflow-x:auto;border-bottom:var(--border);flex:none;padding:0 var(--s4)}
  .steps.v{flex-direction:column;overflow:visible;gap:0;padding:var(--s1) var(--s2) var(--s3)}
  .step{display:flex;align-items:center;gap:10px;background:none;border:0;border-left:3px solid transparent;border-radius:6px;padding:6px 10px;cursor:pointer;font:inherit;font-size:13px;color:var(--grey-600);white-space:nowrap;min-height:44px;text-align:left}
  .steps.v .step{position:relative;height:54px;min-height:54px}.steps.v .step:not(:last-child)::after{content:"";position:absolute;left:20px;width:2px;top:calc(50% + 11px);height:calc(100% - 22px);background:var(--grey-400);z-index:0}.steps.v .step.ok:not(:last-child)::after{background:var(--ok-green)}.steps.v .si{position:relative;z-index:1;background:var(--paper)}
  .step.on{background:var(--grey-100);color:var(--ink);border-left-color:var(--ink)}.step:disabled{opacity:.45;cursor:not-allowed}
  .si{flex:none;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:12px;font-weight:700;border:1.5px solid var(--grey-400);color:var(--grey-600)}
  .step.ok .si{background:var(--ok-green);border-color:var(--ok-green);color:#fff}.step.bad .si{background:var(--alert-red);border-color:var(--alert-red);color:#fff}.step.lock .si{border-style:dashed;font-size:10px}
  .sl{display:flex;flex-direction:column;line-height:1.25;min-width:0}.sl b{font-weight:600;font-size:14px;color:var(--ink)}.sl small{font-size:12px;color:var(--grey-600);overflow:hidden;text-overflow:ellipsis}
  .step.wait .si{background:var(--paper);border-color:var(--grey-400);font-size:13px;line-height:1}.step.wait small{color:var(--ink);font-weight:600}
  .step.ok small{color:var(--ok-green)}.step.bad small{color:var(--alert-red);font-weight:600}
  .steps:not(.v) .sl small{display:none}.steps:not(.v) .step{border-left:0;border-bottom:2px solid transparent;border-radius:0}.steps:not(.v) .step.on{background:none;border-bottom-color:var(--ink)}
  .scrim{position:fixed;inset:0;background:rgba(0,0,0,.4);display:grid;place-items:center;z-index:60;padding:var(--s4)}
  .dlg{max-width:420px}.dlg p{margin:0 0 var(--s4)}.acts{display:flex;gap:var(--s3);justify-content:flex-end}.btn.danger{background:var(--alert-red);border-color:var(--alert-red)}
  .lgrip{position:absolute;right:-4px;top:0;bottom:0;width:9px;cursor:col-resize;z-index:6}.lgrip::after{content:"";position:absolute;left:4px;top:0;bottom:0;width:2px;background:transparent}.lgrip:hover::after,.lgrip:focus-visible::after,.ldrag .lgrip::after{background:var(--ink)}.body.ldrag{transition:none;user-select:none}
  @media (max-width:900px){.body{grid-template-columns:1fr}.top{padding:0 var(--s3) 0 76px;gap:var(--s2)}.crumb{display:none}.top strong{flex:1}.lk.more{display:flex}
    .links{display:none;position:absolute;top:100%;right:var(--s3);z-index:80;flex-direction:column;align-items:stretch;gap:0;background:var(--paper);border:var(--border);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.14);padding:var(--s1)}.links.show{display:flex}.links .lk{padding:0 var(--s4);justify-content:flex-start}.links .dsk{display:none}}
  .lk.wave{font-size:20px;padding:0 var(--s2)}
  .lay{display:flex;border:1px solid var(--grey-200);border-radius:8px;overflow:hidden}.lay button{background:var(--paper);border:0;border-right:1px solid var(--grey-200);padding:0 10px;min-height:36px;cursor:pointer;color:var(--grey-600);display:grid;place-items:center}.lay button:last-child{border-right:0}.lay button:hover{background:var(--grey-100);color:var(--ink)}.lay button.on{background:var(--ink);color:#fff}.lay button:focus-visible{outline:2px solid var(--ink);outline-offset:-2px}
  @media (max-width:900px){.lay{display:none}}
</style>
