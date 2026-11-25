<script>
  // Spreadsheet-style view of the rows a finding involves: the user's own headers and raw values and the row number
  // as it appears in Excel/CSV. The problem columns are pinned right after Status and marked with a warning sign.
  // Spelling findings also show a reference row (the correct spelling) so the difference can be seen side by side.
  // mode="decide": shows the problem.  mode="result": shows what the decision did (before → after).
  import { i18n } from './i18n.svelte.js'
  let { table, chosen = undefined, mode = 'decide' } = $props()
  const t = i18n.t, W = '⚠️'
  const WHY = { 'spasi di akhir': 'why_trail', 'spasi di awal': 'why_lead', 'spasi di awal dan akhir': 'why_both', 'spasi ganda': 'why_dbl', 'huruf besar/kecil beda': 'why_case', singkatan: 'why_abbr', 'ejaan lain': 'why_other' }
  const hiCols = $derived(table.columns.filter((c) => table.rows.some((r) => r.hi.includes(c) && r.role !== 'reference')))
  const pinned = $derived((table.pinned ?? []).filter((c) => !hiCols.includes(c)))
  const refCols = $derived(table.columns.filter((c) => table.rows.some((r) => r.role === 'reference' && r.hi.includes(c))))
  const cols = $derived([...new Set([...hiCols, ...refCols, ...pinned, ...table.columns])])
  const span = $derived(table.columns.length + 2)
  const result = $derived(mode === 'result' && !!chosen)
  const stillBad = $derived(chosen === 'keep' || chosen === 'flag')
  const flagged = $derived(!result || stillBad)      // warning marks disappear once a decision resolved the problem
  const changed = (r) => r.removed || r.hi.some((c) => r.after && r.after[c] !== r.cells[c])
  const hasWs = $derived(table.rows.some((r) => Object.values(r.cells).some((v) => v != null && v !== v.trim())))
  const hasRef = $derived(table.rows.some((r) => r.role === 'reference'))
  const whyText = (r) => (r.why ? (WHY[r.why] ? t(WHY[r.why]) : r.why) : t('rl_variant'))
  function status(r) {
    if (r.role === 'keep') return { ok: true, text: result ? t('rs_original') : t('rl_keep') }
    if (r.role === 'reference') return { ok: true, text: t('rl_ref') }
    if (result) {
      if (r.removed) return { ok: true, text: t('rs_removed') }
      const o = chosen
      const text = o === 'flag' ? t('rs_flagged') : o === 'keep' ? t('rs_kept') : o === 'deduct' ? t('rs_deducted') : o === 'separate' ? t('rs_separated') : o === 'exclude' ? t('rs_excluded')
        : o === 'label' ? t('rs_labeled') : o === 'fill_dominant' ? t('rs_filled') : changed(r) ? t('rs_fixed') : t('rs_kept')
      return { ok: !(o === 'keep' || o === 'flag' || (r.role === 'variant' && !changed(r))), text }
    }
    const base = r.role === 'copy' ? `${t('rl_copy')} → ${chosen === 'drop' ? t('c_dup_drop') : chosen === 'flag' ? t('c_dup_flag') : chosen === 'keep' ? t('c_dup_keep') : t('c_dup_pending')}`
      : r.role === 'return' ? `${t('rl_return')}${chosen ? ' → ' + t('rl_' + chosen) : ''}` : r.role === 'variant' ? `${whyText(r)} → “${r.label}”` : t('rl_' + r.role)
    return { ok: false, text: base }
  }
  const lead = (v) => v.length - v.trimStart().length, trail = (v) => v.length - v.trimEnd().length
</script>

{#snippet val(v, q)}
  {#if v == null}<i>{t('c_tbl_empty')}</i>
  {:else}{#if q}“{/if}{#if lead(v)}<span class="ws" title="spasi tersembunyi">&nbsp;</span>{/if}{v.trim()}{#if trail(v)}<span class="ws" title="spasi tersembunyi">&nbsp;</span>{/if}{#if q}”{/if}{/if}
{/snippet}

<div class="tw" role="region" aria-label={t('c_tbl_involved')} tabindex="0">
  <table class="dt">
    <thead><tr><th class="gut">{t('c_tbl_row')}</th><th class="st">{t('c_tbl_status')}</th>
      {#each cols as c}<th class:r={table.numeric.includes(c)} class:hh={hiCols.includes(c) && flagged} class:pin={pinned.includes(c)}>{#if hiCols.includes(c) && flagged}{W} {/if}{c}</th>{/each}</tr></thead>
    <tbody>
      {#each table.rows as r, i}
        {@const s = status(r)}
        {#if r.group != null && (i === 0 || table.rows[i - 1].group !== r.group)}
          <tr class="grp"><td colspan={span}>{r.group_label ?? `${t('c_tbl_pair')} ${r.group + 1} · ${t('c_tbl_same')}`}</td></tr>
        {/if}
        <tr class="{r.role} {result && r.removed ? 'removed' : ''}">
          <td class="gut">{r.line}</td>
          <td class="st"><span class="chip" class:ok={s.ok} class:bad={!s.ok}>{s.ok ? '✓' : W} {s.text}</span></td>
          {#each cols as c}
            {@const hi = r.hi.includes(c)}
            {@const quote = hi && (r.role === 'variant' || r.role === 'reference')}
            <td class:r={table.numeric.includes(c)} class:pin={pinned.includes(c)} class:ref={hi && r.role === 'reference'}
                class:hi={hi && r.role !== 'reference' && !(result && !stillBad)} class:fixed={hi && r.role !== 'reference' && result && !stillBad && changed(r)}>
              {#if hi && r.role !== 'reference' && result && !stillBad && r.after && r.after[c] !== r.cells[c]}
                <s>{@render val(r.cells[c], quote)}</s> → <b>{@render val(r.after[c], quote)}</b>
              {:else if hi && r.role === 'reference'}✓ {@render val(r.cells[c], quote)}
              {:else if hi && !(result && !stillBad)}{W} {@render val(r.cells[c], quote)}
              {:else}{@render val(r.cells[c], false)}{/if}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
{#if table.hidden}<p class="more">+ {table.hidden.toLocaleString('id-ID')} {t('c_tbl_more')}</p>{/if}
<p class="note">{t('c_tbl_note')}{#if hasRef}&nbsp;{t('c_tbl_refnote')}{/if}</p>
{#if hasWs}<p class="note"><span class="ws demo">&nbsp;</span> {t('c_tbl_ws')}</p>{/if}

<style>
  .tw{overflow:auto;max-width:100%;border:var(--border);border-radius:8px;margin-top:var(--s2)}.tw:focus-visible{outline:2px solid var(--ink)}
  .dt{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;font-size:12.5px}
  th,td{padding:6px 10px;border-bottom:1px solid var(--grey-100);border-right:1px solid var(--grey-100);white-space:nowrap;text-align:left}
  th{background:var(--grey-50);color:var(--grey-600);font-weight:600;position:sticky;top:0;border-bottom:var(--border)}
  th.hh{background:var(--alert-red-bg);color:var(--alert-red)}th.pin{color:var(--ink)}td.pin{font-weight:600}
  .r{text-align:right;font-variant-numeric:tabular-nums}
  .gut{position:sticky;left:0;z-index:2;background:var(--grey-50);color:var(--grey-600);text-align:right;font:12px var(--mono);min-width:52px;border-right:var(--border)}
  .st{position:sticky;left:52px;z-index:2;background:var(--paper);border-right:var(--border)}
  tr.keep td:not(.hi):not(.fixed),tr.reference td{background:var(--ok-green-bg)}tr.copy td:not(.hi):not(.fixed){background:var(--alert-red-bg)}
  tr.keep .gut,tr.copy .gut,tr.reference .gut{background:var(--grey-50)}tr.keep .st,tr.reference .st{background:var(--ok-green-bg)}tr.copy .st{background:var(--alert-red-bg)}
  tr.removed td:not(.gut){opacity:.55;text-decoration:line-through}tr.removed .st{text-decoration:none;opacity:1}tr.removed .st,tr.removed td{background:var(--grey-50)!important}
  td.hi{background:var(--alert-red-bg);color:var(--alert-red);font-weight:700;box-shadow:inset 0 0 0 2px var(--alert-red)}
  td.ref{color:var(--ok-green);font-weight:700;box-shadow:inset 0 0 0 2px var(--ok-green)}
  td.fixed{background:var(--ok-green-bg);box-shadow:inset 0 0 0 2px var(--ok-green)}td.fixed s{color:var(--grey-600);font-weight:400}td.fixed b{color:var(--ok-green)}
  td i{color:var(--alert-red)}
  .chip{font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:99px;background:var(--paper)}.chip.ok{color:var(--ok-green)}.chip.bad{color:var(--alert-red)}
  .ws{display:inline-block;width:.75em;height:1.1em;vertical-align:text-bottom;background:#FFD60A;border:1px solid #B38F00;border-radius:2px;margin:0 1px}.ws.demo{vertical-align:middle}
  .grp td{background:var(--grey-100);color:var(--grey-800);font-weight:600;font-size:12px;position:sticky;left:0}
  .more,.note{font-size:12.5px;color:var(--grey-600);margin:var(--s2) 0 0}
</style>
