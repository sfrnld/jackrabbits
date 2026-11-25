// Indonesian number formatting (mirrors app/fmt.py so UI and server messages agree)
const n = (x, nd = 1) => { const s = x.toFixed(nd).replace('.', ','); return s.endsWith(',0') ? s.slice(0, -2) : s }
export const rp = (x) => {
  const s = x < 0 ? '−' : '', a = Math.abs(x)
  const t = a >= 1e9 ? n(a / 1e9) + ' miliar' : a >= 1e6 ? n(a / 1e6) + ' juta' : a >= 1e3 ? n(a / 1e3, 0) + ' ribu' : a.toFixed(0)
  return s + 'Rp ' + t
}
export const rpShort = (x) => {
  const s = x < 0 ? '−' : '', a = Math.abs(x)
  return s + (a >= 1e9 ? n(a / 1e9) + ' M' : a >= 1e6 ? n(a / 1e6, a >= 1e7 ? 0 : 1) + ' jt' : a >= 1e3 ? n(a / 1e3, 0) + ' rb' : a.toFixed(0))
}
export const rpFull = (x) => (x < 0 ? '−' : '') + 'Rp ' + Math.abs(Math.round(x)).toLocaleString('id-ID')
export const num = (x) => Math.round(x).toLocaleString('id-ID')
export const pct = (x) => (x == null ? '–' : n(Math.abs(x)) + '%')
export const pctSigned = (x) => (x == null ? '–' : (x > 0 ? '+' : x < 0 ? '−' : '') + n(Math.abs(x)) + '%')
const MON = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
const SHORT = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
export const monthLabel = (ym) => { const [y, m] = ym.split('-'); return MON[+m - 1] + ' ' + y }
export const monthShort = (ym) => SHORT[+ym.slice(5, 7) - 1]
export const dimLabelFor = (d) => d
