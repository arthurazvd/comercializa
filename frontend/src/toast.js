/** Notificação única, cancelável e com duração reiniciável. */
export function createToastController(onChange, duration = 1500, scheduler = { setTimeout, clearTimeout }) {
  let timer = null
  let sequence = 0
  function dismiss() {
    if (timer !== null) scheduler.clearTimeout(timer)
    timer = null
    onChange(null)
  }
  function show(text, type = 'success') {
    if (timer !== null) scheduler.clearTimeout(timer)
    const id = ++sequence
    onChange({ text, type, id })
    timer = scheduler.setTimeout(() => { if (sequence === id) dismiss() }, duration)
  }
  return { show, dismiss, dispose: dismiss }
}
