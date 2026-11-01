<script setup>
import { computed } from 'vue'
import { formatMoney } from '../utils'
const props = defineProps({
  rows: { type: Array, default: () => [] },
  type: { type: String, default: 'bar' },
  currency: { type: Boolean, default: true },
  label: { type: String, default: 'Gráfico' },
})
const palette = ['#15ae88', '#4c86d7', '#e5a442', '#8664d7', '#ed6f72', '#16a7b9', '#bd71b3', '#94a8b9', '#c9853e', '#7eaa55', '#d56e9c', '#597c9e']
const display = computed(() => props.rows.filter(p => Number(p.value) > 0 || props.type !== 'donut'))
const width = computed(() => Math.max(480, display.value.length * 42))
const height = 260
const top = 16
const bottom = 45
const max = computed(() => Math.max(1, ...display.value.map(p => Number(p.value))))
const px = i => 45 + (i + .5) * ((width.value - 65) / Math.max(1, display.value.length))
const py = val => top + (height - top - bottom) * (1 - Number(val) / max.value)
const points = computed(() => display.value.map((p, i) => `${px(i)},${py(p.value)}`).join(' '))
const area = computed(() => `45,${height - bottom} ${points.value} ${px(display.value.length - 1)},${height - bottom}`)
const sum = computed(() => display.value.reduce((s, p) => s + Number(p.value), 0))
const circumference = 2 * Math.PI * 72
const segments = computed(() => {
  let offset = 0
  return display.value.map((item, i) => {
    const length = sum.value ? Number(item.value) / sum.value * circumference : 0
    const segment = { ...item, color: palette[i % palette.length], length, offset }
    offset += length
    return segment
  })
})
const renderAmount = v => props.currency ? formatMoney(v) : `${Number(v).toLocaleString('pt-BR')} un.`
const formatLabel = label => /^\d{4}-\d{2}-\d{2}$/.test(label) ? `${label.slice(8)}/${label.slice(5, 7)}` : /^\d{4}-\d{2}$/.test(label) ? `${label.slice(5)}/${label.slice(0, 4)}` : label
</script>
<template>
  <div v-if="!rows.length || !sum" class="chart-empty">Não há vendas para representar neste intervalo.</div>
  <div v-else-if="type === 'donut'" class="donut-layout" :aria-label="label" role="img">
    <svg viewBox="0 0 230 230" class="donut-svg" aria-hidden="true">
      <circle cx="115" cy="115" r="72" fill="none" stroke="var(--stroke)" stroke-width="28" />
      <circle v-for="(segment, i) in segments" :key="i" cx="115" cy="115" r="72" fill="none" :stroke="segment.color" stroke-width="28" :stroke-dasharray="`${segment.length} ${circumference - segment.length}`" :stroke-dashoffset="-segment.offset" transform="rotate(-90 115 115)"><title>{{ segment.label }}: {{ renderAmount(segment.value) }}</title></circle>
      <text x="115" y="110" text-anchor="middle" class="donut-title">TOTAL</text>
      <text x="115" y="135" text-anchor="middle" class="donut-total">{{ currency ? formatMoney(sum) : sum.toLocaleString('pt-BR') }}</text>
    </svg>
    <div class="chart-legend"><div v-for="(segment, i) in segments" :key="i" class="legend-entry"><span class="legend-color" :style="{ background: segment.color }"></span><span class="legend-label" :title="segment.label">{{ formatLabel(segment.label) }}</span><strong>{{ (segment.value / sum * 100).toFixed(1).replace('.', ',') }}%</strong></div></div>
  </div>
  <div v-else class="decision-chart-scroll" role="group" :aria-label="label">
    <svg :viewBox="`0 0 ${width} ${height}`" :style="{ minWidth: `${width}px` }" class="decision-svg" aria-hidden="true">
      <line x1="40" :x2="width - 15" :y1="height - bottom" :y2="height - bottom" stroke="var(--stroke)" />
      <line v-for="n in 3" :key="n" x1="40" :x2="width - 15" :y1="py(n * max / 4)" :y2="py(n * max / 4)" stroke="var(--stroke)" stroke-dasharray="3 5" />
      <polygon v-if="type === 'area'" :points="area" fill="rgba(21, 174, 136, .16)" />
      <polyline v-if="type === 'line' || type === 'area'" :points="points" fill="none" stroke="#15ae88" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      <g v-for="(point, i) in display" :key="i">
        <rect v-if="type === 'bar'" :x="px(i) - 12" :y="py(point.value)" width="24" :height="Math.max(0, height - bottom - py(point.value))" rx="5" fill="#15ae88"><title>{{ point.label }}: {{ renderAmount(point.value) }}</title></rect>
        <circle v-else :cx="px(i)" :cy="py(point.value)" r="4.5" fill="#15ae88" stroke="var(--surface)" stroke-width="2"><title>{{ point.label }}: {{ renderAmount(point.value) }}</title></circle>
        <text v-if="display.length <= 14 || i % Math.ceil(display.length / 10) === 0" :x="px(i)" :y="height - 20" text-anchor="middle" class="chart-axis-label">{{ formatLabel(point.label).slice(0, 12) }}</text>
      </g>
    </svg>
    <p class="chart-footnote">Passe o cursor sobre os pontos para consultar os valores. No celular, deslize para ver o gráfico completo.</p>
    <details class="chart-data-mobile">
      <summary>Ver os valores deste gráfico</summary>
      <div class="chart-data-list">
        <div v-for="(point, i) in display" :key="i"><span>{{ formatLabel(point.label) }}</span><strong>{{ renderAmount(point.value) }}</strong></div>
      </div>
    </details>
  </div>
</template>
