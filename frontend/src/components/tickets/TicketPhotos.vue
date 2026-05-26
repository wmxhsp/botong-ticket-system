<template>
  <div class="card p-3 p-md-4 mb-2">
    <h5 class="mb-3 d-flex align-items-center gap-2">
      <i class="bi bi-camera me-2"></i>现场照片
      <button class="btn btn-sm btn-outline-primary ms-auto" @click="$emit('upload')">
        <i class="bi bi-upload"></i> 上传
      </button>
    </h5>
    <div v-if="photos.length === 0" class="text-muted small py-4 text-center">暂无照片</div>
    <div v-else class="row g-2">
      <div v-for="(p, idx) in photos" :key="idx" class="col-6 col-sm-4 col-md-3">
        <div class="position-relative bt-photo-item">
          <img :src="p.filepath || p.url" class="w-100 rounded border" style="height:96px;object-fit:cover" loading="lazy" @click="$emit('preview', p)">
          <button class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1 bt-photo-delete" @click="$emit('delete', p)">
            <i class="bi bi-x"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  photos: { type: Array, default: () => [] },
})
defineEmits(['upload', 'delete', 'preview'])
</script>

<style scoped>
.bt-photo-delete { opacity: 0.5; transition: opacity 0.15s ease; }
.bt-photo-item:hover .bt-photo-delete { opacity: 1; }
</style>
