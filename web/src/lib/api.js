export async function api(path, body, method) {
  const opt = body === undefined ? { method: method || 'GET' }
    : { method: method || 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }
  const r = await fetch('/api' + path, opt)
  if (!r.ok) { const e = new Error('api ' + r.status); e.status = r.status; try { e.detail = (await r.json()).detail } catch {} ; throw e }
  return r.json()
}
export async function upload(file, sheet) {
  const fd = new FormData(); fd.append('file', file)
  const r = await fetch('/api/data/upload' + (sheet ? '?sheet=' + encodeURIComponent(sheet) : ''), { method: 'POST', body: fd })
  const j = await r.json().catch(() => ({}))
  if (!r.ok) { const e = new Error('upload'); e.status = r.status; e.detail = j.detail; throw e }
  return j
}
