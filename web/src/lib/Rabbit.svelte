<script>
  // The narrator: the red Jackrabbit, bottom-right. It speaks about what is happening right now and keeps no chat
  // history. The bubble fades when idle (so it hides less content) and becomes solid again on hover / focus.
  import { i18n } from './i18n.svelte.js'
  import { st, ask, undo } from './store.svelte.js'
  import { router } from './router.svelte.js'
  import { L } from './i18n.svelte.js'
  import { untrack } from 'svelte'
  import Typed from './Typed.svelte'
  import { glossHtml } from './glossary.js'
  import { rp, pctSigned } from './fmt.js'
  let { canAsk = true, corner = false } = $props()
  const strip = matchMedia('(max-width:900px)').matches
  // icon-only mode: phones, and desktop when the left column is collapsed. The bubble opens on tap; new lines show typing dots, then 💬
  const iconMode = $derived(strip || (!corner && st.ui.leftOff))
  const t = i18n.t
  let askOpen = $state(false), open = $state(false), unread = $state(false), idle = $state(false), text = $state(''), box, tm, fade, hover = false, seen = st.messages.at(-1)?.id ?? 0   // a remount must not replay the last line
  const m = $derived([...st.messages].reverse().find((x) => x.who === 'assistant'))
  const step = $derived(router.path.split('/')[2] || '')
  // context CTAs: what is useful to ask on this screen (the message's own chips come first)
  const ctx = $derived(!canAsk ? [] : ['dashboard', 'actions', 'share'].includes(step)
    ? [{ label: L('5 outlet terlemah', '5 weakest outlets'), text: '5 outlet terlemah' }, { label: L('Top 10 outlet', 'Top 10 outlets'), text: 'top 10 outlet' }, { label: L('Jabar', 'West Java'), text: 'jabar' }] : [])
  // earlier lines stay stacked above the newest one and fade out the older they are (desktop only)
  $effect(() => { router.path; untrack(() => { st.stackFrom = st.messages.at(-1)?.id ?? 0 }) })   // new page: clear the stack
  const keep = $derived(router.path.startsWith('/studio/dashboard'))   // the Dashboard needs more reading time: nothing fades there
  // one-time hint (per reset): the rabbit itself is the button that shows / hides the chat
  let hint = $state(false)
  $effect(() => {
    if (localStorage.getItem('rbHint')) return
    const a = setTimeout(() => { hint = true; localStorage.setItem('rbHint', '1') }, 2500), b = setTimeout(() => (hint = false), 12500)
    return () => { clearTimeout(a); clearTimeout(b) }
  })
  let now = $state(Date.now())
  $effect(() => { const iv = setInterval(() => (now = Date.now()), 1000); return () => clearInterval(iv) })
  const older = $derived(iconMode ? [] : st.messages.filter((x) => x.who === 'assistant' && x.id !== m?.id && x.id > st.stackFrom && (keep || now - (x.t ?? now) < 11000)).slice(-3).reverse())
  const chips = $derived([...(m?.chips ?? []), ...ctx.filter((c) => !(m?.chips ?? []).some((x) => x.label === c.label))])
  const wake = () => { idle = false; clearTimeout(fade); fade = setTimeout(() => { if (!hover && !document.querySelector('.rb :focus')) idle = true }, 3500) }
  const arm = () => { clearTimeout(tm); tm = setTimeout(() => { if (!hover && document.activeElement !== box) open = false }, 30000) }
  let typing = $state(false), root
  $effect(() => { const id = m?.id ?? 0; if (id && id !== seen) { seen = id
    if (iconMode) { unread = true; typing = true; open = false; setTimeout(() => (typing = false), 2200) }   // phone: icon only, dots say "something new"
    else { open = true; unread = false; wake(); arm() } } })
  $effect(() => { if (iconMode) untrack(() => { open = false }) })
  $effect(() => { if (!open || !iconMode) return; const f = (e) => { if (root && !root.contains(e.target)) open = false }; document.addEventListener('pointerdown', f); return () => document.removeEventListener('pointerdown', f) })
  const toggle = () => { hint = false; open = !open; unread = false; typing = false; if (open) { wake(); arm();  } }
  const enter = () => { hover = true; idle = false; clearTimeout(fade) }
  const leave = () => { hover = false; wake(); arm() }
  const pick = (c) => (c.run ? c.run() : ask(c.text))
  function submit(e) { e.preventDefault(); const v = text; text = ''; askOpen = false; ask(v) }
</script>
<div class="rb" class:corner={corner || st.solo} class:flat={st.solo && !corner} class:rail={!corner && st.ui.leftOff} bind:this={root}>
  <div class="fw"><button class="face" class:talk={open} onclick={toggle} aria-expanded={open} aria-label={t('rb_name')} title={t('rb_name')}>
    <img src="/jackrabbit.png" alt="" width="64" height="40" />
    {#if typing && !open}<span class="typ" aria-hidden="true"><i></i><i></i><i></i></span>{:else if unread && !open}<span class="dot" aria-hidden="true">💬</span>{/if}
  </button>{#if hint}<span class="hint" role="note">{L('Klik aku untuk menampilkan atau menyembunyikan chat', 'Click me to show or hide the chat')}</span>{/if}</div>
  {#if open}
    <div class="bub" class:idle={idle && !keep} role="status" aria-live="polite" onpointerenter={enter} onpointerleave={leave} onfocusin={enter} onfocusout={leave}>
      <button class="x" onclick={() => (open = false)} aria-label={t('rs_no')}>✕</button>
      <p class="who">{t('rb_name')}</p>
      {#if st.thinking}<p class="say">…</p>
      {:else if m}
        <p class="say"><Typed text={m.text} speed={9} /></p>
        {#if m.insights}{#each m.insights as i}<blockquote class="quote">{@html glossHtml(i)}</blockquote>{/each}{/if}
        {#if m.intent === 'weakest' || m.intent === 'top'}
          <ol class="res">{#each m.result as r}<li><b>{r.name}</b> <span class="mut">{r.branch} · {r.type}</span>
            {#if m.intent === 'weakest'}<span class="neg">{@html glossHtml('skor')} {r.score.toFixed(0)}</span><blockquote class="quote bad">{@html glossHtml(r.reasons[0].text)}</blockquote>{:else}<span class="num">{rp(r.total)}</span>{/if}</li>{/each}</ol>
        {:else if m.intent === 'why'}{#each m.result.reasons as r}<blockquote class="quote bad">{@html glossHtml(r.text)}</blockquote>{/each}
        {:else if m.intent === 'compare'}
          <ul class="res">{#each m.result.rows.slice(0, 6) as r}<li><b>{r.key}</b> <span class={r.delta >= 0 ? 'pos' : 'neg'}>{r.delta >= 0 ? '▲' : '▼'} {pctSigned(r.pct)}</span> <small>{rp(r.delta)}</small></li>{/each}</ul>
        {/if}
      {/if}
      {#if chips.length || canAsk}<div class="chips">{#each chips as c}<button class="chip" onclick={() => pick(c)}>{c.label}</button>{/each}
        {#if canAsk && st.history.length}<button class="chip" onclick={undo}>↶ {t('undo')}</button>{/if}
        {#if canAsk && !askOpen}<button class="chip ghost" onclick={() => { askOpen = true; queueMicrotask(() => box?.focus()) }}>✎ {t('ask_short')}</button>{/if}</div>{/if}
      {#if canAsk && askOpen}<form onsubmit={submit} class="box">
        <input bind:this={box} bind:value={text} placeholder={t('ask')} aria-label={t('ask')} autocomplete="off" />
        <button class="btn" disabled={!text.trim()}>{t('send')}</button>
      </form>{/if}
    </div>
    {#each older as o, i (o.id)}<div class="bub old" style="opacity:{keep ? 1 : now - (o.t ?? now) >= 9000 ? 0 : [0.6, 0.36, 0.2][i]}" aria-hidden="true"><p class="say">{o.text}</p></div>{/each}
  {/if}
</div>
<style>
    .rb{position:fixed;left:var(--s4);bottom:var(--s4);z-index:70;display:flex;flex-direction:column-reverse;align-items:flex-start;gap:var(--s2);pointer-events:none}
  .rb.rail,.rb.rail.corner{left:8px}.rb.rail .face{width:44px;padding:2px}
  .bub.old{padding:var(--s3) var(--s4);box-shadow:none;animation:none;transition:opacity 1.5s ease}.bub.old .say{margin:0;padding:0;font-size:13.5px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.bub.old:hover{opacity:1!important}
  .rb:not(.corner) .bub{width:min(264px,calc(100vw - 2 * var(--s4)))}
  .rb>*{pointer-events:auto}
  .face{width:72px;border:0;background:none;padding:4px 6px;cursor:pointer;border-radius:12px;position:relative;filter:drop-shadow(0 2px 6px rgba(212,24,61,.25))}
  .face img{display:block;width:100%;height:auto}
  .face:hover img,.face.talk img{animation:hop .9s ease-in-out}
  .face:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
  @keyframes hop{0%,100%{transform:translateY(0)}30%{transform:translateY(-5px) rotate(-4deg)}60%{transform:translateY(0) rotate(3deg)}}
  .dot{position:absolute;top:-10px;left:50%;transform:translateX(-50%);font-size:18px;line-height:1;animation:bobe 1.4s ease-in-out infinite}@keyframes bobe{0%,100%{transform:translate(-50%,0)}50%{transform:translate(-50%,-3px)}}
  .bub{position:relative;width:min(380px,calc(100vw - 2 * var(--s4)));max-height:min(62dvh,560px);overflow:auto;background:var(--paper);border:1.5px solid var(--alert-red);border-radius:14px;padding:var(--s4);box-shadow:0 8px 28px rgba(0,0,0,.16);animation:pop .22s ease-out;opacity:1;transition:opacity .15s ease}
  .bub.idle{opacity:.22;transition:opacity 3.5s ease}
  .bub:hover,.bub:focus-within{opacity:1;transition:opacity .15s ease}
  @keyframes pop{from{opacity:0;transform:translateY(6px) scale(.97)}to{opacity:1;transform:none}}
  @media (prefers-reduced-motion:reduce){.bub,.face:hover img,.face.talk img{animation:none}.bub.idle{transition:none}}
  .x{position:absolute;top:6px;right:8px;background:none;border:0;cursor:pointer;color:var(--grey-600);min-width:36px;min-height:36px}
  .who{margin:0 0 var(--s1);font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--alert-red)}
  .say{margin:0 0 var(--s2);font-size:15px;line-height:1.55;padding-right:var(--s6)}
  .bub :global(.quote){font-size:13.5px;margin:var(--s2) 0 0;padding-left:var(--s3)}
  .res{margin:var(--s2) 0 0;padding-left:18px;font-size:13px}.res li{margin-bottom:var(--s2)}small,.mut{color:var(--grey-600)}
  .chips{display:flex;flex-wrap:wrap;gap:var(--s2);margin-top:var(--s3)}
  .chip{border:1.5px solid var(--alert-red);color:var(--alert-red);background:var(--paper);border-radius:99px;padding:6px 14px;font:500 13px var(--font);cursor:pointer;min-height:36px}.chip:hover{background:var(--alert-red-bg)}
  .box{display:flex;gap:var(--s2);margin-top:var(--s3);flex-wrap:wrap}
  input{flex:1;min-width:120px;min-height:44px;border:1px solid var(--grey-200);border-radius:var(--radius);padding:0 var(--s3);font:inherit}input:focus{border-color:var(--ink);outline:none}
  .chip.ghost{border-color:var(--grey-200);color:var(--grey-800)}
  .box .btn{padding:0 var(--s4)}.btn:disabled{opacity:.35;cursor:not-allowed}
  .typ{position:absolute;top:-6px;right:-4px;display:flex;gap:3px;background:var(--ink);padding:5px 7px;border-radius:99px}.typ i{width:5px;height:5px;border-radius:50%;background:#fff;animation:blink 1s infinite}.typ i:nth-child(2){animation-delay:.15s}.typ i:nth-child(3){animation-delay:.3s}
  @keyframes blink{0%,60%,100%{opacity:.3;transform:none}30%{opacity:1;transform:translateY(-2px)}}
  /* phone: a notification-style icon in the top right; the bubble opens on tap and closes on a tap elsewhere */
  .rb.corner{bottom:92px}
  .rb.corner.flat{bottom:16px}
  @media (max-width:900px){
    .rb,.rb.corner,.rb.rail,.rb.corner.flat{top:18px;bottom:auto;left:var(--s3);right:auto;transform:none;flex-direction:column;align-items:flex-start}
    .face{width:52px}
    .rb:not(.corner) .bub,.bub,.bub.idle{position:fixed;top:64px;left:var(--s3);right:var(--s3);width:auto;max-height:60dvh;opacity:1}
  }
.fw{position:relative;display:flex;align-items:center}
  .hint{position:absolute;left:calc(100% + 8px);top:50%;transform:translateY(-50%);width:max-content;max-width:210px;background:var(--ink);color:#fff;font:500 13px/1.4 var(--font);padding:8px 12px;border-radius:8px;animation:pop .25s ease-out;pointer-events:none}.hint::before{content:"";position:absolute;left:-5px;top:50%;margin-top:-5px;border:5px solid transparent;border-left:0;border-right-color:var(--ink)}
</style>
