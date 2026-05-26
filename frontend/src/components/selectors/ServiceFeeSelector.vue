<template>
  <SearchableSelect
    :modelValue="modelValue"
    @update:modelValue="$emit('update:modelValue', $event)"
    @select="onSelect"
    placeholder="搜索服务规则..."
    :asyncSearch="searchFees"
    labelKey="name"
    valueKey="id"
  >
    <template #option="{ option }">
      <div class="d-flex justify-content-between">
        <span class="fw-medium">{{ option.label }}</span>
        <span>¥{{ option.price }}</span>
      </div>
      <div class="small text-muted">{{ option.sub }}</div>
    </template>
  </SearchableSelect>
</template>

<script setup>
import SearchableSelect from './SearchableSelect.vue'
import { serviceFeeApi } from '@/api/service-fees'

defineProps({ modelValue: { type: [String, Number], default: '' } })
const emit = defineEmits(['update:modelValue', 'select'])

let feesCache = null
let cacheTime = 0
const CACHE_TTL = 30000

function onSelect(item) {
  emit('select', item)
}

async function searchFees(q) {
  try {
    const now = Date.now()
    if (!feesCache || now - cacheTime > CACHE_TTL) {
      const data = await serviceFeeApi.list()
      const list = Array.isArray(data) ? data : data?.fees || data?.data || []
      feesCache = list.filter(f => f.active !== false && f.active !== 0)
      cacheTime = now
    }
    return feesCache.filter(f => !q || (f.name && f.name.includes(q))).map(f => ({
      id: f.id,
      name: f.name,
      price: f.unit_price || 0,
      sub: f.description || f.fee_type || '',
      _raw: f,
    }))
  } catch { return [] }
}
</script>
