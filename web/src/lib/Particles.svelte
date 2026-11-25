<script>
  // "Thinking" animation: particles gathered into a slowly turning ring, like an enigma. Black / grey on white.
  import { onMount } from 'svelte'
  let { height = 170 } = $props()
  let cv, raf = 0
  onMount(() => {
    const ctx = cv.getContext('2d'), reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
    let W = 0, H = 0, t = 0
    const dpr = Math.min(2, devicePixelRatio || 1)
    const gauss = () => (Math.random() + Math.random() + Math.random() - 1.5) / 1.5          // -1..1, bell-shaped
    // the ring: most particles hug the circle, a thinner halo drifts outside it, a few sit in the middle
    const P = [
      ...Array.from({ length: 260 }, () => ({ a: Math.random() * 6.283, r: 1 + gauss() * 0.045, w: 0.0022 + Math.random() * 0.0012, s: 0.7 + Math.random() * 1.2, g: Math.floor(Math.random() * 110), ph: Math.random() * 6.283 })),
      ...Array.from({ length: 90 }, () => ({ a: Math.random() * 6.283, r: 1.12 + Math.abs(gauss()) * 0.22, w: -0.0014 - Math.random() * 0.0008, s: 0.5 + Math.random() * 0.9, g: 90 + Math.floor(Math.random() * 100), ph: Math.random() * 6.283 })),
      ...Array.from({ length: 36 }, () => ({ a: Math.random() * 6.283, r: Math.random() * 0.55, w: 0.0008 + Math.random() * 0.001, s: 0.5 + Math.random() * 0.8, g: 120 + Math.floor(Math.random() * 100), ph: Math.random() * 6.283 })),
    ]
    const size = () => { const b = cv.getBoundingClientRect(); W = b.width; H = b.height; cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0) }
    const ro = new ResizeObserver(size); ro.observe(cv); size()
    function draw() {
      t += 1
      ctx.clearRect(0, 0, W, H)
      const cx = W / 2, cy = H / 2, R = Math.min(H * 0.42, W * 0.3), tilt = 0.82                // a slightly tilted circle (an ellipse), for depth
      for (const p of P) {
        if (!reduce) p.a += p.w
        const breathe = 1 + Math.sin(t * 0.012 + p.ph) * 0.012
        const x = cx + Math.cos(p.a) * R * p.r * breathe * 1.25, y = cy + Math.sin(p.a) * R * p.r * breathe * tilt
        const depth = 0.55 + 0.45 * Math.sin(p.a)                                               // the near side is bigger and darker
        const al = Math.max(0.12, Math.min(0.95, depth * (0.55 + 0.4 * Math.sin(t * 0.02 + p.ph))))
        ctx.fillStyle = `rgba(${p.g},${p.g},${p.g},${al})`
        ctx.beginPath(); ctx.arc(x, y, p.s * (1 + depth * 0.8), 0, 6.283); ctx.fill()
      }
      if (!reduce) raf = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(raf); ro.disconnect() }
  })
</script>
<canvas bind:this={cv} class="pt" style="height:{height}px" aria-hidden="true"></canvas>
<style>.pt{display:block;width:100%;background:#fff;border-radius:10px}</style>
