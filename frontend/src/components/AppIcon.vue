<script setup>
import { computed } from 'vue'
const props = defineProps({ name: { type: String, required: true }, size: { type: [String, Number], default: 19 } })
const paths = {
  dashboard: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  package: 'm12 2 9 5-9 5-9-5 9-5z M3 7v10l9 5 9-5V7 M12 12v10',
  products: 'M4 7V4h16v3 M4 7h16v13H4z M4 11h16 M9 15h6',
  cart: 'M3 3h2l2.5 12h11L21 7H6 M9 21h.01 M18 21h.01',
  arrows: 'M4 7h16m0 0-4-4m4 4-4 4 M20 17H4m0 0 4-4m-4 4 4 4',
  chart: 'M4 20V11 M10 20V4 M16 20v-8 M22 20v-6 M2 20h22',
  alert: 'M12 3 2 21h20L12 3z M12 9v5 M12 18h.01',
  clock: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 6v6l4 2',
  calendar: 'M3 5h18v16H3z M7 3v4 M17 3v4 M3 10h18',
  search: 'M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16z M17 17l5 5',
  add: 'M12 5v14 M5 12h14',
  close: 'M5 5l14 14 M19 5 5 19',
  download: 'M12 3v12 m-5-5 5 5 5-5 M4 17v4h16v-4',
  sun: 'M12 3v2 M12 19v2 M3 12h2 M19 12h2 M5.6 5.6l1.4 1.4 M17 17l1.4 1.4 M18.4 5.6 17 7 M7 17l-1.4 1.4 M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  moon: 'M20.5 14.1A8.5 8.5 0 0 1 9.9 3.5 8.5 8.5 0 1 0 20.5 14.1z',
  filter: 'M4 6h16 M7 12h10 M10 18h4',
  check: 'm4 12 5 5L20 6',
  edit: 'M4 20h5l11-11-5-5L4 15v5z M13 6l5 5',
  trash: 'M4 7h16 M9 7V4h6v3 M6 7l1 14h10l1-14 M10 11v6 M14 11v6',
  refresh: 'M20 6v5h-5 M4 18v-5h5 M5 9a8 8 0 0 1 14-3l1 5 M4 13l1 5a8 8 0 0 0 14-3',
  undo: 'M9 14 4 9l5-5 M4 9h10a6 6 0 0 1 0 12h-2',
  chevron: 'm7 10 5 5 5-5',
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  money: 'M3 7h18v12H3z M3 7l3-3h12l3 3 M12 10a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  layers: 'm12 2 9 5-9 5-9-5 9-5z M3 12l9 5 9-5 M3 17l9 5 9-5',
  sparkles: 'm12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5L12 2z',
  info: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 10v6 M12 7h.01',
}
const d = computed(() => paths[props.name] || paths.package)
</script>
<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="d" /></svg>
</template>
