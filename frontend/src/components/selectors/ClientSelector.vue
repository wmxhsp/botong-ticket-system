<template>
  <SearchableSelect
    :modelValue="modelValue"
    @update:modelValue="$emit('update:modelValue', $event)"
    @select="$emit('select', $event)"
    @create="handleCreate"
    placeholder="搜索客户..."
    :asyncSearch="searchClients"
    labelKey="name"
    valueKey="name"
    allowCreate
  >
    <template #option="{ option }">
      <div class="fw-medium">{{ option.label }}</div>
      <div class="small text-muted">{{ option.sub }}</div>
    </template>
  </SearchableSelect>
</template>

<script setup>
import SearchableSelect from './SearchableSelect.vue'
import { clientApi } from '@/api/clients'

defineProps({ modelValue: { type: [String, Number], default: '' } })
const emit = defineEmits(['update:modelValue', 'select'])

async function searchClients(q) {
  try {
    const params = {}
    if (q && q.length >= 1) params.q = q
    const data = await clientApi.list(params)
    const list = Array.isArray(data) ? data : data?.clients || data?.data || []
    return list.slice(0, 50).map(c => ({
      id: c.id || c.name,
      name: c.name,
      sub: `${c.phone || ''} ${c.contact || ''}`.trim() || `活跃工单: ${c.active_tickets || 0}`,
      ...c,
    }))
  } catch { return [] }
}

async function handleCreate(name) {
  try {
    await clientApi.create({ name })
    emit('update:modelValue', name)
    emit('select', { name })
  } catch (e) {
    console.error('创建客户失败:', e)
  }
}
</script>
