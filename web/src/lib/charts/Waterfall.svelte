<script>
  // Horizontal bridge: total A -> per-group change -> total B. Green up / red down, always with ▲▼ + number.
  import { rp, rpShort, pctSigned } from '../fmt.js'
  import { showTip, hideTip } from '../tip.svelte.js'
  import { termOf } from '../glossary.js'
  let { rows, onselect = () => {}, label = '' } = $props()
  const W = 720, L = 150, R = 110, H = 50
  const calc = $derived.by(() => {
    let cum = 0, max = 0; const out = []
    for (const r of rows) {
      const a = r.kind === 'total' ? 0 : cum, b = r.kind === 'total' ? r.value : cum + r.delta
      cum = b; out.push({ ...r, a, b }); max = Math.max(max, a, b)
    }
    return { out, max: max || 1 }
  })
  const x = (v) => L + (v / calc.max) * (W - L - R)
  const key = (e, r) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onselect(r.key) } }
</script>
<svg viewBox="0 0 {W} {rows.length * H + 8}" role="img" aria-label={label} class="wf">
  {#each calc.out as r, i}
    {@const y = 8 + i * H}
    {@const clickable = r.kind !== 'total' && r.key}
    <g role={clickable ? 'button' : 'listitem'} tabindex={clickable ? 0 : -1} class:click={clickable} aria-label="{r.label}: {r.kind === 'total' ? rp(r.value) : rp(r.delta)}"
       onclick={() => clickable && onselect(r.key)} onkeydown={(e) => clickable && key(e, r)}
       onmousemove={(e) => showTip(e, [r.label, r.kind === 'total' ? rp(r.value) : `${rp(r.a)} → ${rp(r.b)}`, ...(r.kind === 'total' ? [] : [`Perubahan ${rp(r.delta)}${r.pct != null ? ' (' + pctSigned(r.pct) + ')' : ''}`]), ...(r.note ? [r.note] : [])])}
       onmouseleave={hideTip}>
      <rect x="0" y={y} width={W} height={H - 2} fill="transparent" />
      <text x="0" y={y + 24} class="lbl" class:strong={r.kind === 'total'}>{r.label}</text>
      <rect x={x(Math.min(r.a, r.b))} y={y + 10} width={Math.max(3, Math.abs(x(r.b) - x(r.a)))} height="20" rx="4"
            fill={r.kind === 'total' ? 'var(--ink)' : r.delta >= 0 ? 'var(--ok-green)' : 'var(--alert-red)'} />
      <text x={x(Math.max(r.a, r.b)) + 8} y={y + 25} class="val">
        {#if r.kind === 'total'}{rpShort(r.value)}{:else}<tspan fill={r.delta >= 0 ? 'var(--ok-green)' : 'var(--alert-red)'}>{r.delta >= 0 ? '▲' : '▼'}</tspan> {r.delta >= 0 ? '+' : ''}{rpShort(r.delta)}{/if}
      </text>
      {#if r.note}{@const d = termOf(r.note)}<text x={L} y={y + 44} class="note" class:term={!!d} data-title={d?.title} data-tip={d?.tip} tabindex={d ? 0 : undefined}>{r.note}</text>{/if}
    </g>
  {/each}
</svg>
<style>
  .wf{width:100%;height:auto;display:block}
  .lbl{font-size:14px;fill:var(--ink)}.strong{font-weight:600}
  .val{font-size:13px;fill:var(--ink);font-variant-numeric:tabular-nums}
  .note{font-size:11.5px;fill:var(--grey-600)}
  .click{cursor:pointer}.click:hover .lbl{text-decoration:underline}
  g:focus-visible{outline:2px solid var(--ink)}
</style>
