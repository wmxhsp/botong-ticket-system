<template>
  <!-- 内联加载 -->
  <div class="bt-inline-loading" v-if="type === 'inline'">
    <div class="bt-spinner"></div> {{ text || '加载中...' }}
  </div>

  <!-- 页面级加载 -->
  <div class="bt-empty-state" v-else-if="type === 'page'">
    <div class="bt-inline-loading" style="justify-content:center">
      <div class="bt-spinner"></div> {{ text || '加载中...' }}
    </div>
  </div>

  <!-- 卡片列表骨架屏 -->
  <div class="row g-2" v-else-if="type === 'cards'">
    <div class="col-6 col-sm-4 col-lg-2" v-for="i in count" :key="i">
      <div class="card p-2">
        <div class="skeleton-card" style="height:80px"></div>
      </div>
    </div>
  </div>

  <!-- 表格骨架屏 -->
  <div class="skeleton-table" v-else-if="type === 'table'">
    <div class="skeleton-line skeleton-title" style="width:30%"></div>
    <div v-for="i in count" :key="i">
      <div class="skeleton-line skeleton-row" style="width:100%"></div>
    </div>
  </div>

  <!-- 列表项骨架屏（用于工单列表等） -->
  <div class="skeleton-list" v-else-if="type === 'list'">
    <div v-for="i in count" :key="i" class="skeleton-list-item">
      <div class="skeleton-line" style="width: 20%; height: 14px; margin-bottom: 8px;"></div>
      <div class="skeleton-line" style="width: 60%; height: 18px; margin-bottom: 8px;"></div>
      <div class="skeleton-line" style="width: 80%; height: 14px; margin-bottom: 8px;"></div>
      <div class="skeleton-line" style="width: 40%; height: 12px;"></div>
    </div>
  </div>

  <!-- 详情页面骨架屏 -->
  <div class="skeleton-detail" v-else-if="type === 'detail'">
    <div class="skeleton-line" style="width: 50%; height: 24px; margin-bottom: 16px;"></div>
    <div class="skeleton-line" style="width: 100%; height: 16px; margin-bottom: 12px;"></div>
    <div class="skeleton-line" style="width: 100%; height: 16px; margin-bottom: 12px;"></div>
    <div class="skeleton-line" style="width: 80%; height: 16px; margin-bottom: 24px;"></div>
    <div class="skeleton-line" style="width: 30%; height: 40px;"></div>
  </div>

  <!-- 统计卡片骨架屏 -->
  <div class="skeleton-stats" v-else-if="type === 'stats'">
    <div v-for="i in count" :key="i" class="skeleton-stat-card">
      <div class="skeleton-line" style="width: 40%; height: 14px; margin-bottom: 8px;"></div>
      <div class="skeleton-line" style="width: 60%; height: 28px;"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: { 
    type: String, 
    default: 'inline',
    validator: (value) => ['inline', 'page', 'cards', 'table', 'list', 'detail', 'stats'].includes(value)
  },
  text: { type: String, default: '' },
  count: { type: Number, default: 6 },
})
</script>

<style scoped>
/* 基础骨架屏样式 */
.skeleton-line {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* 卡片骨架屏 */
.skeleton-card {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}

/* 列表骨架屏 */
.skeleton-list {
  padding: 8px 0;
}

.skeleton-list-item {
  padding: 14px 16px;
  border-bottom: 1px solid var(--bt-gray-100, #e5e7eb);
}

.skeleton-list-item:last-child {
  border-bottom: none;
}

/* 表格骨架屏 */
.skeleton-table {
  padding: 16px;
}

.skeleton-title {
  margin-bottom: 16px;
  height: 24px;
}

.skeleton-row {
  height: 16px;
  margin-bottom: 12px;
}

.skeleton-row:last-child {
  margin-bottom: 0;
}

/* 详情页骨架屏 */
.skeleton-detail {
  padding: 24px;
}

/* 统计卡片骨架屏 */
.skeleton-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 16px 0;
}

.skeleton-stat-card {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .skeleton-line,
  .skeleton-card {
    background: linear-gradient(
      90deg,
      #2d2d2d 25%,
      #3d3d3d 50%,
      #2d2d2d 75%
    );
    background-size: 200% 100%;
  }
}

/* 保持原有的spinner样式 */
.bt-inline-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--bt-gray-500, #6b7280);
}

.bt-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--bt-gray-200, #e5e7eb);
  border-top-color: var(--bt-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
