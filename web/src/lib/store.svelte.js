import { api, upload } from './api.js'
import { router } from './router.svelte.js'
import { L } from './i18n.svelte.js'

export const st = $state({
  session: null, info: null, mapping: {}, confirmed: null, fs: null, options: null,
  filters: {}, solo: false, detShown: true, detReq: 0, about: false, analysing: false, analysedFor: '', stackFrom: 0, reached: JSON.parse(localStorage.getItem('reached') || '[]'), tab: 'sum', ui: JSON.parse(localStorage.getItem('ui') || '{"leftOff":false,"rightOff":false,"aw":null}'), history: [], messages: [], thinking: false, dq: false, palette: false,
  views: JSON.parse(localStorage.getItem('views') || '[]'), insightKey: '', said: {}, notice: '', act: null,
})
let mid = 0
const snap = (o) => JSON.parse(JSON.stringify(o))

export function say(text, extra = {}) { if (st.messages.length > 40) st.messages.splice(0, 20); st.messages.push({ id: ++mid, who: 'assistant', text, t: Date.now(), ...extra }) }
export function userSay(text) { st.messages.push({ id: ++mid, who: 'user', text }) }
export function sayOnce(key, text, extra) { if (!st.said[key]) { st.said[key] = true; say(text, extra) } }

export async function guard(fn) {
  try { return await fn() } catch (e) {
    if (e.status === 409) { st.session = { loaded: false, confirmed: false }; router.go('/studio/data', true); say(L('Data belum siap atau sesi hilang. Pilih data dulu ya.', 'The data is not ready or the session was lost. Please pick data first.')); return null }
    if (e.status === 422) { st.notice = typeof e.detail === 'string' ? e.detail : JSON.stringify(e.detail); return null }
    throw e
  }
}

export function setFilters(f, record = true) {
  if (record) st.history.push(snap(st.filters))
  st.filters = f
}
export function undo() { if (st.history.length) st.filters = st.history.pop() }

export async function ask(text) {
  if (!text.trim()) return
  userSay(text); st.thinking = true
  const r = await guard(() => api('/assistant', { text, filters: snap(st.filters) }))
  st.thinking = false
  if (!r) return
  if (JSON.stringify(r.filters) !== JSON.stringify(st.filters)) setFilters(r.filters)
  say(r.message, { chips: r.chips, intent: r.intent, result: r.result, resp: r })
  if (['weakest', 'top', 'compare', 'filter', 'why'].includes(r.intent) && !router.path.endsWith('/dashboard')) router.go('/studio/dashboard')
}

export async function loadSession() {
  st.session = await api('/session')
  if (st.session.confirmed) await Promise.all([loadOptions(), loadFindings()])
  return st.session
}
export async function loadOptions() { st.options = await guard(() => api('/analytics/options')) }
// After any cleaning decision the values people can filter by change (e.g. "Jabar" merged into "Jawa Barat"): reload them
// and drop filter values that no longer exist.
export async function syncOptions() {
  await loadOptions()
  const f = {}; let changed = false
  for (const [d, vs] of Object.entries(st.filters)) {
    const ok = st.options?.[d] ? vs.filter((v) => st.options[d].includes(v)) : vs
    if (ok.length !== vs.length) changed = true
    if (ok.length) f[d] = ok
  }
  if (changed) st.filters = f
}
export async function loadFindings() { st.fs = await guard(() => api('/findings')) }

export async function pickSample() {
  say(L('Memuat data contoh Dua Kelinci…', 'Loading the Dua Kelinci sample data…')); st.info = await api('/data/sample', {}); initMapping(); router.go('/studio/mapping')
}
let lastFile = null
export async function uploadFile(file, sheet) {
  lastFile = file; say(L(`Membaca ${file.name}…`, `Reading ${file.name}…`))
  try { st.info = await upload(file, sheet); st.notice = ''; initMapping(); router.go('/studio/mapping') }
  catch (e) { st.notice = (typeof e.detail === 'string' ? e.detail : 'Tidak bisa membaca file ini'); say(L(`Aku tidak bisa membaca file itu: ${st.notice}`, `I could not read that file: ${st.notice}`)); throw e }
}
export const reloadSheet = (sheet) => lastFile && uploadFile(lastFile, sheet)
function initMapping() {
  st.mapping = Object.fromEntries(Object.entries(st.info.mapping).map(([r, v]) => [r, v.column]))
  st.session = { loaded: true, confirmed: false }
  st.said = {}; st.filters = {}; st.history = []; st.fs = null; st.confirmed = null
}
export async function confirmMapping() {
  const m = Object.fromEntries(Object.entries(st.mapping).filter(([, c]) => c))
  const r = await guard(() => api('/data/mapping', { mapping: m }))
  if (!r) return
  say(L('Pemetaan dikonfirmasi. Sekarang aku memeriksa kualitas datanya…', 'Mapping confirmed. Now I am checking the data quality…')); st.confirmed = r; st.session = { ...st.session, confirmed: true }
  await Promise.all([loadOptions(), loadFindings()])
  router.go('/studio/clean')
}

const after = (fid) => { const f = st.fs?.findings.find((x) => x.id === fid); return f && { f, label: f.options.find((o) => o.id === f.decision?.option)?.label } }
export async function decide(fid, option, params) {
  st.fs = await guard(() => api('/findings/' + fid, { option, params }, 'PUT')) ?? st.fs     // PUT, like the server route
  await syncOptions()
  const r = after(fid); if (r?.f.decision) say(`${r.f.title}: ${r.label}. ${st.fs.pending.length ? L(`Sisa ${st.fs.pending.length} temuan.`, `${st.fs.pending.length} findings left.`) : L('Semua temuan sudah diputuskan, angkanya kini bersih.', 'Every finding is decided, so the numbers are now clean.')}`)
}
export async function undoDecision(fid) {
  const f = st.fs?.findings.find((x) => x.id === fid)
  st.fs = await guard(() => api('/findings/' + fid, undefined, 'DELETE')) ?? st.fs; await syncOptions(); if (f) say(L(`Keputusan "${f.title}" dibatalkan. Data kembali ke kondisi awal untuk temuan ini.`, `Decision "${f.title}" undone. The data is back to its original state for this finding.`))
}
export async function applyAll() {
  st.fs = await guard(() => api('/findings/apply-all', {})) ?? st.fs
  await syncOptions()
  if (st.fs && !st.fs.pending.length) say(L(`Semua rekomendasi diterapkan. Net bersih Rp ${st.fs.summary.after.net.toLocaleString('id-ID')} dari ${st.fs.summary.after.rows.toLocaleString('id-ID')} baris.`, `All recommendations applied. Clean net Rp ${st.fs.summary.after.net.toLocaleString('id-ID')} from ${st.fs.summary.after.rows.toLocaleString('id-ID')} rows.`))
}

export function saveUi() { localStorage.setItem('ui', JSON.stringify($state.snapshot(st.ui))) }
export function saveViews() { localStorage.setItem('views', JSON.stringify(st.views)) }

let tmr
export function refreshInsights() {
  clearTimeout(tmr)
  tmr = setTimeout(async () => {
    const r = await guard(() => api('/analytics/insights', { filters: snap(st.filters) }))
    if (!r || !r.insights.length) return
    const g = st.messages.at(-1); if (g?.guide && Date.now() - g.t < 12000) await new Promise((res) => setTimeout(res, 12000 - (Date.now() - g.t)))   // let a page guide be read first
    const key = r.insights.map((i) => i.text).join('|')
    if (key === st.insightKey) return
    st.insightKey = key; say(L('Temuan untuk tampilan ini:', 'What I see in this view:'), { insights: r.insights.map((i) => i.text), chips: null })
  }, 450)
}

// Fresh-start: wipe server + browser state. The Telegram token (.env) is deliberately untouched.
export async function resetAll() {
  await api('/reset', {})
  localStorage.removeItem('setupDone'); localStorage.removeItem('views'); localStorage.removeItem('reached'); localStorage.removeItem('rbHint')
  Object.assign(st, { session: null, info: null, mapping: {}, confirmed: null, fs: null, options: null, filters: {}, tab: 'sum', history: [], messages: [], thinking: false, dq: false, palette: false, views: [], insightKey: '', said: {}, notice: '', act: null, reached: [], analysing: false, analysedFor: '' })
  router.go('/setup')
}
