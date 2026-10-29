/** Preferências da interface sem falhar em navegadores que bloqueiam storage. */
export function readTheme(storageProvider = () => globalThis.localStorage) {
  try { return storageProvider()?.getItem('comercializa-theme') === 'dark' ? 'dark' : 'light' }
  catch { return 'light' }
}

export function saveTheme(theme, storageProvider = () => globalThis.localStorage) {
  if (!['dark', 'light'].includes(theme)) return false
  try { storageProvider()?.setItem('comercializa-theme', theme); return true }
  catch { return false }
}
