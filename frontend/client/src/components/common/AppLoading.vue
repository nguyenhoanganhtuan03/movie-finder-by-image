<template>
  <div class="loading-overlay" v-if="visible">
    <div class="spinner"></div>
    <p class="loading-text" v-if="text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  text: {
    type: String,
    default: '',
  },
});
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(255, 255, 255, 0.75);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0d6efd;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: 1rem;
  font-weight: 500;
  color: #333;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
