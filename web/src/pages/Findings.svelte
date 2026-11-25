<script>
  import { untrack } from 'svelte'
  import { i18n } from '../lib/i18n.svelte.js'
  import { L } from '../lib/i18n.svelte.js'
  import { st, say, decide, undoDecision, applyAll } from '../lib/store.svelte.js'
  import { router } from '../lib/router.svelte.js'
  import { rpFull, num } from '../lib/fmt.js'
  import Page from '../lib/Page.svelte'
  import DataTable from '../lib/DataTable.svelte'
  const t = i18n.t
  let draft = $state({}), groupsSel = $state({}), renames = $state({}), idx = $state(0), started = false, pg
  // a few seconds of "analysing" the first time, so the work feels real (and Jackrabbit narrates it)
  const key = $derived(st.info?.name ?? 'data'), STEPS_A = ['reg', 'dup', 'ret', 'sal', 'out']
  let ai = $state(0)
  $effect(() => {
    if (!st.fs || st.analysedFor === key) return
    untrack(() => { st.analysing = true; ai = 0; say(L('Sedang menganalisa datamu…', 'Analysing your data…')) })
    const iv = setInterval(() => { ai++; if (ai >= STEPS_A.length) { clearInterval(iv); setTimeout(() => { st.analysedFor = key; st.analysing = false }, 500) } }, 2000)
    return () => clearInterval(iv)
  })
  // after the analysis: point at the evidence in the right column, with a pulsing header for a few seconds
  let pulseDet = $state(false)
  $effect(() => { if (st.analysing || !st.fs?.findings.length) return; pulseDet = true; const id = setTimeout(() => (pulseDet = false), 9000); return () => clearTimeout(id) })
  const fs = $derived(st.fs?.findings ?? [])
  const done = $derived(fs.filter((f) => f.decision).length)
  const f = $derived(fs[idx])
  const last = $derived(idx === fs.length - 1)
  // start on the first case that still needs a decision
  $effect(() => { if (!started && fs.length) { started = true; const k = fs.findIndex((x) => !x.decision); idx = k < 0 ? 0 : k } })
  $effect(() => { idx; pg?.top() })
  const short = (x) => { const v = t('fs_' + x.id); return v === 'fs_' + x.id ? x.title : v }
  const needsParams = (o) => o === 'merge_groups' || o === 'rename'
  // choosing an option only selects it; it is applied by the explicit button (or after a 30 s countdown)
  const pick = (x, o) => { draft[x.id] = o }
  const chosen = (x) => draft[x.id] ?? x.decision?.option
  const pend = (x) => !!x && !!draft[x.id] && draft[x.id] !== x.decision?.option
  let cd = $state(30)
  async function applyNow(x) { const o = draft[x.id]; if (!o) return; await decide(x.id, o); draft[x.id] = undefined }
  const cancel = (x) => { draft[x.id] = undefined }
  $effect(() => {
    const x = f; if (!x || !pend(x) || needsParams(draft[x.id])) return
    cd = 30
    const iv = setInterval(() => { cd--; if (cd <= 0) { clearInterval(iv); applyNow(x) } }, 1000)
    return () => clearInterval(iv)
  })
  const preview = (x) => x.options.find((o) => o.id === chosen(x))?.preview
  const apply = async (x) => { await decide(x.id, draft[x.id], draft[x.id] === 'merge_groups' ? { groups: x.groups.map((g) => g.canonical).filter((g) => groupsSel[x.id]?.[g] ?? true) } : { map: Object.fromEntries(Object.entries(renames[x.id] ?? {}).filter(([, v]) => v)) }); draft[x.id] = undefined }
  const next = () => { if (last) router.go('/studio/health'); else idx++ }
  async function useRec() { draft[f.id] = undefined; await decide(f.id, f.recommended); next() }
</script>

<Page bind:this={pg} wide pulse={pulseDet} title={t('c_title')} lead={t('c_lead')} asideTitle={f ? f.title : t('c_tbl_involved')} asideSub={f ? `${num(f.impact_rows)} ${t('c_rows')} · ${t('c_tbl_involved')}` : ''}>
  {#snippet tools()}<button class="btn secondary sm" onclick={applyAll} disabled={!fs.length || done === fs.length}>{t('c_all')}</button>{/snippet}

  {#if st.analysing}
    <div class="an" role="status" aria-live="polite"><b>{t('c_analysing')}</b>
      <ul>{#each STEPS_A as k, i}<li class:on={i < ai} class:cur={i === ai}><span aria-hidden="true">{i < ai ? '✓' : i === ai ? '…' : '○'}</span> {t('c_an_' + k)}</li>{/each}</ul></div>
  {:else if fs.length}
    <nav class="dots" aria-label={t('c_title')}>
      {#each fs as x, i}
        <button class="dot" class:cur={i === idx} class:ok={x.decision} class:bad={!x.decision} onclick={() => (idx = i)} aria-current={i === idx ? 'step' : undefined} title={x.title}>
          <span>{x.decision ? '✓' : '⚠️'}</span> {short(x)}
        </button>
      {/each}
    </nav>
    <p class="cnt num">{t('c_case')} {idx + 1} {t('of')} {fs.length}</p>

    {#if f}
      {#key f.id}
      <article class="card f" class:pend={!f.decision}>
        <header>
          <h2>{f.title}</h2>
          <span class="chip {f.decision ? 'ok' : 'bad'}">{f.decision ? '✓ ' + t('c_applied') : '⚠️ ' + t('c_pending')}</span>
        </header>
        <p class="imp"><b>{num(f.impact_rows)} {t('c_rows')}</b>{#if f.impact_rp}&nbsp;· <span class="num">{rpFull(f.impact_rp)}</span>{/if}</p>
        <h4 class="st"><span class="sn">1</span>{t('c_s_problem')}</h4>
        {#if t('c_prob_' + f.id) !== 'c_prob_' + f.id}<p class="prob">{t('c_prob_' + f.id)}</p>{/if}
        {#if f.groups && f.id === 'region'}<p class="grp">{#each f.groups as g}<span>{g.variants.join(', ')} → <b>{g.canonical}</b></span>{/each}</p>{/if}
        {#if f.groups && f.id === 'outlet_names'}
          <ul class="sp">{#each f.groups as g}
            <li><b>{g.outlet_id}</b>: {#each g.spellings as x, k}{#if k}<span class="vs">&nbsp;{t('c_sp_vs')}&nbsp;</span>{/if}<span class="spell" class:bad={x.issue}>“{x.text.trim()}{#if x.issue}<span class="ws2">&nbsp;</span>{/if}”</span> <span class="mut">({x.rows} {t('c_sp_rows')}{#if x.issue}, {x.issue}{/if})</span>{/each}
              → {t('c_sp_becomes')} <b>“{g.canonical}”</b></li>{/each}</ul>
        {/if}
        {#if f.id === 'duplicates'}<blockquote class="quote"><p>{t('c_dup_intro')}</p><cite>{f.compared_columns} {t('c_dup_cols')}</cite></blockquote>{/if}
        <h4 class="st"><span class="sn">2</span>{t('c_s_check')}</h4>
        <p class="hintR"><span class="arrow" aria-hidden="true">→</span> {t('c_hint_detail')}{#if !st.detShown}&nbsp;<button class="openR" onclick={() => st.detReq++}>{L('Buka panel Detail', 'Open the Detail panel')} →</button>{/if}</p>
        <h4 class="st"><span class="sn">3</span>{t('c_s_choose')}</h4>
        <fieldset>
          <legend class="sr">{f.title}</legend>
          {#each f.options as o}
            <label class="opt" class:sel={chosen(f) === o.id}>
              <input type="radio" name={f.id} checked={chosen(f) === o.id} onchange={() => pick(f, o.id)} />
              <span>{o.label}{#if o.id === f.recommended} <em>{t('c_rec')}</em>{/if}</span>
            </label>
          {/each}
        </fieldset>
        <div class="impact" class:empty={!preview(f)} aria-live="polite"><span class="il">{t('c_impact')}{#if chosen(f)}&nbsp;·&nbsp;{f.options.find((o) => o.id === chosen(f))?.label}{/if}</span><b>{preview(f) ?? t('c_impact_none')}</b></div>
        {#if pend(f) && !needsParams(draft[f.id])}
          <div class="cf" role="status" aria-live="polite"><div class="cft"><b>{t('c_will_apply')}</b> <span class="num">{cd}{t('c_sec')}</span></div><div class="bar"><i style="width:{(cd / 30) * 100}%"></i></div>
            <span class="cfb"><button class="btn" onclick={() => applyNow(f)}>{t('c_apply_now')}</button><button class="btn secondary" onclick={() => cancel(f)}>{t('c_cancel')}</button></span></div>
        {/if}
        {#if chosen(f) === 'merge_groups'}
          <div class="par"><b>{t('c_groups')}</b>{#each f.groups as g}<label><input type="checkbox" checked={groupsSel[f.id]?.[g.canonical] ?? true} onchange={(e) => ((groupsSel[f.id] ??= {})[g.canonical] = e.currentTarget.checked)} /> {g.canonical} ({g.variants.join(', ')})</label>{/each}<span class="cfb"><button class="btn" onclick={() => apply(f)}>{t('c_apply_now')}</button><button class="btn secondary" onclick={() => cancel(f)}>{t('c_cancel')}</button></span></div>
        {:else if chosen(f) === 'rename'}
          <div class="par"><b>{t('c_rename')}</b>{#each f.groups.flatMap((g) => g.variants) as v}<label>{v} → <input value={renames[f.id]?.[v] ?? ''} oninput={(e) => ((renames[f.id] ??= {})[v] = e.currentTarget.value)} placeholder={v} /></label>{/each}<span class="cfb"><button class="btn" onclick={() => apply(f)}>{t('c_apply_now')}</button><button class="btn secondary" onclick={() => cancel(f)}>{t('c_cancel')}</button></span></div>
        {/if}
        {#if f.decision}<button class="undo" onclick={() => { draft[f.id] = undefined; undoDecision(f.id) }}>{t('c_undo')}</button>{/if}
      </article>
      {/key}
    {/if}
  {:else}
    <p class="clean">✓ {t('c_clean')}</p>
  {/if}

  {#snippet aside()}
    {#if f}<DataTable table={f.table} chosen={chosen(f)} />{:else}<p class="mut">—</p>{/if}
  {/snippet}
  {#snippet footer()}
    {#if fs.length}
      <button class="btn secondary" onclick={() => (idx = Math.max(0, idx - 1))} disabled={idx === 0}>←<span class="lbl">&nbsp;{t('c_prev_label')}</span></button>
      <span class="mut num hn">{done}/{fs.length} {t('c_decided')}</span><span class="sp"></span>
      {#if f && !f.decision}
        <button class="btn secondary hs" onclick={next}>{last ? t('c_next') : t('c_skip')}</button>
        <button class="btn" onclick={useRec}>{last ? t('c_use_rec') : t('c_use_rec_next')}</button>
      {:else}
        <button class="btn" onclick={next}>{last ? t('c_next') : t('c_nextcase')}</button>
      {/if}
    {:else}
      <span class="sp"></span><button class="btn" onclick={() => router.go('/studio/health')}>{t('c_next')}</button>
    {/if}
  {/snippet}
</Page>

<style>
  .top{display:flex;align-items:center;justify-content:space-between;gap:var(--s3);flex-wrap:wrap;margin-bottom:var(--s3)}h1{font-size:24px;margin:0}
  .btn.sm{min-height:40px;padding:0 var(--s4);font-size:14px}.btn:disabled{opacity:.35;cursor:not-allowed}
  .dots{display:flex;gap:var(--s2);flex-wrap:wrap;margin-bottom:var(--s2)}
  .dot{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--grey-200);background:var(--paper);border-radius:99px;padding:0 14px;min-height:38px;font:inherit;font-size:13.5px;cursor:pointer;color:var(--grey-600)}
  .dot.ok{border-color:var(--ok-green);color:var(--ok-green)}.dot.bad{border-color:var(--alert-red);color:var(--alert-red)}.dot.cur{background:var(--ink);border-color:var(--ink);color:var(--paper);font-weight:600}
  .cnt{margin:var(--s2) 0 var(--s3);font-size:13px;color:var(--grey-600)}.clean{color:var(--ok-green);font-weight:600;font-size:17px}
  .mut{color:var(--grey-600)}
  .f{max-width:none}.f.pend{border-left:3px solid var(--alert-red)}
  header{display:flex;justify-content:space-between;align-items:center;gap:var(--s3);flex-wrap:wrap}h2{margin:0;font-size:18px}
  .chip{font-size:12.5px;font-weight:500;padding:3px 10px;border-radius:99px}.chip.ok{background:var(--ok-green-bg);color:var(--ok-green)}.chip.bad{background:var(--alert-red-bg);color:var(--alert-red)}
  .imp{margin:var(--s2) 0;color:var(--grey-800)}.grp{display:flex;flex-direction:column;gap:2px;font-size:13.5px;color:var(--grey-600);margin:0 0 var(--s2)}.grp b{color:var(--ink)}
  fieldset{border:0;padding:0;margin:var(--s3) 0 0;display:flex;flex-direction:column}.sr{position:absolute;left:-9999px}
  .opt{display:flex;gap:var(--s3);align-items:center;padding:8px 10px;border-radius:8px;cursor:pointer;min-height:44px}.opt:hover{background:var(--grey-50)}.opt.sel{background:var(--grey-100)}
  .opt input{width:18px;height:18px;accent-color:var(--ink)}em{font-style:normal;font-size:12px;border:1px solid var(--ink);border-radius:99px;padding:0 8px;margin-left:6px}
  .par{display:flex;flex-direction:column;gap:var(--s2);padding:var(--s3);background:var(--grey-50);border-radius:8px;margin-top:var(--s2)}.par label{font-size:14px}.par input:not([type]),.par input[type=text]{min-height:36px;border:1px solid var(--grey-200);border-radius:6px;padding:0 8px}.par .btn{align-self:flex-start}
  .prev{margin:var(--s3) 0 0;font-size:13.5px;color:var(--grey-600)}.dupi{font-size:14px;margin:var(--s2) 0;max-width:68ch}
  .sp{list-style:none;margin:0 0 var(--s2);padding:0;font-size:13.5px;display:flex;flex-direction:column;gap:4px}.spell{font-weight:600}.spell.bad{color:var(--alert-red)}.vs{color:var(--grey-600)}
  .ws2{display:inline-block;width:.7em;height:1em;vertical-align:text-bottom;background:#FFD60A;border:1px solid #B38F00;border-radius:2px;margin:0 1px}
  .ti{font-size:13px;color:var(--grey-600);font-weight:500;margin:var(--s3) 0 0}
  .undo{margin-top:var(--s2);background:none;border:0;color:var(--grey-600);text-decoration:underline;cursor:pointer;font:inherit;font-size:13px;min-height:36px}
.an{border:var(--border);border-radius:12px;padding:var(--s6);display:flex;flex-direction:column;gap:var(--s3);align-items:stretch}.an b{font-size:18px}.an .sp{width:28px;height:28px;border:3px solid var(--grey-200);border-top-color:var(--ink);border-radius:50%;animation:spin .8s linear infinite}.an ul{list-style:none;margin:0;padding:0;display:grid;gap:6px;color:var(--grey-600)}.an li.on{color:var(--ok-green)}.an li.cur{color:var(--ink);font-weight:600}@keyframes spin{to{transform:rotate(360deg)}}@media (prefers-reduced-motion:reduce){.an .sp{animation:none}}
.cf{margin-top:var(--s3);border:1.5px solid var(--ink);border-radius:10px;padding:var(--s3) var(--s4);display:flex;flex-direction:column;gap:var(--s2)}.cft{display:flex;justify-content:space-between;gap:var(--s3);font-size:14px}.bar{height:4px;background:var(--grey-100);border-radius:99px;overflow:hidden}.bar i{display:block;height:100%;background:var(--ink);transition:width 1s linear}.cfb{display:flex;gap:var(--s2);flex-wrap:wrap}.cfb .btn{min-height:44px}
.impact{margin:var(--s3) 0 var(--s4);padding:var(--s4) var(--s5);background:var(--ok-green-bg);border:1.5px solid var(--ok-green);border-radius:10px;display:flex;flex-direction:column;gap:var(--s1)}.impact .il{font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--ok-green)}.impact b{font-size:18px;line-height:1.4}.impact.empty{background:var(--grey-50);border:1.5px dashed var(--grey-200)}.impact.empty .il{color:var(--grey-600)}.impact.empty b{font-weight:400;color:var(--grey-600);font-size:15px}
.hintR{display:flex;gap:var(--s2);align-items:flex-start;margin:var(--s2) 0 0;padding:var(--s2) var(--s3);background:var(--grey-100);border-radius:8px;font-size:14px;color:var(--grey-800)}.hintR .arrow{font-weight:700;color:var(--alert-red);animation:nudge 1.4s ease-in-out infinite}@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(4px)}}@media (prefers-reduced-motion:reduce){.hintR .arrow{animation:none}}@container (max-width:880px){.hintR .arrow{transform:rotate(90deg)}}
.st{display:flex;align-items:center;gap:var(--s2);margin:var(--s5) 0 var(--s2);font:600 13px var(--font);letter-spacing:.05em;text-transform:uppercase;color:var(--grey-600)}.sn{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--ink);color:#fff;font-size:12px}.prob{margin:0 0 var(--s2);font-size:15.5px;line-height:1.5}.impact{margin-top:var(--s4)}
.openR{background:var(--ink);color:#fff;border:0;border-radius:99px;padding:4px 14px;margin-left:var(--s2);min-height:32px;font:600 13px var(--font);cursor:pointer;white-space:nowrap}.openR:hover{opacity:.85}
</style>
