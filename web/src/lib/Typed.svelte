<script>
  // Typing effect; renders full text instantly under reduced motion.
  let { text, speed = 14 } = $props()
  import { glossHtml } from './glossary.js'
  let shown = $state(''), done = $state(false)
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
  $effect(() => {
    const full = text                      // read here so the effect re-runs when the text changes
    done = false
    if (reduce) { shown = full; done = true; return }
    shown = ''; let i = 0
    const id = setInterval(() => { shown = full.slice(0, ++i); if (i >= full.length) { clearInterval(id); done = true } }, speed)
    return () => clearInterval(id)
  })
</script>
<span aria-label={text}>{#if done}{@html glossHtml(text)}{:else}{shown}{/if}</span>
