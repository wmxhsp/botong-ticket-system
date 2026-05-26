<template>
  <div class="bt-inline-loading" v-if="type === 'inline'">
    <div class="bt-spinner"></div> {{ text || '加载中...' }}
  </div>

  <div class="bt-empty-state" v-else-if="type === 'page'">
    <div class="bt-inline-loading" style="justify-content:center">
      <div class="bt-spinner"></div> {{ text || '加载中...' }}
    </div>
  </div>

  <div class="row g-2" v-else-if="type === 'cards'">
    <div class="col-6 col-sm-4 col-lg-2" v-for="i in count" :key="i">
      <div class="card p-2">
        <div class="bt-skeleton bt-skeleton-card" style="height:80px"></div>
      </div>
    </div>
  </div>

  <div class="bt-skeleton-table" v-else-if="type === 'table'">
    <div class="bt-skeleton bt-skeleton-title" style="width:30%"></div>
    <div v-for="i in count" :key="i">
      <div class="bt-skeleton bt-skeleton-row" style="width:100%"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'inline' },
  text: { type: String, default: '' },
  count: { type: Number, default: 6 },
})
</script>
