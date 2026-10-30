// Endereços das variações vetoriais extraídas da arte-mestre Comercializa.
export const BRAND_ASSETS = Object.freeze({
  verticalOnDark: '/logo-comercializa-vertical.svg',
  horizontalOnDark: '/logo-comercializa-horizontal-dark.svg',
  horizontalOnLight: '/logo-comercializa-horizontal-light.svg',
  faviconOnLight: '/favicon-comercializa.svg',
  faviconOnDark: '/favicon-comercializa-dark.svg',
})

export function getCopyrightYear(now = new Date()) {
  return now.getFullYear()
}
