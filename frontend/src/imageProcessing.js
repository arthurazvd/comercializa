/** Converte foto da câmera ou galeria para JPEG padronizado, até 100 KiB.
 * A fotografia é centralizada em fundo branco sem deformar as proporções.
 * O limite de bytes é rigoroso: se não couber, o upload não será iniciado.
 */
export const PRODUCT_IMAGE_MAX_BYTES = 100 * 1024
export const PRODUCT_IMAGE_MAX_INPUT_BYTES = 20 * 1024 * 1024

export function productPhotoFilename(code) {
  const sanitized = String(code || 'produto').normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '').slice(0, 70) || 'produto'
  return `${sanitized}.jpg`
}
export function checkOriginalPhoto(file) {
  if (!file) throw new Error('Selecione uma imagem.')
  if (!file.type.startsWith('image/')) throw new Error('Selecione um arquivo de imagem.')
  if (file.size > PRODUCT_IMAGE_MAX_INPUT_BYTES) throw new Error('Imagem original muito grande (máximo de 20 MB).')
}
function jpegBlob(canvas, quality) {
  return new Promise((resolve, reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Não foi possível gerar JPEG.')), 'image/jpeg', quality))
}
function openPhoto(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => { URL.revokeObjectURL(url); resolve(image) }
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Imagem inválida ou incompatível.')) }
    image.src = url
  })
}
export async function normalizeProductPhoto(file, code) {
  checkOriginalPhoto(file)
  const image = await openPhoto(file)
  if (!image.naturalWidth || !image.naturalHeight) throw new Error('Imagem sem dimensões válidas.')
  // Reduzir o quadrado progressivamente é uma garantia adicional para fotos detalhadas.
  for (const side of [800, 720, 640, 560, 480, 400, 320, 256, 192, 128]) {
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = side
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Este navegador não suporta processamento de imagens.')
    context.fillStyle = '#fff'
    context.fillRect(0, 0, side, side)
    const scale = Math.min(side / image.naturalWidth, side / image.naturalHeight)
    const width = Math.max(1, Math.round(image.naturalWidth * scale))
    const height = Math.max(1, Math.round(image.naturalHeight * scale))
    context.drawImage(image, (side - width) / 2, (side - height) / 2, width, height)
    for (const quality of [.86, .76, .65, .53, .42, .30]) {
      const blob = await jpegBlob(canvas, quality)
      if (blob.size > 0 && blob.size <= PRODUCT_IMAGE_MAX_BYTES) {
        return new File([blob], productPhotoFilename(code), { type: 'image/jpeg' })
      }
    }
  }
  throw new Error('Não foi possível reduzir a foto para 100 KB.')
}
