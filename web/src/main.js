import './tokens.css'
import { mount } from 'svelte'
import { initTips } from './lib/glossary.js'

// Browser storage belongs to the address (127.0.0.1:8765), not to one install. If this server is a different install than the
// last one this browser saw (a fresh download in another folder), start from a clean slate so it begins at /setup.
async function boot() {
  try {
    const id = (await (await fetch('/api/health')).json()).install_id
    if (id && localStorage.getItem('installId') !== id) {
      for (const k of ['setupDone', 'views', 'reached', 'rbHint', 'ui']) localStorage.removeItem(k)
      localStorage.setItem('installId', id)
    }
  } catch { /* server not reachable: carry on with whatever is stored */ }
  const { default: App } = await import('./App.svelte')
  initTips()
  mount(App, { target: document.getElementById('app') })
}
boot()
