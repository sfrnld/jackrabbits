<script>let { state = 'ready' } = $props()</script>
<span class="orb {state}" role="img" aria-label={state}></span>
<style>
  .orb{display:inline-block;width:14px;height:14px;border-radius:50%;background:var(--ink)}
  .thinking{animation:p 1s ease-in-out infinite}.done{background:var(--ok-green)}
  @keyframes p{50%{opacity:.3}}
  @media (prefers-reduced-motion:reduce){.thinking{animation:none}}
</style>
