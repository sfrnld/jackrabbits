<script>
  // Single-hue horizontal bars. Optional per-row `hi` = 'neg' | 'pos' to draw attention.
  import { rpShort } from '../fmt.js'
  import { showTip, hideTip } from '../tip.svelte.js'
  let { rows, onselect = () => {}, label = '', fmt = rpShort } = $props()
  const max = $derived(Math.max(1, ...rows.map((r) => Math.abs(r.value))))
</script>
<ul class="bars" aria-label={label}>
  {#each rows as r (r.key)}
    <li>
      <button class="row" onclick={() => onselect(r.key)} onmousemove={(e) => showTip(e, [r.label, fmt(r.value), ...(r.note ? [r.note] : [])])} onmouseleave={hideTip}>
        <span class="name">{r.label}</span>
        <span class="track"><span class="bar" style="width:{Math.max(1, (Math.abs(r.value) / max) * 100)}%;background:{r.hi === 'neg' ? 'var(--alert-red)' : r.hi === 'pos' ? 'var(--ok-green)' : 'var(--ink)'}"></span></span>
        <span class="v num">{fmt(r.value)}</span>
        {#if r.badge}<span class="badge {r.hi}">{r.hi === 'neg' ? '▼' : '▲'} {r.badge}</span>{/if}
      </button>
    </li>
  {/each}
</ul>
<style>
  .bars{list-style:none;margin:0;padding:0}
  .row{display:grid;grid-template-columns:150px 1fr 70px 76px;align-items:center;gap:var(--s3);width:100%;background:none;border:0;padding:6px 0;cursor:pointer;font:inherit;text-align:left;color:var(--ink);min-height:36px}
  .row:hover .name{text-decoration:underline}
  .name{font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .track{height:14px;display:block}.bar{display:block;height:14px;border-radius:0 4px 4px 0}
  .v{font-size:13px;text-align:right}
  .badge{font-size:12px;text-align:right}.badge.neg{color:var(--alert-red)}.badge.pos{color:var(--ok-green)}
  @media (max-width:520px){.row{grid-template-columns:100px 1fr 60px}.badge{display:none}}
</style>
