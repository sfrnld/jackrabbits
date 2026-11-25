<script>
  import { untrack, tick } from 'svelte'
  import { i18n } from '../lib/i18n.svelte.js'
  import { st, setFilters, refreshInsights, guard, ask, saveViews, say } from '../lib/store.svelte.js'
  import { router } from '../lib/router.svelte.js'
  import { L } from '../lib/i18n.svelte.js'
  import { api } from '../lib/api.js'
  import { rp, rpShort, num, pct, pctSigned, monthLabel, monthShort } from '../lib/fmt.js'
  import Waterfall from '../lib/charts/Waterfall.svelte'
  import BarList from '../lib/charts/BarList.svelte'
  import Spark from '../lib/charts/Spark.svelte'
  import Scatter from '../lib/charts/Scatter.svelte'
  import { glossHtml, glossify } from '../lib/glossary.js'
  import Page from '../lib/Page.svelte'
  const t = i18n.t
  const DRILL = ['region', 'branch', 'outlet_id', 'invoice']
  const DIMN = { region: 'Region', branch: 'Cabang', brand: 'Brand', sku: 'SKU', outlet_type: 'Tipe outlet', salesman: 'Salesman', outlet_id: 'Outlet', invoice: 'Invoice', month: 'Bulan', week: 'Minggu' }
  const FILT = ['region', 'branch', 'brand', 'outlet_type', 'salesman', 'sku', 'month']
  const METRICS = ['net', 'gross', 'qty', 'invoices', 'discount', 'discount_ratio']
  let tab = $state(st.tab), seen = $state({ sum: true }), metric = $state('net'), pgroup = $state(null), sortKey = $state('b'), sortDir = $state(-1)
  let D = $state({ loading: true }), seq = 0, sel = $state(null), copied = $state(false)
  let addDim = $state(''), addVals = $state([]), viewName = $state('')

  const opts = $derived(st.options ?? {})
  const has = (d) => !!opts[d]?.length
  const months = $derived(opts.month ?? [])
  const per = $derived(months.length >= 2 && !st.filters.month ? [months.at(-2), months.at(-1)] : null)
  const drillDim = $derived(st.filters.outlet_id ? 'invoice' : st.filters.branch ? 'outlet_id' : st.filters.region ? 'branch' : 'region')
  const defGroup = $derived({ sum: drillDim, brand: 'brand', outlet: 'outlet_id', sales: 'salesman' }[tab])
  const pg = $derived(pgroup ?? defGroup)
  const additive = $derived(['net', 'gross', 'qty', 'discount'].includes(metric) && ['region', 'branch', 'outlet_id'].includes(drillDim))
  const mfmt = (v) => (metric === 'discount_ratio' ? pct(v * 100) : ['net', 'gross', 'discount'].includes(metric) ? rpShort(v) : num(v))
  const tone = (p, th = 10) => (p == null ? '' : p <= -th ? 'neg' : p >= th ? 'pos' : '')
  const cur = (r) => (per ? r.b : r.value)
  const nm = (k) => D.names?.[k] ?? k

  async function load() {
    const my = ++seq; D.loading = true
    const f = $state.snapshot(st.filters), fNoM = { ...f }; delete fNoM.month
    const Q = (extra) => api('/analytics/query', { filters: f, compare: per, ...extra })
    try {
      const [main, kInv, kDisc, outl, piv, brand, series, sales] = await Promise.all([
        Q({ group_by: drillDim, metric }), Q({ metric: 'invoices' }), Q({ metric: 'discount_ratio' }),
        api('/analytics/outlets', { filters: f }), Q({ group_by: pg, metric }),
        tab === 'brand' && has('brand') ? Q({ group_by: 'brand', metric }) : null,
        tab === 'brand' && has('brand') ? api('/analytics/series', { filters: f, split_by: 'brand', x: 'week', metric }) : null,
        tab === 'sales' && has('salesman') ? Q({ group_by: 'salesman', metric }) : null,
      ])
      let drv = {}
      if (tab === 'sum' && per && additive && drillDim !== 'outlet_id' && main.rows.length <= 10) {
        const r = await Promise.all(main.rows.map((x) => api('/analytics/drivers', { group_dim: drillDim, key: x.key, a: per[0], b: per[1], filters: fNoM, top: 1 })))
        main.rows.forEach((x, i) => (drv[x.key] = r[i][0]))
      }
      if (my !== seq) return
      D = { loading: false, main, kInv, kDisc, outl: outl.items, piv, brand, series, sales, drv, names: Object.fromEntries(outl.items.map((o) => [o.outlet_id, o.name])) }
    } catch (e) { if (my === seq) { D = { loading: false, error: true }; await guard(async () => { throw e }) } }
  }
  const key = $derived(JSON.stringify([st.filters, tab, metric, pg, !!st.options, per, drillDim]))
  $effect(() => { key; if (untrack(() => st.options)) untrack(load) })
  $effect(() => { JSON.stringify(st.filters); if (st.options) refreshInsights() })

  // ---------- headline sentences ("cerita dulu, chart kemudian") ----------
  // names of regions, branches, brands, outlets and salesmen that appear in text get a marker so the eye can scan them
  const esc = (x) => String(x).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
  const ents = $derived.by(() => {
    const m = new Map()
    for (const d of ['region', 'branch', 'brand', 'salesman']) for (const v of opts[d] ?? []) { m.set(String(nm(v)), d); m.set(String(v), d) }
    for (const o of D.outl ?? []) m.set(o.name, 'outlet')
    return [...m.entries()].filter(([k]) => k && k.length > 2).sort((a, b) => b[0].length - a[0].length)
  })
  const hl = (text) => {
    let out = esc(text ?? ''); if (!ents.length) return out
    const rx = new RegExp(ents.map(([k]) => esc(k).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'g'), kind = new Map(ents.map(([k, d]) => [esc(k), d]))
    return out.replace(rx, (m) => `<mark class="ent ${kind.get(m) ?? ''} ${hiByName[m] ?? ''}" title="${DIMN[kind.get(m) === 'outlet' ? 'outlet_id' : kind.get(m)] ?? ''}">${m}</mark>`)
  }
  // active filters and the metric are worked into the sentence itself ("Untuk Region Jawa Tengah, diukur dengan Qty karton, …")
  const blend = (h) => {
    if (!h) return h
    const parts = Object.entries(st.filters).map(([d, vs]) => `${DIMN[d] ?? d} ${vs.map((v) => label(d, v)).join(', ')}`)
    const f = parts.length ? L(`Untuk ${parts.join(' dan ')}`, `For ${parts.join(' and ')}`) : ''
    const m = metric !== 'net' ? L(`diukur dengan ${t('m_' + metric)}`, `measured by ${t('m_' + metric)}`) : ''
    const lead = [f, m].filter(Boolean).join(', ')
    if (!lead) return h
    return `${lead}, ${/^(Dari|From) /.test(h) ? h[0].toLowerCase() + h.slice(1) : '— ' + h}`
  }
  const headline = $derived.by(() => {
    if (D.loading || D.error) return ''
    const m = D.main, tot = m.total
    if (tab === 'sum') {
      if (!per) { const r = m.rows[0]; return r ? `${DIMN[drillDim]} terbesar: ${nm(r.key)} (${mfmt(r.value)}, ${pct((r.value / m.total) * 100)} dari total).` : '' }
      const up = [...m.rows].sort((a, b) => b.delta - a.delta)[0], dn = [...m.rows].sort((a, b) => a.delta - b.delta)[0]
      return `Dari ${monthLabel(per[0])} ke ${monthLabel(per[1])}, total ${tot.delta >= 0 ? 'naik' : 'turun'} ${pct(tot.pct)} (${tot.delta >= 0 ? '+' : ''}${mfmt(tot.delta)}). ${dn && dn.delta < 0 ? `Penurunan terbesar: ${nm(dn.key)} (${mfmt(dn.delta)}). ` : ''}${up && up.delta > 0 ? `Kenaikan terbesar: ${nm(up.key)} (+${mfmt(up.delta)}).` : ''}`
    }
    if (tab === 'brand' && D.brand) {
      const r = D.brand.rows; if (!r.length) return ''
      if (!per) return `Brand terbesar: ${r[0].key} (${mfmt(r[0].value)}).`
      const g = [...r].sort((a, b) => (b.pct ?? -1e9) - (a.pct ?? -1e9)), up = g[0], dn = g.at(-1)
      return `${up.pct > 0 ? `${up.key} tumbuh paling cepat (${pctSigned(up.pct)})` : 'Tidak ada brand yang tumbuh'}${dn.pct < 0 ? `; ${dn.key} turun paling dalam (${pctSigned(dn.pct)})` : ''}.`
    }
    if (tab === 'outlet') {
      const w = D.outl.slice(0, 5); if (!w.length) return ''
      return `5 outlet terlemah dibanding sesama tipenya: ${w.map((x) => x.name).join(', ')}. Skor memakai nilai, tren, frekuensi, dan recency, bukan sekadar total terkecil.`
    }
    if (tab === 'sales' && D.sales) {
      const r = D.sales.rows, tt = r.reduce((s, x) => s + cur(x), 0), top = r[0]
      const dn = per ? [...r].sort((a, b) => (a.pct ?? 0) - (b.pct ?? 0))[0] : null
      return top ? `${top.key} berkontribusi paling besar (${pct((cur(top) / tt) * 100)} dari total)${dn && dn.pct < 0 ? `; paling turun: ${dn.key} (${pctSigned(dn.pct)})` : ''}.` : ''
    }
    return ''
  })

  // ---------- chart data ----------
  const wfRows = $derived.by(() => {
    if (!per || !D.main) return []
    const out = [{ kind: 'total', label: monthLabel(per[0]), value: D.main.total.a }]
    for (const r of D.main.rows) {
      const d = D.drv?.[r.key]
      out.push({ kind: 'delta', key: r.key, label: nm(r.key), delta: r.delta, pct: r.pct, note: d && d.share != null && Math.abs(d.share) >= 0.5 ? `Penggerak: ${d.name} (${d.delta >= 0 ? '+' : ''}${rpShort(d.delta)}${d.exceeds_total ? ', melebihi total perubahan' : ''})` : undefined })
    }
    out.push({ kind: 'total', label: monthLabel(per[1]), value: D.main.total.b }); return out
  })
  const barRows = (res) => res.rows.slice(0, 12).map((r) => ({ key: r.key, label: nm(r.key), value: cur(r), badge: per && r.pct != null ? pctSigned(r.pct) : undefined, hi: per ? tone(r.pct) : '', note: per ? `${mfmt(r.a)} → ${mfmt(r.b)}` : undefined }))
  // a score always means "against all outlets of its type", whatever the filters: the numbers shown anywhere come from the whole-company list
  const gOf = (o) => G?.find((x) => x.outlet_id === o.outlet_id) ?? o
  const scatter = $derived((D.outl ?? []).map((o, i) => ({ id: o.outlet_id, name: o.name, x: o.invoices, y: o.total, weak: i < 5, rank: i + 1, tip: [o.name, `${o.type} · ${o.branch}`, `Total ${rp(o.total)}`, `${o.invoices} invoice · skor ${gOf(o).score.toFixed(0)}`] })))
  const selOutlet = $derived((() => { const o = D.outl?.find((x) => x.outlet_id === sel); return o && gOf(o) })())
  const pivRows = $derived.by(() => {
    if (!D.piv) return []
    const r = D.piv.rows.map((x) => ({ key: x.key, a: per ? x.a : null, b: cur(x), delta: per ? x.delta : null, pct: per ? x.pct : null }))
    return r.sort((x, y) => ((x[sortKey] ?? -1e18) - (y[sortKey] ?? -1e18)) * sortDir)
  })
  // the biggest riser (green) and biggest faller (light red) in the current table: highlighted in the cards, the table and the text
  // the real arithmetic behind each weak outlet's score: data → mark 0-100 → share → contribution
  const COMP = [['value', 'Uang masuk', 'Money in', 0.35, (o) => rpShort(o.total)],
    ['trend', 'Naik atau turun', 'Up or down', 0.30, (o) => (o.trend == null ? L('belum ada bulan lalu', 'no earlier month') : pctSigned(o.trend * 100))],
    ['frequency', 'Frekuensi pemesanan', 'Order frequency', 0.20, (o) => `${o.invoices} ${L('nota', 'receipts')}`],
    ['recency', 'Terakhir memesan', 'Last order', 0.15, (o) => L(`${o.days_since} hari lalu`, `${o.days_since} days ago`)]]
  const calc = (o) => COMP.map(([k, id, en, w, f]) => { const mark = Math.round((o.components?.[k] ?? 0) * 100); return { k, label: L(id, en), data: f(o), mark, w, part: (o.components?.[k] ?? 0) * w * 100 } })
  // the popover on "skor": the real arithmetic of THIS outlet's score
  const attr = (x) => String(x).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]).replace(/\n/g, '&#10;')
  const scoreTip = (o) => {
    const c = calc(o), lo = c.reduce((a, b) => ((100 - b.mark) * b.w > (100 - a.mark) * a.w ? b : a))   // the part that costs the most points
    const lines = c.map((x) => `${x.label}: ${x.data} → ${L('nilai', 'mark')} ${x.mark} × ${Math.round(x.w * 100)}% = ${x.part.toFixed(1)}`)
    return { title: L(`Kenapa skor ${o.name} = ${o.score.toFixed(1)}`, `Why ${o.name}'s score = ${o.score.toFixed(1)}`),
      tip: [...lines, `${L('Jumlah', 'Total')}: ${c.map((x) => x.part.toFixed(1)).join(' + ')} = ${o.score.toFixed(1)}`, '',
        L(`Nilai 0–100 adalah peringkat di antara toko ${o.type} (makin kecil makin lemah). Yang paling menarik skor ke bawah: ${lo.label} (nilai ${lo.mark}).`, `A mark from 0 to 100 is the rank among ${o.type} shops (lower = weaker). What pulls the score down most: ${lo.label} (mark ${lo.mark}).`)].join('\n') }
  }
  const scoreSpan = (o, word = 'skor') => { const x = scoreTip(o); return `<span class="term" tabindex="0" data-title="${attr(x.title)}" data-tip="${attr(x.tip)}">${word}</span>` }
  // one outlet in focus (clicked, or filtered down to exactly one): explain its score from the whole-company comparison
  let G = $state(null)
  $effect(() => { if (st.options && !G) api('/analytics/outlets', { filters: {} }).then((r) => (G = r.items)).catch(() => {}) })
  const oneId = $derived(sel ?? (st.filters.outlet_id?.length === 1 ? st.filters.outlet_id[0] : null))
  const one = $derived.by(() => {
    const o = oneId && G?.find((x) => x.outlet_id === oneId); if (!o) return null
    const peers = G.filter((x) => x.type === o.type), rank = peers.findIndex((x) => x.outlet_id === oneId) + 1, c = calc(o)
    const hi = c.reduce((a, b) => (b.mark > a.mark ? b : a)), lo = c.reduce((a, b) => (b.mark < a.mark ? b : a))
    const tone = o.score < 35 ? 'bad' : o.score >= 65 ? 'good' : 'mid'
    const verdict = { bad: L('lemah', 'weak'), mid: L('sedang', 'average'), good: L('baik', 'good') }[tone]
    const text = L(`${o.name} (${o.branch}) mendapat §S§ ${o.score.toFixed(0)} dari 100, jadi tergolong ${verdict}. Peringkat ${rank} dari ${peers.length} outlet ${o.type} (1 = terlemah). Paling kuat di "${hi.label}" (nilai ${hi.mark}); paling lemah di "${lo.label}" (nilai ${lo.mark}). ${o.reasons.map((r) => r.text).join('; ')}.`,
      `${o.name} (${o.branch}) §S§ ${o.score.toFixed(0)} out of 100, so it counts as ${verdict}. Rank ${rank} of ${peers.length} ${o.type} outlets (1 = weakest). Strongest on "${hi.label}" (mark ${hi.mark}); weakest on "${lo.label}" (mark ${lo.mark}). ${o.reasons.map((r) => r.text).join('; ')}.`)
    return { o, tone, text }
  })
  // picking an outlet (list or chart) brings its row in the right-hand table into view
  $effect(() => {
    const id = sel; if (!id) return
    untrack(async () => {
      if (!st.detShown) st.detReq++
      await tick(); await new Promise((r) => setTimeout(r, 120))
      document.querySelector(`.piv tr[data-key="${CSS.escape(id)}"]`)?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    })
  })
  let hov = $state(null)   // outlet id under the pointer in the weakest list: dims the other red markers
  const hiMap = $derived.by(() => {
    const m = {}, r = pivRows.filter((x) => x.pct != null)
    if (!r.length) return m
    const top = r.reduce((a, b) => (b.pct > a.pct ? b : a)), low = r.reduce((a, b) => (b.pct < a.pct ? b : a))
    if (top.pct > 0) m[top.key] = 'pos'; if (low.pct < 0) m[low.key] = 'neg'
    return m
  })
  const hiByName = $derived(Object.fromEntries(Object.entries(hiMap).map(([k, v]) => [String(nm(k)), v])))
  const sort = (k) => { if (sortKey === k) sortDir *= -1; else { sortKey = k; sortDir = -1 } }
  async function copy() {
    const head = [DIMN[pg], per ? monthLabel(per[0]) : '', per ? monthLabel(per[1]) : t('m_net'), 'Δ', 'Δ%'].join('\t')
    const body = pivRows.map((r) => [nm(r.key), r.a ?? '', Math.round(r.b), r.delta == null ? '' : Math.round(r.delta), r.pct == null ? '' : r.pct.toFixed(1)].join('\t'))
    await navigator.clipboard?.writeText([head, ...body].join('\n')); copied = true; setTimeout(() => (copied = false), 1500)
  }

  // ---------- filters, drill-down, views ----------
  const crumbs = $derived(DRILL.filter((d) => st.filters[d]).map((d) => ({ d, label: st.filters[d].map(nm).join(', ') })))
  const label = (d, v) => (d === 'month' ? monthLabel(v) : nm(v))
  const rm = (d) => { const f = { ...st.filters }; delete f[d]; setFilters(f) }
  function crumbTo(i) { const f = { ...st.filters }; DRILL.slice(i).forEach((d) => delete f[d]); setFilters(f) }
  function drill(key) { const d = pg; if (DRILL.includes(d) && d !== 'invoice') setFilters({ ...st.filters, [d]: [key] }); else if (['brand', 'salesman', 'outlet_type', 'sku'].includes(d)) setFilters({ ...st.filters, [d]: [key] }) }
  function addFilter() { if (addDim && addVals.length) { setFilters({ ...st.filters, [addDim]: [...addVals] }); addDim = ''; addVals = [] } }
  const toggleVal = (v) => { addVals = addVals.includes(v) ? addVals.filter((x) => x !== v) : [...addVals, v] }
  function saveView() { const n = viewName.trim(); if (!n) return; st.views = [...st.views.filter((v) => v.name !== n), { name: n, filters: $state.snapshot(st.filters) }]; saveViews(); viewName = '' }
  const TABS = $derived([['sum', 'tb_sum'], ...(has('brand') ? [['brand', 'tb_brand']] : []), ['outlet', 'tb_outlet'], ...(has('salesman') ? [['sales', 'tb_sales']] : [])])
  let prevTab = tab
  $effect(() => { const x = st.tab; untrack(() => { if (tab !== x) tab = x }) })
  const TABSAY = {
    sum: () => L('Ringkasan: batang hijau naik, merah turun dibanding bulan lalu. Klik satu batang untuk menelusuri ke cabang lalu outlet.', 'Summary: green bars rose, red fell versus last month. Click a bar to drill into branches, then outlets.'),
    brand: () => L('Brand: tiap brand punya garis tren mingguan sendiri. Lihat mana yang tumbuh dan mana yang turun; klik namanya di tabel kanan untuk memfilter.', 'Brand: each brand has its own weekly trend line. See which grow and which fall; click one in the right-hand table to filter.'),
    outlet: () => L('Outlet: titik merah adalah 5 outlet terlemah dibanding sesama tipenya, bukan sekadar yang terkecil. Klik satu titik atau namanya untuk alasannya di kanan.', 'Outlet: red dots are the 5 weakest outlets against their own type, not just the smallest. Click a dot or a name for the reasons on the right.'),
    sales: () => L('Salesman: kontribusi tiap orang ke total. Cari yang turun paling dalam, lalu klik untuk memfilter.', 'Salesman: each person\'s share of the total. Find the steepest decline, then click to filter.'),
  }
  $effect(() => { const x = tab; untrack(() => { if (x !== prevTab) { prevTab = x; pgroup = null; sel = null; if (!seen[x]) { seen[x] = true; say(TABSAY[x]?.() ?? '') } else say(TABSAY[x]?.() ?? '') } }) })
</script>
<Page wide title={t('s_dashboard')} asideTitle={selOutlet ? selOutlet.name : t('db_aside')} asideSub={selOutlet ? selOutlet.outlet_id : (Object.keys(st.filters).length ? Object.values(st.filters).flat().map(nm).join(', ') : t('j_all'))}>


{#if D.loading && !D.main}<p class="mut">…</p>
{:else if D.error}<p class="err">▲ {t('db_empty')}</p>
{:else if D.main}
  <section class="kpis" aria-label="KPI" class:dim={D.loading}>
    {#each [[t('k_net'), D.main.total, rpShort, true], [t('k_inv'), D.kInv.total, num], [t('k_disc'), D.kDisc.total, (v) => pct(v * 100)], [t('k_outlets'), { b: D.outl.length, value: D.outl.length }, num]] as [lab, tot, f, big]}
      <div class="kpi card"><span class="kl">{@html glossHtml(lab)}</span><b class="kv num">{f(per ? (tot.b ?? 0) : (typeof tot === 'object' ? (tot.value ?? tot.b) : tot))}</b>
        {#if per && tot.pct != null && lab !== t('k_outlets')}<span class="kd {lab === t('k_disc') ? '' : tone(tot.pct, 5)}">{tot.pct >= 0 ? '▲' : '▼'} {pctSigned(tot.pct)} <small>{t('k_vs')}</small></span>{/if}</div>
    {/each}
  </section>

  <div class="tabs" role="tablist">{#each TABS as [id, k]}<button role="tab" aria-selected={tab === id} class:on={tab === id} class:hint={!seen[id]} onclick={() => (st.tab = id)}>{t(k)}</button>{/each}</div>
  {#if one}<blockquote class="quote headline one {one.tone}"><p>{@html glossify(hl(one.text)).replace('§S§', scoreSpan(one.o, L('skor', 'scores')))}</p>{@render calcGrid(one.o)}<cite>{L('Kenapa skornya begini', 'Why this score')}</cite></blockquote>
  {:else if headline}<blockquote class="quote headline"><p>{@html glossify(hl(blend(headline)))}</p><cite>{t('insight')}</cite></blockquote>{/if}

  {#if D.main.total === 0 || (!per && !D.main.rows.length) }<p class="mut">{t('db_empty')}</p>{/if}

  <div class="chart card" class:dim={D.loading}>
    {#if tab === 'sum'}
      {#if per && additive}<Waterfall rows={wfRows} onselect={drill} label="Perubahan per {DIMN[drillDim]}" />
      {:else if D.main.rows.length}<BarList rows={barRows(D.main)} onselect={drill} label={DIMN[drillDim]} fmt={mfmt} />{/if}
    {:else if tab === 'brand' && D.series}
      <div class="sm">
        {#each D.series.series as s (s.key)}
          {@const b = D.brand?.rows.find((r) => r.key === s.key)}
          <div class="smc {hiMap[s.key] ?? ''}"><div class="smh"><b class="ent brand">{s.key}</b>{#if per && b?.pct != null}<span class="kd {tone(b.pct)}">{b.pct >= 0 ? '▲' : '▼'} {pctSigned(b.pct)}</span>{/if}</div>
            <div class="sv2 num">{mfmt(per && b ? b.b : s.total)}</div><Spark values={s.values} labels={D.series.x} name={s.key} /></div>
        {/each}
      </div>
    {:else if tab === 'outlet'}
      <Scatter hl={hov} points={scatter} xLabel="Jumlah invoice" yLabel="Net sales" onselect={(id) => (sel = id)} />
      <ol class="weak">{#each D.outl.slice(0, 5).map(gOf) as o, i}<li onmouseenter={() => (hov = o.outlet_id)} onmouseleave={() => (hov = null)}><button class:on={sel === o.outlet_id} onfocus={() => (hov = o.outlet_id)} onblur={() => (hov = null)} onclick={() => (sel = o.outlet_id)}><span class="rkb">{i + 1}</span> <b class="ent outlet">{o.name}</b> <span class="mut">{@html hl(o.branch)} · {o.type}</span> <span class="neg">▼ {@html scoreSpan(o)} {o.score.toFixed(0)}</span></button>
          {@render calcGrid(o)}</li>{/each}</ol>
    {:else if tab === 'sales' && D.sales}
      <BarList rows={barRows(D.sales)} onselect={drill} label="Salesman" fmt={mfmt} />
    {/if}
  </div>

{/if}

{#snippet scopeLine()}
  {#if Object.keys(st.filters).length || metric !== 'net'}
    <p class="scope"><small>{L('Berlaku untuk', 'Applies to')}</small>{#each Object.entries(st.filters) as [d, vs]}<span class="sc">{DIMN[d] ?? d}: <b>{vs.map((v) => label(d, v)).join(', ')}</b></span>{/each}{#if metric !== 'net'}<span class="sc">{t('db_metric')}: <b>{t('m_' + metric)}</b></span>{/if}</p>
  {/if}
{/snippet}
{#snippet calcGrid(o)}
  <div class="calc" aria-label={L('Hitungan skor', 'Score calculation')}>{#each calc(o) as c}<span class="cc"><small>{c.label}</small><em>{c.data}</em><span class="num">{L('nilai', 'mark')} {c.mark} × {Math.round(c.w * 100)}% = <b>{c.part.toFixed(1)}</b></span></span>{/each}<span class="cc tot"><small>{L('Skor', 'Score')}</small><b class="num">{o.score.toFixed(1)}</b></span></div>
{/snippet}
{#snippet footer()}
  <span class="hn mut">{t('db_next_hint')}</span><span class="sp"></span>
  <button class="btn" onclick={() => router.go('/studio/actions')}>{t('db_next')}</button>
{/snippet}
{#snippet aside()}
<section class="fbar" aria-label="Filter">
  <nav class="crumbs" aria-label="Drill-down"><button onclick={() => crumbTo(0)} disabled={!crumbs.length}>{t('db_all')}</button>{#each crumbs as c, i}<span aria-hidden="true">›</span><button onclick={() => crumbTo(i + 1)} disabled={i === crumbs.length - 1}>{c.label}</button>{/each}</nav>
  <div class="chips">
    {#each Object.entries(st.filters) as [d, vs]}{#each vs as v}<span class="fc">{DIMN[d] ?? d}: {label(d, v)}</span>{/each}<button class="x" onclick={() => rm(d)} aria-label="Hapus filter {DIMN[d] ?? d}">✕ {DIMN[d] ?? d}</button>{/each}
    {#if Object.keys(st.filters).length}<button class="lk" onclick={() => setFilters({})}>{t('db_clear')}</button>{/if}
  </div>
  <div class="ctl">
    <select bind:value={addDim} aria-label={t('db_add')} onchange={() => (addVals = [])}><option value="">+ {t('db_add')}</option>{#each FILT.filter((d) => has(d)) as d}<option value={d}>{DIMN[d]}</option>{/each}</select>
    {#if addDim}<div class="vals" role="group" aria-label={t('db_value')}>{#each opts[addDim] as v}<button type="button" class="vopt" class:on={addVals.includes(v)} aria-pressed={addVals.includes(v)} onclick={() => toggleVal(v)}><span class="cbx" aria-hidden="true">{addVals.includes(v) ? '✓' : ''}</span><span class="vl">{label(addDim, v)}</span></button>{/each}<button class="btn" onclick={addFilter} disabled={!addVals.length}>{t('c_apply')}</button></div>{/if}
    <label class="mt">{t('db_metric')} <select bind:value={metric}>{#each METRICS as m}<option value={m}>{t('m_' + m)}</option>{/each}</select></label>
    {#if st.views.length}<select aria-label={t('db_views')} onchange={(e) => { const v = st.views.find((x) => x.name === e.currentTarget.value); if (v) setFilters(structuredClone(v.filters)); e.currentTarget.value = '' }}><option value="">{t('db_views')}</option>{#each st.views as v}<option>{v.name}</option>{/each}</select>{/if}
    <span class="sv"><input bind:value={viewName} placeholder={t('db_name')} aria-label={t('db_name')} onkeydown={(e) => e.key === 'Enter' && saveView()} /><button class="btn secondary" onclick={saveView} disabled={!viewName.trim()}>{t('db_save')}</button></span>
  </div>
</section>
{#if D.main}
{#if selOutlet}<div class="oc"><h3><span class="ent outlet">{selOutlet.name}</span> <small>{selOutlet.outlet_id} · {@html hl(selOutlet.region)} · {@html hl(selOutlet.branch)}</small></h3>
        {#each selOutlet.reasons as r}<blockquote class="quote bad"><p>{@html glossHtml(r.text)}</p></blockquote>{/each}
        <button class="btn secondary" onclick={() => ask(`kenapa ${selOutlet.outlet_id} turun?`)}>Tanya asisten</button> <button class="btn secondary" onclick={() => setFilters({ ...st.filters, outlet_id: [selOutlet.outlet_id] })}>Drill ke invoice</button></div>{/if}
  <section class="piv" class:dim={D.loading} aria-label="Tabel pivot">
    <header><h2>{t('db_table')}</h2>
      <label>{t('db_group')} <select value={pg} onchange={(e) => (pgroup = e.currentTarget.value === defGroup ? null : e.currentTarget.value)}>{#each ['region', 'branch', 'brand', 'sku', 'outlet_type', 'salesman', 'outlet_id', 'month', 'week'].filter((d) => has(d) || d === 'week' || d === 'month' || d === defGroup) as d}<option value={d}>{DIMN[d]}</option>{/each}</select></label>
      <button class="btn secondary" onclick={copy}>{copied ? '✓ ' + t('db_copied') : t('db_copy')}</button></header>
    <div class="tw"><table>
      <thead><tr><th>{DIMN[pg]}</th>{#if per}<th><button onclick={() => sort('a')}>{monthShort(per[0])}</button></th>{/if}<th><button onclick={() => sort('b')}>{per ? monthShort(per[1]) : t('m_net')}</button></th>{#if per}<th><button onclick={() => sort('delta')}>Δ</button></th><th><button onclick={() => sort('pct')}>Δ%</button></th>{/if}</tr></thead>
      <tbody>{#each pivRows.slice(0, Math.max(50, pivRows.findIndex((x) => x.key === sel) + 1)) as r (r.key)}<tr data-key={r.key} class:picked={sel === r.key} class={hiMap[r.key] ? 'hi ' + hiMap[r.key] : ''} class:click={DRILL.slice(0, 3).includes(pg) || ['brand', 'salesman', 'outlet_type', 'sku'].includes(pg)} onclick={() => drill(r.key)}>
        <td><span class="ent {pg} {hiMap[r.key] ?? ''}">{nm(r.key)}</span></td>{#if per}<td class="num">{mfmt(r.a)}</td>{/if}<td class="num">{mfmt(r.b)}</td>
        {#if per}<td class="num">{mfmt(r.delta)}</td><td class="num {tone(r.pct)}">{r.pct == null ? '–' : (r.pct >= 0 ? '▲ ' : '▼ ') + pctSigned(r.pct)}</td>{/if}</tr>{/each}</tbody>
    </table></div>
  </section>
{/if}
{/snippet}
</Page>
<style>
  h1{font-size:26px;margin:0 0 var(--s4)}
  .fbar{display:flex;flex-direction:column;gap:var(--s3)}
  .crumbs{display:flex;gap:6px;align-items:center;font-size:14px;flex-wrap:wrap}.crumbs button{background:none;border:0;font:inherit;cursor:pointer;padding:4px 2px;min-height:32px;color:var(--ink)}.crumbs button:disabled{color:var(--grey-600);cursor:default;font-weight:600}.crumbs button:not(:disabled):hover{text-decoration:underline}
  .chips{display:flex;gap:var(--s2);flex-wrap:wrap;align-items:center}.fc{background:var(--grey-100);border-radius:99px;padding:4px 12px;font-size:13px}
  .x{background:none;border:0;color:var(--grey-600);cursor:pointer;font:inherit;font-size:12px;min-height:32px}.x:hover{color:var(--ink)}.lk{background:none;border:0;text-decoration:underline;color:var(--grey-600);cursor:pointer;font:inherit;font-size:13px;min-height:32px}
  .ctl{display:flex;gap:var(--s3);flex-wrap:wrap;align-items:flex-start}.ctl select,.ctl input{min-height:40px;border:1px solid var(--grey-200);border-radius:6px;padding:0 10px;font:inherit;background:var(--paper)}.ctl select:focus,.ctl input:focus{border-color:var(--ink);outline:none}
  .mt{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--grey-600)}.sv{display:flex;gap:var(--s2);margin-left:auto}.sv .btn{padding:0 var(--s4)}.btn:disabled{opacity:.35;cursor:not-allowed}
  .vals{display:flex;flex-wrap:wrap;gap:var(--s2) var(--s4);align-items:center;padding:var(--s2) var(--s3);border:var(--border);border-radius:8px;max-width:520px;font-size:14px}.vals .btn{padding:0 var(--s4);min-height:36px}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:var(--s3);margin-bottom:var(--s5)}.kpi{padding:var(--s4);display:flex;flex-direction:column;gap:2px}.kl{font-size:13px;color:var(--grey-600)}.kv{font-size:24px;font-weight:600}
  .kd{font-size:13px;font-weight:500}.kd small{color:var(--grey-600);font-weight:400}.pos{color:var(--ok-green)}.neg{color:var(--alert-red)}.dim{opacity:.55;transition:opacity var(--t-base)}
  .tabs{display:flex;gap:var(--s2);margin-bottom:var(--s3);overflow-x:auto}.tabs button{background:var(--paper);border:1px solid var(--grey-200);border-radius:99px;padding:0 18px;min-height:40px;font:inherit;cursor:pointer}.tabs button.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}
  .headline{margin:var(--s3) 0 var(--s4)}.headline p{font-size:17px}.mut{color:var(--grey-600)}.err{color:var(--alert-red)}
  .chart{margin-bottom:var(--s6)}.sm{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:var(--s4)}.smc{border:var(--border);border-radius:8px;padding:var(--s3)}.smh{display:flex;justify-content:space-between;gap:6px;font-size:14px}.sv2{font-size:18px;font-weight:600;margin:2px 0 6px}
  .weak{list-style:none;padding:0;margin:var(--s4) 0 0;display:flex;flex-direction:column;gap:2px}.weak button{background:none;border:0;font:inherit;cursor:pointer;padding:8px;border-radius:6px;text-align:left;min-height:40px;width:100%}.weak button:hover,.weak .on{background:var(--grey-100)}
  .rkb{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--alert-red);color:#fff;font-size:11px;font-weight:700;margin-right:4px}
  .oc{border-bottom:var(--border);margin-bottom:var(--s4);padding-bottom:var(--s3)}.oc h3{margin:0 0 var(--s2);font-size:16px}.oc small{color:var(--grey-600);font-weight:400}.oc ul{margin:0 0 var(--s3);padding-left:20px;font-size:14px}.oc .btn{padding:0 var(--s4);min-height:40px;margin-right:var(--s2)}
  .piv header{display:flex;gap:var(--s4);align-items:center;margin-bottom:var(--s3);flex-wrap:wrap}.piv h2{margin:0;font-size:16px;flex:1}.piv select{min-height:36px;border:1px solid var(--grey-200);border-radius:6px;padding:0 8px;font:inherit}.piv .btn{padding:0 var(--s4);min-height:36px}
  .tw{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:right;font-weight:500;color:var(--grey-600);padding:4px 8px}th:first-child{text-align:left}th button{background:none;border:0;font:inherit;color:inherit;cursor:pointer;min-height:32px}th button:hover{color:var(--ink)}
  td{padding:8px;border-top:var(--border)}td.num{text-align:right}tr.click{cursor:pointer}tr.click:hover{background:var(--grey-50)}
  @media (max-width:700px){.sv{margin-left:0}}
  @media (max-width:1280px){.kpi{padding:var(--s3)}.kv{font-size:20px}}
  .tabs button.hint:not(.on){border-color:var(--alert-red);color:var(--alert-red);animation:ring 2s ease-in-out infinite}@keyframes ring{0%,100%{box-shadow:0 0 0 0 rgba(212,24,61,.35)}50%{box-shadow:0 0 0 5px rgba(212,24,61,0)}}@media (prefers-reduced-motion:reduce){.tabs button.hint{animation:none}}
  .fbar{margin-bottom:var(--s4);padding-bottom:var(--s4);border-bottom:var(--border)}
  /* scan markers: an entity name = bold with a soft highlight (colour stays reserved for good/bad) */
  :global(.ent){font-weight:600;color:var(--ink);background:var(--grey-100);border-radius:4px;padding:1px 6px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
  :global(.ent.outlet),:global(.ent.outlet_id){border-radius:0;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px;text-decoration-skip-ink:none}
  :global(mark.ent){background:var(--grey-100);color:var(--ink)}
  .tabs{margin-top:var(--s2);margin-bottom:var(--s4)}.headline{margin:0 0 var(--s5)}.chart{padding:var(--s5)}
  .kpis{margin-bottom:var(--s5)}
  .fbar{padding-bottom:var(--s4);border-bottom:var(--border);margin-bottom:var(--s4)}.piv{margin-top:var(--s2)}
  :global(.ent.pos){background:var(--ok-green-bg)}:global(.ent.neg){background:var(--alert-red-bg)}
  .smc.pos{background:var(--ok-green-bg);border-color:var(--ok-green)}.smc.neg{background:var(--alert-red-bg);border-color:var(--alert-red)}
  tr.hi.pos td{background:var(--ok-green-bg)}tr.hi.neg td{background:var(--alert-red-bg)}
  /* the finding: a light grey box with a black border, generous padding */
  .quote.headline{display:flow-root;background:var(--grey-100);color:var(--ink);border:1.5px solid var(--ink);border-radius:12px;padding:var(--s5) var(--s6);margin:0 0 var(--s6);max-width:none}
  .quote.headline p{font-size:19px;line-height:1.6;margin:0;color:var(--ink)}.quote.headline cite{display:block;margin-top:var(--s3);font:600 12px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600);font-style:normal}
  .quote.headline :global(.ent){background:var(--paper)}.quote.headline :global(.ent.pos){background:var(--ok-green-bg)}.quote.headline :global(.ent.neg){background:var(--alert-red-bg)}
  .chart.card{padding:var(--s6);margin-top:var(--s2);margin-bottom:var(--s6)}
  /* dropdowns in the right column: a roomy chevron on the far right */
  .fbar select,.piv select{appearance:none;-webkit-appearance:none;padding:0 38px 0 var(--s3);min-width:150px;background:var(--paper) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23111' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") no-repeat right 14px center}
  .fbar .mt{display:flex;align-items:center;gap:var(--s2)}.fbar .mt select{flex:1}
  .calc{display:flex;flex-wrap:wrap;gap:var(--s2);margin:2px 0 var(--s3) 38px}.cc{display:flex;flex-direction:column;gap:1px;padding:6px 10px;border:1px solid var(--grey-200);border-radius:8px;background:var(--paper);font-size:12.5px;min-width:130px}.cc small{font:600 11px var(--font);letter-spacing:.04em;text-transform:uppercase;color:var(--grey-600)}.cc em{font-style:normal;color:var(--ink)}.cc.tot{background:var(--ink);color:#fff;border-color:var(--ink);min-width:70px;justify-content:center}.cc.tot small{color:var(--grey-400)}.cc.tot b{font-size:18px}
  .quote.headline.one.bad{border-color:var(--alert-red)}.quote.headline.one.good{border-color:var(--ok-green)}.quote.headline.one .calc{margin:var(--s4) 0 0}
  tr.picked td{background:var(--grey-100);box-shadow:inset 0 1px 0 var(--ink),inset 0 -1px 0 var(--ink)}tr.picked td:first-child{box-shadow:inset 3px 0 0 var(--ink),inset 0 1px 0 var(--ink),inset 0 -1px 0 var(--ink)}tr.picked.hi.pos td{background:var(--ok-green-bg)}tr.picked.hi.neg td{background:var(--alert-red-bg)}
.scope{display:flex;flex-wrap:wrap;gap:var(--s2);align-items:center;margin:var(--s3) 0 0!important;font-size:13.5px!important;font-style:normal}.scope small{font:600 11px var(--font);letter-spacing:.06em;text-transform:uppercase;color:var(--grey-600);margin-right:var(--s1)}.scope .sc{background:var(--paper);border:1px solid var(--grey-400);border-radius:99px;padding:2px 12px;font-family:var(--font)}
.vals{display:grid!important;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:var(--s2);padding:var(--s3);background:var(--paper);border:var(--border);border-radius:10px}
  .vopt{display:flex;align-items:center;gap:var(--s2);min-height:44px;padding:0 var(--s3);background:var(--paper);border:1.5px solid var(--grey-200);border-radius:10px;font:inherit;font-size:14px;color:var(--ink);cursor:pointer;text-align:left}
  .vopt:hover{border-color:var(--grey-400)}.vopt:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
  .vopt .cbx{flex:none;display:grid;place-items:center;width:20px;height:20px;border:1.5px solid var(--grey-400);border-radius:5px;font-size:13px;font-weight:700;color:#fff;line-height:1}
  .vopt.on{border-color:var(--ink);background:var(--grey-100);font-weight:600}.vopt.on .cbx{background:var(--ink);border-color:var(--ink)}
  .vals>.btn{grid-column:1/-1;justify-self:start}
</style>
