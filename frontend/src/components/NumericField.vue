<script setup>
import { computed } from 'vue'
const props = defineProps({
  modelValue: { type: [Number, String], default: 0 },
  min: { type: [Number, String], default: undefined },
  max: { type: [Number, String], default: undefined },
  step: { type: [Number, String], default: 1 },
  buttonStep: { type: [Number, String], default: undefined },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  label: { type: String, default: 'Quantidade' },
})
const emit = defineEmits(['update:modelValue'])
const lower = computed(() => props.min === undefined || props.min === '' ? -Infinity : Number(props.min))
const upper = computed(() => props.max === undefined || props.max === '' || props.max == null ? Infinity : Number(props.max))
const stepNumber = computed(() => Number(props.buttonStep ?? props.step) > 0 ? Number(props.buttonStep ?? props.step) : 1)
function updateInput(event) {
  // Deixe o usuário esvaziar o campo ao digitar; a validação do formulário decide.
  emit('update:modelValue', event.target.value === '' ? '' : Number(event.target.value))
}
function changeBy(direction) {
  if (props.disabled) return
  const value = Number(props.modelValue)
  const base = Number.isFinite(value) ? value : (Number.isFinite(lower.value) ? lower.value : 0)
  const next = Math.min(upper.value, Math.max(lower.value, Math.round((base + direction * stepNumber.value) * 100) / 100))
  if (next !== base && Number.isFinite(next)) emit('update:modelValue', next)
}
</script>
<template>
  <span class="numeric-control">
    <button type="button" class="numeric-stepper numeric-decrease" :aria-label="`Diminuir ${label}`" :disabled="disabled || Number(modelValue) <= lower" @click="changeBy(-1)">−</button>
    <input :value="modelValue" type="number" inputmode="decimal" :min="min" :max="max" :step="step" :disabled="disabled" :required="required" :aria-label="label" @input="updateInput" />
    <button type="button" class="numeric-stepper numeric-increase" :aria-label="`Aumentar ${label}`" :disabled="disabled || Number(modelValue) >= upper" @click="changeBy(1)">+</button>
  </span>
</template>
