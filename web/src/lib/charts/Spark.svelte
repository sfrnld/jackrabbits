<script>
  import { rp, rpShort } from '../fmt.js'
  import { showTip, hideTip } from '../tip.svelte.js'
  let { values, labels, name = '' } = $props()
  const W = 220, H = 56, P = 6
  const max = $derived(Math.max(1, ...values))
  const px = (i) => P + (i / Math.max(1, values.length - 1)) * (W - 2 * P)
  const py = (v) => H - P - (v / max) * (H - 2 * P)
  const pts = $derived(values.map((v, i) => `${px(i)},${py(v)}`).join(' '))
  function move(e) {
    const r = e.currentTarget.getBoundingClientRect(), i = Math.round(((e.clientX - r.left) / r.width) * (values.length - 1))
    const j = Math.max(0, Math.min(values.length - 1, i)); showTip(e, [name, labels[j], rp(values[j])])
  }
</script>
<svg viewBox="0 0 {W} {H}" role="img" aria-label="{name}: {rpShort(values.at(-1) ?? 0)} minggu terakhir" onmousemove={move} onmouseleave={hideTip} class="sp">
  <line x1={P} x2={W - P} y1={H - P} y2={H - P} stroke="var(--grey-200)" />
  <polyline points={pts} fill="none" stroke="var(--ink)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
  {#if values.length}<circle cx={px(values.length - 1)} cy={py(values.at(-1))} r="4" fill="var(--ink)" stroke="var(--paper)" stroke-width="2" />{/if}
</svg>
<style>.sp{width:100%;height:auto;display:block}</style>
