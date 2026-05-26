<template>
  <Teleport to="body">
    <div v-if="visible" class="photo-preview-overlay" @click.self="close">
      <button class="photo-preview-close" @click="close">
        <i class="bi bi-x-lg"></i>
      </button>
      
      <button class="photo-preview-prev" @click="prev" :disabled="currentIndex === 0">
        <i class="bi bi-chevron-left"></i>
      </button>
      
      <div class="photo-preview-content">
        <img :src="currentPhoto.url" :alt="currentPhoto.name" class="photo-preview-img" />
        <div class="photo-preview-info">
          <span>{{ currentPhoto.name }}</span>
          <span class="photo-preview-counter">{{ currentIndex + 1 }} / {{ photos.length }}</span>
        </div>
      </div>
      
      <button class="photo-preview-next" @click="next" :disabled="currentIndex === photos.length - 1">
        <i class="bi bi-chevron-right"></i>
      </button>
      
      <div class="photo-preview-indicators">
        <span 
          v-for="(photo, idx) in photos" 
          :key="photo.id || idx"
          class="photo-preview-indicator"
          :class="{ active: idx === currentIndex }"
          @click="goTo(idx)"
        ></span>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  photos: { type: Array, default: () => [] },
  initialIndex: { type: Number, default: 0 },
})

const emit = defineEmits(['close'])

const currentIndex = ref(0)

const currentPhoto = computed(() => {
  return props.photos[currentIndex.value] || { url: '', name: '' }
})

watch(() => props.visible, (val) => {
  if (val) {
    currentIndex.value = props.initialIndex
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

watch(() => props.initialIndex, (val) => {
  currentIndex.value = val
})

function close() {
  emit('close')
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

function next() {
  if (currentIndex.value < props.photos.length - 1) {
    currentIndex.value++
  }
}

function goTo(idx) {
  currentIndex.value = idx
}
</script>

<style scoped>
.photo-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.photo-preview-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.photo-preview-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.photo-preview-prev,
.photo-preview-next {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.photo-preview-prev {
  left: 20px;
}

.photo-preview-next {
  right: 20px;
}

.photo-preview-prev:hover:not(:disabled),
.photo-preview-next:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
}

.photo-preview-prev:disabled,
.photo-preview-next:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.photo-preview-content {
  max-width: 90vw;
  max-height: 90vh;
  position: relative;
}

.photo-preview-img {
  max-width: 100%;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.photo-preview-info {
  position: absolute;
  bottom: -40px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  font-size: 14px;
  padding: 8px 0;
}

.photo-preview-counter {
  opacity: 0.7;
}

.photo-preview-indicators {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}

.photo-preview-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: background 0.2s;
}

.photo-preview-indicator.active {
  background: white;
}
</style>
