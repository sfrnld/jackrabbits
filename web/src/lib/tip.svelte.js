export const tip = $state({ show: false, x: 0, y: 0, lines: [] })
export function showTip(e, lines) { tip.show = true; tip.x = e.clientX; tip.y = e.clientY; tip.lines = lines }
export function hideTip() { tip.show = false }
