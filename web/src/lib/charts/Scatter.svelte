<script>
  // Outlet scatter: invoices (x) vs net sales (y). Weak outlets are red + labelled; the rest stay grey.
  import { rp, rpShort, num } from '../fmt.js'
  import { showTip, hideTip } from '../tip.svelte.js'
  import { termOf } from '../glossary.js'
  let { points, onselect = () => {}, xLabel = '', yLabel = '', hl = null } = $props()
  const dx = $derived(termOf(xLabel)), dy = $derived(termOf(yLabel))
  const W = 720, H = 340, L = 64, R = 16, T = 12, B = 44
  const maxX = $derived(Math.max(1, ...points.map((p) => p.x)) * 1.08), maxY = $derived(Math.max(1, ...points.map((p) => p.y)) * 1.08)
  const sx = (v) => L + (v / maxX) * (W - L - R), sy = (v) => H - B - (v / maxY) * (H - T - B)
  const ticks = (m) => { const s = Math.pow(10, Math.floor(Math.log10(m / 4))), k = [1, 2, 5, 10].find((f) => (m / (s * f)) <= 5) * s; return Array.from({ length: Math.floor(m / k) + 1 }, (_, i) => i * k) }
</script>
<svg viewBox="0 0 {W} {H}" role="img" aria-label="{yLabel} per {xLabel}" class="sc">
  {#each ticks(maxY) as t}<line x1={L} x2={W - R} y1={sy(t)} y2={sy(t)} stroke="var(--grey-100)" /><text x={L - 8} y={sy(t) + 4} text-anchor="end" class="ax">{rpShort(t)}</text>{/each}
  {#each ticks(maxX) as t}<text x={sx(t)} y={H - B + 18} text-anchor="middle" class="ax">{t}</text>{/each}
  <text x={(L + W - R) / 2} y={H - 6} text-anchor="middle" class="ax lab" class:term={!!dx} data-title={dx?.title} data-tip={dx?.tip} tabindex={dx ? 0 : undefined}>{xLabel}</text>
  <text x={L + 6} y={T + 8} class="ax lab" class:term={!!dy} data-title={dy?.title} data-tip={dy?.tip} tabindex={dy ? 0 : undefined}>{yLabel}</text>
  {#each points.filter((p) => !p.weak) as p (p.id)}
    <circle cx={sx(p.x)} cy={sy(p.y)} r="6" fill="var(--grey-400)" stroke="var(--paper)" stroke-width="2" class="pt" role="button" tabindex="0" aria-label="{p.name}"
      onclick={() => onselect(p.id)} onkeydown={(e) => e.key === 'Enter' && onselect(p.id)} onmousemove={(e) => showTip(e, p.tip)} onmouseleave={hideTip} />
  {/each}
  {#each points.filter((p) => p.weak) as p (p.id)}
    <g class="pt" style="opacity:{hl && hl !== p.id ? 0.22 : 1};transition:opacity .15s" role="button" tabindex="0" aria-label="{p.rank}. {p.name} (lemah)" onclick={() => onselect(p.id)} onkeydown={(e) => e.key === 'Enter' && onselect(p.id)}
       onmousemove={(e) => showTip(e, p.tip)} onmouseleave={hideTip}>
      <circle cx={sx(p.x)} cy={sy(p.y) - (p.rank - 3) * 3} r="10" fill="var(--alert-red)" stroke="var(--paper)" stroke-width="2" />
      <text x={sx(p.x)} y={sy(p.y) - (p.rank - 3) * 3 + 4} text-anchor="middle" class="rk">{p.rank}</text>
    </g>
  {/each}
</svg>
<style>
  .sc{width:100%;height:auto;display:block}.ax{font-size:11px;fill:var(--grey-600)}.lab{font-size:12px;font-weight:600;fill:var(--ink)}
  .pt{cursor:pointer}.pt:focus-visible{outline:2px solid var(--ink)}.rk{font-size:11px;fill:#fff;font-weight:700;pointer-events:none}
</style>
