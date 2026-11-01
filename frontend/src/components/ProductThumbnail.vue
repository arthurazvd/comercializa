<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { api } from '../api'
import AppIcon from './AppIcon.vue'

const props = defineProps({ productId: { type: Number, default: null }, updatedAt: { default: null }, name: { type: String, default: 'Produto' }, size: { type: String, default: 'catalog' } })
const root = ref(null)
const url = ref('')
const visible = ref(false)
let observer = null
let requestSeq = 0
function clearImage() { if (url.value) URL.revokeObjectURL(url.value); url.value = '' }
async function load() {
  const seq = ++requestSeq
  clearImage()
  if (!visible.value || !props.productId || !props.updatedAt) return
  try {
    const response = await api.get(`products/${props.productId}/image/`, { responseType: 'blob' })
    if (seq !== requestSeq) return
    url.value = URL.createObjectURL(response.data)
  } catch { /* Sem foto/autorização: manter ícone de embalagem, sem popup. */ }
}
watch(() => [props.productId, props.updatedAt], load)
onMounted(() => {
  if (!('IntersectionObserver' in window)) { visible.value = true; void load(); return }
  observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) {
      visible.value = true
      observer?.disconnect()
      void load()
    }
  }, { rootMargin: '160px' })
  observer.observe(root.value)
})
onUnmounted(() => { observer?.disconnect(); ++requestSeq; clearImage() })
</script>
<template>
  <span ref="root" :class="['product-avatar', 'product-thumbnail', `product-thumbnail--${size}`]">
    <img v-if="url" :src="url" :alt="`Foto de ${name}`" loading="lazy" />
    <AppIcon v-else name="package" :size="size === 'editor' ? 38 : 17" />
  </span>
</template>
