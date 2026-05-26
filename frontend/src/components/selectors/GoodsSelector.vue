<template>
  <SearchableSelect
    :modelValue="modelValue"
    :displayText="selectedText"
    @update:modelValue="$emit('update:modelValue', $event)"
    @select="onSelect"
    placeholder="搜索商品..."
    :asyncSearch="searchGoods"
    labelKey="name"
    valueKey="id"
  >
    <template #option="{ option }">
      <div class="d-flex justify-content-between">
        <span class="fw-medium">{{ option.label }}</span>
        <span :class="option.stock > 0 ? 'text-success' : 'text-danger'">
          库存: {{ option.stock }}
          <i v-if="option.stock <= 0" class="bi bi-exclamation-triangle-fill text-danger ms-1" title="库存不足"></i>
        </span>
      </div>
      <div class="small text-muted">¥{{ option.price }} / {{ option.unit || '个' }}</div>
    </template>
  </SearchableSelect>
</template>

<script setup>
import { ref, watch } from 'vue'
import SearchableSelect from './SearchableSelect.vue'
import { goodsApi } from '@/api/goods'

const props = defineProps({ modelValue: { type: [String, Number], default: '' } })
const emit = defineEmits(['update:modelValue', 'select'])

const selectedText = ref('')
let goodsCache = null
let cacheTime = 0
const CACHE_TTL = 30000

function onSelect(item) {
  selectedText.value = item.label || item.name || ''
  emit('select', item)
}

async function searchGoods(q) {
  try {
    const now = Date.now()
    if (!goodsCache || now - cacheTime > CACHE_TTL) {
      const data = await goodsApi.list({ q })
      const list = Array.isArray(data) ? data : data?.goods || data?.data || []
      goodsCache = list
      cacheTime = now
    }
    const sourceList = Array.isArray(goodsCache) ? goodsCache : goodsCache?.goods || goodsCache?.data || []
    const filtered = q ? sourceList.filter(g => g.name && g.name.toLowerCase().includes(q.toLowerCase())) : sourceList
    return filtered.map(g => ({
      id: g.id,
      name: g.name,
      sub: `库存: ${g.stock || 0} | ¥${g.selling_price || g.unit_price || 0}`,
      stock: g.stock || g.quantity || 0,
      price: g.selling_price || g.unit_price || 0,
      unit: g.unit || '个',
      _raw: g,
    }))
  } catch { return [] }
}

watch(() => props.modelValue, (val) => {
  if (!val) {
    selectedText.value = ''
  }
})
</script>
