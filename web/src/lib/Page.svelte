<script>
  // Screen layout. Centre column = the core content (scrolls inside). Right column (`aside`) = details AND actions:
  // the detail scrolls, the action bar (`footer`) is pinned under it. The right column can be collapsed or dragged wider.
  // Narrow screens: the detail drops below, collapsible, and the action bar spans the bottom.
  import { onMount } from 'svelte'
  import { i18n } from './i18n.svelte.js'
  import { router } from './router.svelte.js'
  import { st, saveUi } from './store.svelte.js'
  import { STEPS } from './steps.js'
  let { children, footer = undefined, aside = undefined, asideTitle = '', asideSub = '', title = '', lead = '', tools = undefined, wide = false, maxw = undefined, center = false, pulse = false } = $props()
  const stepNo = $derived(STEPS.indexOf(router.path.split('/')[2] || '') + 1)
  const t = i18n.t, reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
  let sc = $state(), more = $state(false), raf = 0, openDet = $state(false), pageEl = $state(), dragging = $state(false)
  let narrow = $state(false)
  const off = $derived(!!aside && st.ui.rightOff)
  // tell the page whether the detail column can be seen right now (so a "open the panel" button can appear), and obey open requests
  $effect(() => { st.detShown = !aside || (!off && (!narrow || openDet)); return () => { st.detShown = true } })
  $effect(() => { if (st.detReq) { openDet = true; if (st.ui.rightOff) { st.ui.rightOff = false; saveUi() } } })
  const awStyle = $derived(off ? '--aw:48px' : st.ui.aw ? `--aw:${st.ui.aw}px` : '')
  const measure = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { if (sc) more = sc.scrollHeight - sc.scrollTop - sc.clientHeight > 28 }) }
  onMount(() => {
    measure(); const ro = new ResizeObserver(() => { measure(); narrow = pageEl.clientWidth <= 880 }); ro.observe(sc); ro.observe(pageEl); narrow = pageEl.clientWidth <= 880; if (sc.firstElementChild) ro.observe(sc.firstElementChild)
    const mo = new MutationObserver(measure); mo.observe(sc, { childList: true, subtree: true, characterData: true })
    return () => { ro.disconnect(); mo.disconnect(); cancelAnimationFrame(raf) }
  })
  $effect(() => { st.solo = !aside; return () => { st.solo = false } })   // the Jackrabbit moves to the empty bottom-left when there is no detail column
  export function top() { sc?.scrollTo({ top: 0 }) }
  const down = () => sc.scrollBy({ top: Math.max(180, sc.clientHeight * 0.75), behavior: reduce ? 'auto' : 'smooth' })
  const toggleRight = () => { st.ui.rightOff = !st.ui.rightOff; saveUi() }
  // drag the edge between centre and right column
  const clampW = (w) => Math.round(Math.min(Math.max(w, 280), Math.min(900, pageEl.clientWidth - 360)))
  function dragStart(e) { dragging = true; e.currentTarget.setPointerCapture(e.pointerId) }
  function dragMove(e) { if (dragging) { st.ui.aw = clampW(pageEl.getBoundingClientRect().right - e.clientX) } }
  function dragEnd() { if (dragging) { dragging = false; saveUi() } }
  function dragKey(e) {
    const cur = st.ui.aw ?? aside_w(); if (e.key === 'ArrowLeft') st.ui.aw = clampW(cur + 24); else if (e.key === 'ArrowRight') st.ui.aw = clampW(cur - 24); else if (e.key === 'Enter') st.ui.aw = null; else return
    e.preventDefault(); saveUi()
  }
  const aside_w = () => pageEl?.querySelector('.det')?.clientWidth ?? 380
</script>
<div class="wrap">
<div class="page" class:solo={!aside} class:wide class:open={openDet} class:off class:dragging bind:this={pageEl} style={awStyle}>
  <div class="sw">
    <div class="scroll" bind:this={sc} onscroll={measure}><div class="inner" class:center style={maxw ? `max-width:${maxw}px` : ''}>
    {#if title}<header class="ph">{#if stepNo > 0}<p class="eb">{t('j_step')} {stepNo} {t('of')} {STEPS.length}</p>{/if}<div class="pr"><h1>{title}</h1>{#if tools}<div class="tl">{@render tools()}</div>{/if}</div>{#if lead}<p class="ld">{lead}</p>{/if}</header>{/if}
    {@render children?.()}</div></div>
    {#if more}<div class="fade" aria-hidden="true"></div><button class="down" onclick={down} aria-label={t('scroll_down')} title={t('scroll_down')}>↓</button>{/if}
  </div>
  {#if aside}
    <aside class="det" aria-label={asideTitle || t('detail')}>
      {#if !off}<div class="grip" role="separator" aria-orientation="vertical" aria-label={t('col_resize')} title={t('col_resize')} tabindex="0" onpointerdown={dragStart} onpointermove={dragMove} onpointerup={dragEnd} onpointercancel={dragEnd} onkeydown={dragKey} ondblclick={() => { st.ui.aw = null; saveUi() }}></div>{/if}
      <div class="dh" class:pulse={pulse && !off}><button class="dhb" onclick={() => (openDet = !openDet)} aria-expanded={openDet}><span class="dt"><small>{t('detail')}</small><b>{asideTitle || t('detail')}</b>{#if asideSub}<em>{asideSub}</em>{/if}</span><span class="chev" aria-hidden="true">{openDet ? '▾' : '▴'}</span></button>
        <button class="col" onclick={toggleRight} aria-label={off ? t('col_expand') : t('col_collapse')} title={off ? t('col_expand') : t('col_collapse')}>{off ? '‹' : '›'}</button></div>
      <div class="db">{@render aside()}</div>
    </aside>
  {/if}
  {#if footer}<footer class="bar"><div class="in" class:center style={maxw ? `max-width:${maxw}px` : ''}>{@render footer()}</div></footer>{/if}
</div>
</div>
<style>
  .wrap{height:100%;container-type:inline-size;min-height:0}
  .page{display:grid;height:100%;min-height:0;grid-template-columns:minmax(0,1fr) var(--aw,clamp(320px,34%,440px));grid-template-rows:minmax(0,1fr) auto;grid-template-areas:"main det" "main bar";transition:grid-template-columns var(--t-base)}
  .page.wide{grid-template-columns:minmax(0,1fr) var(--aw,clamp(380px,46%,680px))}
  .page.dragging{transition:none;user-select:none}
  .page.solo{grid-template-columns:minmax(0,1fr);grid-template-areas:"main" "bar"}
  .page.off{grid-template-areas:"main det" "bar det"}
  .sw{grid-area:main;position:relative;min-height:0}
  .scroll{height:100%;overflow:auto;padding:var(--s6) var(--s6);overscroll-behavior:contain}
  .inner{margin:0 auto 0 0}.inner.center,.in.center{margin:0 auto}
  .ph{margin-bottom:var(--s6)}.eb{margin:0 0 var(--s1);font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600)}
  .pr{display:flex;align-items:center;justify-content:space-between;gap:var(--s3);flex-wrap:wrap}.ph h1{margin:0;font-size:26px;line-height:1.2}.tl{display:flex;gap:var(--s2)}
  .ld{margin:var(--s2) 0 0;color:var(--grey-800);font-size:15.5px;line-height:1.5;max-width:60ch}
  .det{grid-area:det;position:relative;min-height:0;display:flex;flex-direction:column;border-left:var(--border);background:var(--grey-50)}
  .grip{position:absolute;left:-4px;top:0;bottom:0;width:9px;cursor:col-resize;z-index:6}.grip::after{content:"";position:absolute;left:4px;top:0;bottom:0;width:2px;background:transparent;transition:background var(--t-fast)}
  .grip:hover::after,.grip:focus-visible::after,.dragging .grip::after{background:var(--ink)}
  .dh{flex:none;display:flex;align-items:stretch;border-bottom:var(--border);min-height:64px}
  .dhb{flex:1;min-width:0;text-align:left;display:flex;justify-content:space-between;align-items:center;background:none;border:0;padding:var(--s3) var(--s4) var(--s3) var(--s6);font:inherit;color:var(--ink);cursor:default}
  .col{flex:none;width:48px;background:none;border:0;border-left:1px solid transparent;cursor:pointer;font-size:20px;color:var(--grey-600)}.col:hover{background:var(--grey-100);color:var(--ink)}
  .dt{display:flex;flex-direction:column;gap:1px;min-width:0}.dt small{font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600)}.dt b{font-size:16px;line-height:1.3}.dt em{font-style:normal;font-size:13px;color:var(--grey-600)}
  .dh.pulse{animation:dhring 1.6s ease-in-out infinite}@keyframes dhring{0%,100%{box-shadow:inset 0 0 0 0 rgba(212,24,61,0)}50%{box-shadow:inset 0 0 0 3px rgba(212,24,61,.55)}}@media (prefers-reduced-motion:reduce){.dh.pulse{animation:none;box-shadow:inset 0 0 0 3px rgba(212,24,61,.55)}}
  .chev{display:none}
  .db{flex:1;min-height:0;overflow:auto;padding:var(--s4) var(--s6) var(--s6);overscroll-behavior:contain}
  .off .dhb,.off .db{display:none}.off .dh{flex-direction:column;border-bottom:0}.off .col{width:100%;height:56px}
  .fade{position:absolute;left:0;right:0;bottom:0;height:56px;background:linear-gradient(to bottom,rgba(255,255,255,0),var(--paper));pointer-events:none}
  .down{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);width:44px;height:44px;border-radius:50%;border:1px solid var(--ink);background:var(--ink);color:var(--paper);font-size:20px;line-height:1;cursor:pointer;
        box-shadow:0 2px 10px rgba(0,0,0,.18);animation:bob 1.6s ease-in-out infinite;z-index:5}
  .down:hover{opacity:.88}
  @keyframes bob{0%,100%{transform:translate(-50%,0)}50%{transform:translate(-50%,4px)}}
  @media (prefers-reduced-motion:reduce){.down{animation:none}.page{transition:none}}
  /* the action bar: under the right column when there is one, otherwise under the centre */
  .bar{grid-area:bar;border-top:var(--border);background:var(--paper);padding:var(--s3) var(--s6);min-width:0}
  .page:not(.solo):not(.off) .bar{background:var(--grey-50);border-left:var(--border)}
  .page:not(.solo):not(.off) .in{flex-wrap:wrap}.page:not(.solo):not(.off) .in :global(.btn){flex:1 1 auto;justify-content:center}.page:not(.solo):not(.off) .in :global(.sp),.page:not(.solo):not(.off) .in :global(.hn){display:none}
  .in{display:flex;gap:var(--s3);align-items:center;flex-wrap:wrap}
  .in :global(.sp){flex:1}
  @container (max-width:520px){.in :global(.lbl),.in :global(.hs){display:none}}
  @container (max-width:760px){.in :global(.hn){display:none}.in{flex-wrap:nowrap}.in :global(.btn){padding:0 var(--s4);white-space:nowrap}}
  /* narrow: detail drops below the main column, collapsed behind its header; the bar spans the bottom */
  @container (max-width:880px){
    .page,.page.wide,.page.off{grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(0,1fr) auto auto;grid-template-areas:"main" "det" "bar"}
    .det{border-left:0;border-top:var(--border);max-height:45dvh}.grip,.col{display:none}
    .dhb{cursor:pointer;padding-left:var(--s6)}.chev{display:inline}
    .db{display:none}.page.open .db{display:block}.off .dhb{display:flex}
    .page:not(.solo):not(.off) .bar{background:var(--paper);border-left:0}
    .page:not(.solo):not(.off) .in{flex-wrap:nowrap}.page:not(.solo):not(.off) .in :global(.btn){flex:0 0 auto}.page:not(.solo):not(.off) .in :global(.sp){display:block}
  }
  @media (max-width:900px){.scroll{padding:var(--s4)}.bar{padding:var(--s3) var(--s4)}.dhb{padding:var(--s3) var(--s4)}.db{padding:var(--s3) var(--s4)}}
</style>
