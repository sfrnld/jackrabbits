<script>
  // "Who made this": a small popover opened by the 👋 button in the top bar.
  import { i18n, L } from './i18n.svelte.js'
  import { st } from './store.svelte.js'
  const onkey = (e) => e.key === 'Escape' && (st.about = false)
</script>
<svelte:window onkeydown={onkey} />
{#if st.about}
  <button class="scrim" aria-label={i18n.t('close')} onclick={() => (st.about = false)}></button>
  <div class="ab" role="dialog" aria-label={L('Tentang aplikasi ini', 'About this app')}>
    <button class="x" onclick={() => (st.about = false)} aria-label={i18n.t('close')}>✕</button>
    <p class="hi" aria-hidden="true">👋</p>
    <h2>{L('Halo!', 'Hello!')}</h2>
    <p>{L('Aplikasi ini dikembangkan oleh agen-agen AI yang diorkestrasi oleh', 'This app was developed by AI agents orchestrated by')} <a href="https://www.linkedin.com/in/sefrinaldi" target="_blank" rel="noopener noreferrer"><b>Aldi</b> ↗</a>.</p>
    <p class="mut">{L('Klik namanya untuk melihat profil LinkedIn.', 'Click the name to see the LinkedIn profile.')}</p>
  </div>
{/if}
<style>
  .scrim{position:fixed;inset:0;background:rgba(0,0,0,.28);border:0;z-index:90}
  .ab{position:fixed;top:72px;right:var(--s6);width:min(340px,calc(100vw - 2 * var(--s4)));background:var(--paper);border:1.5px solid var(--ink);border-radius:14px;padding:var(--s6);z-index:91;box-shadow:0 12px 32px rgba(0,0,0,.2);animation:pop .2s ease-out}
  .hi{font-size:34px;margin:0}h2{margin:var(--s1) 0 var(--s3);font-size:20px}p{margin:0 0 var(--s2);line-height:1.55}.mut{color:var(--grey-600);font-size:13.5px}
  a{color:var(--ink);text-decoration:underline;text-underline-offset:3px}a:hover{background:var(--grey-100)}
  .x{position:absolute;top:8px;right:10px;background:none;border:0;cursor:pointer;min-width:40px;min-height:40px;color:var(--grey-600);font-size:16px}
  @keyframes pop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
  @media (max-width:900px){.ab{right:var(--s4);top:64px}}
</style>
