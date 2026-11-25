// Plain-language definitions for terms used in the app. A term is underlined (dotted); hovering or focusing it shows the definition.
import { L } from './i18n.svelte.js'

const G = [
  { rx: 'terlemah|weakest',
    id: ['Outlet terlemah', 'Outlet (toko pelanggan) yang paling perlu perhatian.\nBukan sekadar yang jualannya paling sedikit, karena toko kecil memang jualannya kecil. Jadi setiap toko dibandingkan dengan toko lain yang sejenis (toko besar dengan toko besar, warung dengan warung), lalu diberi "skor". Skor paling rendah = paling lemah.'],
    en: ['Weakest outlet', 'The outlet (customer shop) that needs attention the most.\nNot simply the one that sells the least, because small shops always sell little. Every shop is compared with similar shops (big with big, small stall with small stall) and given a "score". The lowest score = the weakest.'] },
  { rx: 'skor|score',
    id: ['Skor (0 sampai 100)', 'Nilai untuk satu toko. Makin kecil, makin lemah. Cara menghitungnya:\n1. Kumpulkan toko yang sejenis.\n2. Beri tiap toko 4 nilai, masing-masing 0 sampai 100 (100 = terbaik di antara temannya, 0 = terburuk): uang yang masuk, naik atau turunnya dibanding bulan lalu, frekuensi pemesanan, dan kapan terakhir memesan.\n3. Campur dengan porsi: uang masuk 35%, naik-turun 30%, frekuensi pemesanan 20%, terakhir memesan 15%.\nHitungan sebenarnya tiap toko (datanya, nilainya, dan hasil akhirnya) tampil langsung di bawah namanya di daftar outlet terlemah.'],
    en: ['Score (0 to 100)', 'A number for one shop. The lower, the weaker. How it is worked out:\n1. Gather shops of the same kind.\n2. Give each shop 4 marks, each 0 to 100 (100 = best among its peers, 0 = worst): money coming in, going up or down compared with last month, how often it orders, and when it last ordered.\n3. Blend them by share: money 35%, up/down 30%, order frequency 20%, last order 15%.\nThe real working for each shop (its data, its marks and the final result) is shown right under its name in the weakest-outlets list.'] },
  { rx: 'persentil|percentile',
    id: ['Peringkat 0 sampai 100', 'Cara memberi nilai lewat peringkat di antara teman sejenis. Kalau sebuah toko lebih baik dari 8 dari 10 toko sejenis, nilainya 80. Yang paling buruk 0, yang paling baik 100.'],
    en: ['Rank from 0 to 100', 'A way of marking by ranking among similar shops. If a shop beats 8 out of 10 similar shops, its mark is 80. The worst gets 0, the best gets 100.'] },
  { rx: 'tren|trend',
    id: ['Naik atau turun', 'Penjualan toko bulan terakhir dibanding bulan sebelumnya, lalu diperingkat di antara toko sejenis. Kalau belum ada bulan sebelumnya, dianggap biasa saja.'],
    en: ['Up or down', 'The shop\'s sales in the latest month compared with the month before, then ranked among similar shops. If there is no earlier month, it counts as neutral.'] },
  { rx: 'recency',
    id: ['Terakhir memesan', 'Sudah berapa hari sejak toko itu terakhir memesan. Makin lama tidak memesan, makin lemah nilainya.'],
    en: ['Last order', 'How many days since the shop last bought something. The longer it has not bought, the weaker the mark.'] },
  { rx: 'frekuensi|frequency',
    id: ['Frekuensi pemesanan', 'Berapa kali toko itu memesan, dihitung dari jumlah nota belanjanya.'],
    en: ['Order frequency', 'How many times the shop placed an order, counted from its number of receipts.'] },
  { rx: 'net sales',
    id: ['Net sales (penjualan bersih)', 'Uang penjualan yang benar-benar masuk: harga jual dikurangi potongan harga, dan barang yang dikembalikan pelanggan sudah dikurangkan.\n"jt" artinya juta rupiah. 878 jt = Rp 878.000.000.'],
    en: ['Net sales', 'The sales money that really came in: selling price minus price cuts, with returned goods already taken off.\n"jt" means million rupiah. 878 jt = Rp 878,000,000.'] },
  { rx: 'rasio diskon|discount ratio',
    id: ['Rasio diskon', 'Berapa persen potongan harga yang diberikan dibanding harga normal. Contoh 2%: dari tiap Rp 100 harga normal, Rp 2 dipotong.'],
    en: ['Discount ratio', 'What percent of the normal price was cut off. Example 2%: from every Rp 100 of normal price, Rp 2 is cut.'] },
  { rx: 'outlet aktif|active outlets',
    id: ['Outlet aktif', 'Jumlah toko pelanggan yang membeli pada periode ini.'],
    en: ['Active outlets', 'The number of customer shops that bought something in this period.'] },
  { rx: 'invoice',
    id: ['Invoice (nota)', 'Jumlah nota belanja. Satu nota = satu kali pesanan. Nota yang tercatat dobel dihitung satu kali.'],
    en: ['Invoice (receipt)', 'The number of purchase receipts. One receipt = one order. A receipt recorded twice is counted once.'] },
  { rx: 'Δ%',
    id: ['Berapa persen naik atau turun', 'Rumus: (nilai Oktober − nilai September) ÷ nilai September × 100.\nContoh: dari 100 menjadi 110 = naik 10%. Dari 100 menjadi 80 = turun 20%.'],
    en: ['Percent up or down', 'Formula: (October value − September value) ÷ September value × 100.\nExample: from 100 to 110 = up 10%. From 100 to 80 = down 20%.'] },
  { rx: 'penggerak|driver',
    id: ['Penggerak', 'Yang paling besar pengaruhnya pada naik atau turunnya angka di baris itu.'],
    en: ['Driver', 'What had the biggest effect on that row going up or down.'] },
  { rx: 'retur|returns?',
    id: ['Retur', 'Barang yang dikembalikan pelanggan. Uangnya dikurangkan dari penjualan.'],
    en: ['Returns', 'Goods the customer sent back. Their money is taken off the sales.'] },
]
const pick = (g) => (L('id', 'en') === 'id' ? g.id : g.en)   // L() answers with the active language

/** Definition for a whole label (used on SVG chart text, where HTML spans are impossible). */
export function termOf(text) {
  const g = G.find((x) => new RegExp('(?<![\\p{L}\\d])(?:' + x.rx + ')(?![\\p{L}\\d])', 'iu').test(String(text ?? '')))
  if (!g) return null
  const [title, tip] = pick(g); return { title, tip }
}

/** Wrap known terms in already-escaped HTML. Text inside tags (attributes) is left alone. */
export function glossify(html) {
  const parts = String(html ?? '').split(/(<[^>]*>)/)
  const rx = new RegExp('(?<![\\p{L}\\d])(' + G.map((g) => g.rx).join('|') + ')(?![\\p{L}\\d])', 'giu')
  let inMark = 0
  return parts.map((p) => {
    if (p.startsWith('<')) { if (/^<span class="term"/.test(p)) inMark++; if (p === '</span>' && inMark) inMark--; return p }
    if (inMark) return p
    return p.replace(rx, (m) => {
      const g = G.find((x) => new RegExp('^(?:' + x.rx + ')$', 'iu').test(m)); if (!g) return m
      const [title, body] = pick(g)
      return `<span class="term" tabindex="0" data-title="${title.replace(/"/g, '&quot;')}" data-tip="${body.replace(/"/g, '&quot;')}">${m}</span>`
    })
  }).join('')
}
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }
export const glossHtml = (text) => glossify(String(text ?? '').replace(/[&<>"]/g, (c) => ESC[c]))

/** One floating tooltip for every .term (fixed position, so scrolling panels never clip it). */
export function initTips() {
  const tip = document.createElement('div'); tip.className = 'tipbox'; tip.setAttribute('role', 'tooltip'); document.body.appendChild(tip)
  const show = (el) => {
    tip.innerHTML = `<b></b><span></span>`; tip.firstChild.textContent = el.dataset.title; tip.lastChild.textContent = el.dataset.tip
    tip.style.display = 'block'
    const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight
    const left = Math.min(Math.max(8, r.left), innerWidth - w - 8), top = r.top - h - 8 > 8 ? r.top - h - 8 : r.bottom + 8
    tip.style.left = left + 'px'; tip.style.top = top + 'px'
  }
  const hide = () => (tip.style.display = 'none')
  document.addEventListener('mouseover', (e) => { const el = e.target.closest?.('.term'); if (el) show(el) })
  document.addEventListener('mouseout', (e) => { if (e.target.closest?.('.term')) hide() })
  document.addEventListener('focusin', (e) => { const el = e.target.closest?.('.term'); if (el) show(el) })
  document.addEventListener('focusout', hide)
  document.addEventListener('keydown', (e) => e.key === 'Escape' && hide())
}
