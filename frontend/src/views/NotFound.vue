<template>
  <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:var(--bt-body-bg)">
    <div class="bt-empty-state">
      <div class="bt-empty-icon"><i class="bi bi-emoji-neutral" style="font-size:64px;color:var(--bt-gray-300)"></i></div>
      <div class="bt-empty-title" style="font-size:24px;margin-bottom:4px">404</div>
      <div class="bt-empty-title">页面未找到</div>
      <div class="bt-empty-desc">您访问的页面不存在或已被移除</div>
      <router-link to="/app/" class="btn btn-primary btn-sm mt-3">
        <i class="bi bi-house me-1"></i> 返回首页
      </router-link>
    </div>
  </div>
</template>
