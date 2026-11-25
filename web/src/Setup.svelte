<script>
  import { i18n } from './lib/i18n.svelte.js'
  import Typed from './lib/Typed.svelte'
  import Orb from './lib/Orb.svelte'
  import { router } from './lib/router.svelte.js'
  import TokenSetup from './lib/TokenSetup.svelte'
  import Pairing from './lib/Pairing.svelte'
  import { api } from './lib/api.js'
  import Page from './lib/Page.svelte'
  import Rabbit from './lib/Rabbit.svelte'
  import About from './lib/About.svelte'
  import { st, say, sayOnce } from './lib/store.svelte.js'
  import { L } from './lib/i18n.svelte.js'
  import { tick, untrack } from 'svelte'
  const t = i18n.t
  let step = $state(1)         // A1 welcome, A2 installed, A3 system check, A4 Telegram, A5 ready
  $effect(() => { step; untrack(() => { st.stackFrom = st.messages.at(-1)?.id ?? 0 }) })   // a new step starts a fresh bubble stack
  let tg = $state(null), admin = $state(null), connecting = $state(false)
  // A3: the checks are fast, so reveal them one by one: the user sees each item being checked, then its result.
  // A2: simulated install (everything is already on this computer; we replay the sequence so a reset feels like a fresh start)
  let hasSample = $state(true)
  fetch('/api/data/sample').then((r) => r.json()).then((j) => (hasSample = j.available)).catch(() => {})
  const MIN_ITEM = 4000          // a check or install item never finishes faster than this (ms)
  const INST = ['uv', 'python', 'libs', 'data']
  let idone = $state(0), installing = $state(false)
  async function install() {
    installing = true; idone = 0
    for (let k = 0; k < INST.length; k++) { await sleep(reduce ? 80 : MIN_ITEM); idone = k + 1 }
    installing = false
  }
  $effect(() => { if (step === 2) install() })
  const IDS = ['engine', 'storage', 'writable', 'sample', 'port', 'internet']
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
  let items = $state({}), done = $state(0), running = $state(false), run = 0
  async function check() {
    const my = ++run; running = true; done = 0; items = {}
    let res
    try { [res] = await Promise.all([fetch('/api/setup/check').then((r) => r.json()), sleep(reduce ? 0 : 500)]) } catch { res = { items: [] } }
    if (my !== run) return
    items = Object.fromEntries(res.items.map((i) => [i.id, i]))
    for (let k = 0; k < IDS.length; k++) {
      await sleep(reduce ? 120 : MIN_ITEM)     // every item takes at least MIN_ITEM so it feels like real work
      if (my !== run) return
      done = k + 1
    }
    running = false
  }
  $effect(() => { if (step === 3) check(); else run++ })
  const smooth = reduce ? 'auto' : 'smooth'
  $effect(() => { if (step === 3 && running) { const id = IDS[done]; if (id) tick().then(() => document.getElementById('chk-' + id)?.scrollIntoView({ block: 'center', behavior: smooth })) } })
  $effect(() => { if (step === 3 && finished) tick().then(() => document.querySelector('.plabel')?.scrollIntoView({ block: 'start', behavior: smooth })) })
  $effect(() => { if (step === 4) api('/recipients').then((r) => (admin = r.items.find((x) => x.role === 'Admin') ?? null)).catch(() => {}) })
  const list = $derived(IDS.map((id, k) => ({ id, data: items[id], state: k < done ? 'done' : k === done && running ? 'active' : 'pending' })))
  const finished = $derived(!running && done === IDS.length)
  const passed = $derived(list.filter((x) => x.data?.status === 'ok').length)
  const allOk = $derived(finished && list.every((x) => x.data && x.data.status !== 'error'))
  // the Jackrabbit narrates every step and result
  const LINES = () => ({
    1: L('Halo! Aku Jackrabbit, asisten Sales Studio. Aku akan menemani setiap langkah dan memberi tahu apa yang terjadi. Tekan Mulai kalau sudah siap.', 'Hi! I am Jackrabbit, the Sales Studio assistant. I will walk with you through every step and tell you what is happening. Press Start when you are ready.'),
    2: L('Aku memasang komponen satu per satu. Ini simulasi: semuanya sudah ada di komputermu dan tidak ada yang dikirim keluar.', 'I am installing the components one by one. This is a simulation: everything is already on your computer and nothing leaves it.'),
    3: L('Sekarang aku memeriksa komputermu satu per satu: mesin data, penyimpanan, folder, data contoh, port, dan internet. Halaman akan bergulir mengikuti pemeriksaan.', 'Now I am checking your computer one item at a time: data engine, storage, folder, sample data, port and internet. The page scrolls along with the checks.'),
    4: L('Telegram dipakai untuk mengirim laporan ke tim. Ini opsional: kamu bisa melewatinya dan mencoba semuanya dulu dengan pratinjau.', 'Telegram is used to send reports to the team. It is optional: skip it and try everything with previews first.'),
    5: L('Semua siap! Masuk ke Studio, lalu pilih data yang mau diolah.', 'All set! Enter the Studio, then pick the data you want to work with.'),
  })
  $effect(() => { sayOnce('setup' + step, LINES()[step]) })
  $effect(() => { if (step === 2 && idone > 0 && idone <= INST.length) { const id = INST[idone - 1]; sayOnce('inst:' + id, L(`${t('inst_' + id)}: terpasang ✓`, `${t('inst_' + id)}: installed ✓`)) } })
  // the rabbit follows every check as it finishes
  $effect(() => {
    if (step !== 3 || done < 1) return
    const id = IDS[done - 1], x = items[id]; if (!x) return
    const fact = x.facts?.[0] ? `${t('f_' + x.facts[0].k)}: ${x.facts[0].v}` : ''
    sayOnce(`chk${run}:${id}`, x.status === 'ok' ? L(`${t(id)} — aman. ${fact}`, `${t(id)} — OK. ${fact}`) : L(`${t(id)} — perlu perhatian. ${t('adv_' + id)}`, `${t(id)} — needs attention. ${t('adv_' + id)}`))
  })
  $effect(() => {
    if (step !== 3 || !finished) return
    const bad = list.filter((x) => x.data?.status !== 'ok')
    sayOnce('chk' + run, !bad.length ? L(`Semua ${IDS.length} pemeriksaan lolos. Komputermu siap.`, `All ${IDS.length} checks passed. Your computer is ready.`) : L(`${passed} dari ${IDS.length} lolos. Perlu perhatian: ${bad.map((x) => t(x.id)).join(', ')}.${allOk ? ' Tidak menghalangi; kamu tetap bisa lanjut.' : ' Perbaiki yang merah dulu lalu coba lagi.'}`, `${passed} of ${IDS.length} passed. Needs attention: ${bad.map((x) => t(x.id)).join(', ')}.${allOk ? ' Not blocking; you can still continue.' : ' Fix the red ones first, then retry.'}`))
  })
  $effect(() => { if (step === 4 && tg?.configured && tg.online) sayOnce('tg:' + tg.bot?.username, L(`Bot @${tg.bot?.username} tersambung. Sekarang pasangkan akunmu: scan QR atau buka tautannya, lalu tekan Start di Telegram.`, `Bot @${tg.bot?.username} is connected. Now pair your account: scan the QR or open the link, then press Start in Telegram.`)) })
  $effect(() => { if (step === 4 && tg?.configured && !tg.online) sayOnce('tgoff', L('Aku belum bisa menjangkau Telegram. Cek internetmu, atau lewati dulu.', 'I cannot reach Telegram yet. Check your internet, or skip for now.')) })
  $effect(() => { if (admin) sayOnce('admin' + admin.id, L(`Terhubung dengan ${admin.first_name || admin.name}! Laporan nanti bisa masuk ke chat ini.`, `Connected with ${admin.first_name || admin.name}! Reports can land in this chat.`)) })
</script>

<div class="shell">
<header class="top"><strong>Sales Studio</strong><span class="crumb">{t('part1')}</span><button class="link" onclick={() => (st.about = true)} aria-label={L('Tentang aplikasi ini', 'About this app')} title={L('Tentang aplikasi ini', 'About this app')}>👋</button><button class="link" onclick={() => i18n.toggle()}><span class="lgl">{t('lang')}</span><span class="lgs">{L('EN', 'ID')}</span></button></header>
<About />
<Rabbit canAsk={false} corner />

<div class="body"><Page maxw={640} center>
<p class="step num">{t('step')} {step} {t('of')} 5</p>
<div class="who"><Orb state={step === 3 && running ? 'thinking' : step === 5 || (step === 4 && admin) || (step === 3 && allOk) ? 'done' : 'ready'} /></div>

{#if step === 1}
  <h1><Typed text={t('welcome_h')} /></h1>
  <p>{t('welcome_p')}</p>
  <p class="heads"><span aria-hidden="true">💻</span> {L('Aplikasi ini bisa dibuka di browser HP, tapi lebih nyaman dan lengkap lewat browser desktop.', 'This app works in a mobile browser, but it is more comfortable and complete in a desktop browser.')}</p>
  <div class="cards">
    <div class="card active"><b>{t('part1')}</b><span class="tag">{t('now')}</span><p>{t('part1_d')}</p></div>
    <div class="card"><b>{t('part2')}</b><span class="tag mute">{t('next')}</span><p>{t('part2_d')}</p></div>
  </div>
{:else if step === 2}
  <h1>{installing ? t('inst_title') : t('installed_h')}</h1><p>{installing ? t('inst_sim') : t('installed_p')}</p>
  <ul class="checks inst">{#each INST as id, k}<li class={k < idone ? 'done' : k === idone && installing ? 'active' : 'pending'}>
    {#if k < idone}<span class="ic ok pop" aria-hidden="true">✓</span>{:else if k === idone && installing}<span class="spin" aria-hidden="true"></span>{:else}<span class="ic idle" aria-hidden="true"></span>{/if}
    <div class="bd"><b>{t('inst_' + id)}</b>{#if id === 'data' && !hasSample}<small class="mut"> · {L('tidak ditemukan (opsional, kamu bisa unggah data sendiri)', 'not found (optional, you can upload your own data)')}</small>{/if}</div></li>{/each}</ul>
{:else if step === 3}
  <h1>{t('check_h')}</h1><p>{t('check_p')}</p>
  <div class="prog" role="progressbar" aria-valuemin="0" aria-valuemax={IDS.length} aria-valuenow={done} aria-label={t('check_h')}><span style="width:{(done / IDS.length) * 100}%"></span></div>
  <p class="plabel num" class:good={finished && passed === IDS.length} aria-live="polite">
    {#if finished}{passed === IDS.length ? '✓ ' + t('all_ok') : `${passed} ${t('chk_passed')} · ${IDS.length - passed} ${t('chk_attention')}`}{:else}{t('chk_checking')} {Math.min(done + 1, IDS.length)} {t('of')} {IDS.length}…{/if}
  </p>
  <ul class="checks">
    {#each list as x (x.id)}
      {@const st = x.data?.status ?? 'error'}
      <li class={x.state} id="chk-{x.id}">
        {#if x.state === 'done'}<span class="ic {st} pop" aria-hidden="true">{st === 'ok' ? '✓' : st === 'warn' ? '!' : '✕'}</span>
        {:else if x.state === 'active'}<span class="spin" aria-hidden="true"></span>
        {:else}<span class="ic idle" aria-hidden="true"></span>{/if}
        <div class="bd">
          <b>{t(x.id)}</b>{#if x.state === 'active'}<span class="runl">{t('chk_running')}</span>{/if}
          {#if x.state !== 'pending'}<p class="what">{t('chk_' + x.id)}</p>{/if}
          {#if x.state === 'done'}
            {#if x.data}
              <dl class="facts">
                {#each x.data.facts as f, j}
                  <div class="rise" style="animation-delay:{reduce ? 0 : j * 80}ms"><dt>{t('f_' + f.k)}</dt><dd class:path={f.k === 'path'}>{f.v}{#if f.min}&nbsp;<em>· {t('f_min')} {f.min}</em>{/if}{#if f.max}&nbsp;<em>· {t('f_max')} {f.max}</em>{/if}</dd></div>
                {/each}
              </dl>
              {#if st !== 'ok'}<p class="adv {st}">{st === 'error' ? '✕' : '!'} {t('adv_' + x.id)}</p>{/if}
            {:else}<p class="adv error">✕ {t('chk_noresp')}</p>{/if}
          {/if}
        </div>
      </li>
    {/each}
  </ul>
{:else if step === 4}
  <h1>{t('tg_title')}</h1><p>{t('tg_p')}</p>
  <TokenSetup bind:status={tg} />
  {#if admin}<p class="pos"><b>✓ {t('tg_found')}{admin.first_name || admin.name}</b></p>
  {:else if tg?.configured && tg.online}<div class="gap"><Pairing draft={{ name: '', role: 'Admin', region: '' }} onpaired={(r) => (admin = r)} /></div>{/if}
{:else}
  <h1>{t('ready_h')}</h1><p>{t('ready_p')}</p>
{/if}
{#snippet footer()}
  {#if step === 1}<span class="sp"></span><button class="btn" onclick={() => (step = 2)}>{t('start')}</button>
  {:else if step === 2}<span class="sp"></span><button class="btn" disabled={installing} onclick={() => (step = 3)}>{t('cont')}</button>
  {:else if step === 3}<button class="btn secondary" onclick={check} disabled={running}>{t('retry')}</button><span class="sp"></span><button class="btn" disabled={!allOk} onclick={() => (step = 4)}>{t('cont')}</button>
  {:else if step === 4}<button class="btn secondary" onclick={() => { say(L('Telegram dilewati. Pengiriman akan diganti pratinjau; kamu bisa menyambungkannya kapan saja dari langkah Bagikan.', 'Telegram skipped. Sending is replaced by previews; you can connect it any time from the Share step.')); step = 5 }}>{t('tg_skip')}</button><span class="sp"></span><button class="btn" disabled={!admin} onclick={() => (step = 5)}>{t('cont')}</button>
  {:else}<span class="sp"></span><button class="btn" onclick={() => { localStorage.setItem('setupDone', '1'); router.go('/studio') }}>{t('enter_studio')}</button>{/if}
{/snippet}
</Page></div></div>

<style>
  .top{display:flex;gap:var(--s4);align-items:center;padding:var(--s3) var(--s6);border-bottom:var(--border)}
  .crumb{color:var(--grey-600);flex:1}.link{background:none;border:0;cursor:pointer;color:var(--grey-600);min-height:44px;font:inherit}.link:hover{color:var(--ink)}
  .shell{display:flex;flex-direction:column;height:100dvh}.body{flex:1;min-height:0}.top{flex:none}
  .step{color:var(--grey-600);font-size:14px;margin:0}
  h1{font-size:28px;line-height:1.25;margin:var(--s4) 0 var(--s3);min-height:2.5em}
  p{color:var(--grey-800)}
  .lgs{display:none}.top .link{white-space:nowrap}.top strong{white-space:nowrap}
  @media (max-width:900px){.top{padding:var(--s3) var(--s3) var(--s3) 76px;gap:var(--s3)}.crumb{display:none}.top strong{flex:1}.lgl{display:none}.lgs{display:inline}}
  .cards{display:grid;grid-template-columns:1fr 1fr;gap:var(--s4);margin:var(--s8) 0}
  .card.active{border-color:var(--ink)}
  .card p{margin:var(--s2) 0 0;font-size:14px;color:var(--grey-600)}
  .tag{margin-left:var(--s2);font-size:12px;padding:2px 8px;border-radius:99px;background:var(--ink);color:var(--paper)}
  .tag.mute{background:var(--grey-100);color:var(--grey-600)}
  .prog{height:4px;background:var(--grey-100);border-radius:99px;overflow:hidden;margin:var(--s6) 0 var(--s2)}
  .prog span{display:block;height:100%;background:var(--ink);border-radius:99px;transition:width .5s ease}
  .plabel{margin:0 0 var(--s2);font-size:14px;color:var(--grey-600)}.plabel.good{color:var(--ok-green);font-weight:600}
  .checks{list-style:none;padding:0;margin:var(--s3) 0 var(--s6)}
  .checks li{transition:opacity .35s}.checks li.pending{opacity:.4}.checks li.pending .bd b{color:var(--grey-600)}
  .spin{width:22px;height:22px;border-radius:50%;border:2.5px solid var(--grey-200);border-top-color:var(--ink);flex:none;animation:spin .8s linear infinite}
  .ic.idle{border:2px solid var(--grey-200);background:none}
  .runl{margin-left:var(--s2);font-size:13px;color:var(--grey-600)}
  .pop{animation:pop .35s cubic-bezier(.34,1.56,.64,1)}.rise{animation:rise .35s ease both}
  @keyframes spin{to{transform:rotate(360deg)}}@keyframes pop{from{transform:scale(.3);opacity:0}to{transform:scale(1);opacity:1}}@keyframes rise{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
  @media (prefers-reduced-motion:reduce){.spin,.pop,.rise{animation:none}.prog span,.checks li{transition:none}}
  .checks li{display:flex;gap:var(--s3);align-items:flex-start;padding:var(--s3) 0;border-bottom:var(--border)}
  .bd{flex:1;min-width:0}.what{margin:2px 0 var(--s2);font-size:13.5px;color:var(--grey-600)}
  .facts{margin:0;display:grid;gap:2px}.facts div{display:grid;grid-template-columns:130px 1fr;gap:var(--s3);font-size:13px}.facts dt{color:var(--grey-600)}.facts dd{margin:0;color:var(--ink);overflow-wrap:anywhere}
  .facts dd.path{font-family:var(--mono);font-size:12px}.facts em{font-style:normal;color:var(--grey-600)}
  .adv{margin:var(--s2) 0 0;font-size:13.5px;font-weight:500}.adv.warn,.adv.error{color:var(--alert-red)}
  @media (max-width:520px){.facts div{grid-template-columns:1fr;gap:0}}
  .ic{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:13px;font-weight:700;flex:none}
  .ic.ok{background:var(--ok-green-bg);color:var(--ok-green)}
  .ic.warn,.ic.error{background:var(--alert-red-bg);color:var(--alert-red)}
  .gap{margin-top:var(--s6)}
  .btn:disabled{opacity:.35;cursor:not-allowed}
  @media (max-width:520px){.cards{grid-template-columns:1fr}}
.heads{display:flex;gap:var(--s2);align-items:flex-start;padding:var(--s3) var(--s4);background:var(--grey-100);border-radius:10px;font-size:14.5px;color:var(--grey-800)}
</style>
