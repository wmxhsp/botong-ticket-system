<template>
  <div class="searchable-select" ref="wrapperRef">
    <div class="position-relative">
      <input
        class="form-control"
        :value="props.displayText || displayText"
        @input="onInput"
        @focus="onFocus"
        @keydown.down.prevent="highlightNext"
        @keydown.up.prevent="highlightPrev"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.esc="showDropdown = false"
        :placeholder="placeholder"
        :required="required"
        autocomplete="off"
      />
      <i v-if="loading" class="bi bi-arrow-repeat spin position-absolute" style="right:10px;top:50%;transform:translateY(-50%)"></i>
      <i v-else-if="showClear && displayText" class="bi bi-x-circle position-absolute text-muted" style="right:10px;top:50%;transform:translateY(-50%);cursor:pointer" @click="clear"></i>
    </div>
    <ul v-if="showDropdown && filteredOptions.length" class="searchable-dropdown">
      <li
        v-for="(opt, idx) in filteredOptions"
        :key="opt.value"
        :class="{ active: idx === highlightIndex }"
        @mousedown.prevent="selectOption(opt)"
        @mouseenter="highlightIndex = idx"
      >
        <slot name="option" :option="opt">
          <div class="fw-medium">{{ opt.label }}</div>
          <div v-if="opt.sub" class="small text-muted">{{ opt.sub }}</div>
        </slot>
      </li>
      <li v-if="allowCreate && displayText && filteredOptions.length === 0" class="create-new" @mousedown.prevent="$emit('create', displayText); showDropdown = false">
        <i class="bi bi-plus-circle me-1"></i> 创建"{{ displayText }}"
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
  asyncSearch: { type: Function, default: null },
  placeholder: { type: String, default: '搜索...' },
  required: { type: Boolean, default: false },
  allowCreate: { type: Boolean, default: false },
  clearable: { type: Boolean, default: true },
  labelKey: { type: String, default: 'name' },
  valueKey: { type: String, default: 'id' },
  displayText: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'select', 'create', 'search'])
const wrapperRef = ref(null)
const showDropdown = ref(false)
const highlightIndex = ref(-1)
const loading = ref(false)
const displayText = ref('')
const showClear = ref(false)
const localOptions = ref([])

const filteredOptions = computed(() => {
  const opts = props.options.length ? props.options : localOptions.value
  return opts
})

watch(() => props.modelValue, (val) => {
  if (!val) displayText.value = ''
})

function onInput(e) {
  const val = e.target.value
  displayText.value = val
  showDropdown.value = true
  highlightIndex.value = -1
  emit('update:modelValue', val)
  emit('search', val)
  if (props.asyncSearch) {
    loading.value = true
    Promise.resolve(props.asyncSearch(val)).then(results => {
      localOptions.value = (results || []).map(r => ({
        value: r[props.valueKey],
        label: r[props.labelKey],
        sub: r.sub || r.phone || r.contact || '',
        stock: r.stock,
        price: r.price,
        unit: r.unit,
        _raw: r,
      }))
    }).finally(() => { loading.value = false })
  }
}

function onFocus() {
  if (props.asyncSearch) {
    loading.value = true
    Promise.resolve(props.asyncSearch(displayText.value)).then(results => {
      localOptions.value = (results || []).map(r => ({
        value: r[props.valueKey],
        label: r[props.labelKey],
        sub: r.sub || r.phone || r.contact || '',
        stock: r.stock,
        price: r.price,
        unit: r.unit,
        _raw: r,
      }))
    }).finally(() => { loading.value = false })
  }
  showDropdown.value = true
}

function highlightNext() {
  if (highlightIndex.value < filteredOptions.value.length - 1) highlightIndex.value++
}
function highlightPrev() {
  if (highlightIndex.value > 0) highlightIndex.value--
}
function selectHighlighted() {
  if (highlightIndex.value >= 0 && filteredOptions.value[highlightIndex.value]) {
    selectOption(filteredOptions.value[highlightIndex.value])
  }
}

function selectOption(opt) {
  displayText.value = opt.label
  showDropdown.value = false
  emit('update:modelValue', opt.value)
  emit('select', opt._raw || opt)
}

function clear() {
  displayText.value = ''
  showDropdown.value = false
  emit('update:modelValue', '')
  emit('select', null)
}

function handleClickOutside(e) {
  if (wrapperRef.value && !wrapperRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
.searchable-select { position: relative; }
.searchable-dropdown {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 9999;
  background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1); max-height: 240px; overflow-y: auto;
  list-style: none; padding: 4px; margin: 2px 0 0;
}
[data-theme="dark"] .searchable-dropdown { background: var(--card-bg); border-color: var(--card-border); }
.searchable-dropdown li {
  padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 13px;
}
.searchable-dropdown li.active { background: #6366f1; color: white; }
.searchable-dropdown li.create-new { border-top: 1px solid var(--card-border); color: #6366f1; font-weight: 500; }
[data-theme="dark"] .searchable-dropdown li.create-new { border-color: var(--card-border); }
@keyframes spin { to { transform: translateY(-50%) rotate(360deg); } }
.spin { animation: spin 0.8s linear infinite; }
</style>
