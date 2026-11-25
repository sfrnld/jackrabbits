let path = $state(location.pathname)
addEventListener('popstate', () => { path = location.pathname })
export const router = {
  get path() { return path },
  go(p, replace = false) { history[replace ? 'replaceState' : 'pushState']({}, '', p); path = p; window.scrollTo(0, 0) },
}
