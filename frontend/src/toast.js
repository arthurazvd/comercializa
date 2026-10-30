/** Notificação única, cancelável e com duração reiniciável. */
export function createToastController(onChange, duration = 2000, scheduler = { setTimeout, clearTimeout }) {
  let timer = null
  function dismiss() {
    if (timer !== null) scheduler.clearTimeout(timer)
    timer = null
    onChange(null)
  }
  function show(text, type = 'success') {
    if (timer !== null) scheduler.clearTimeout(timer)
    onChange({ text, type })
    timer = scheduler.setTimeout(() => { timer = null; onChange(null) }, duration)
  }
  return { show, dismiss, dispose: dismiss }
}
