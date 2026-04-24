<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: { type: String, default: '' },
  type: { type: String, default: 'success' },
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const visible = ref(false)

watch(() => props.show, (val) => {
  if (val) {
    visible.value = true
    setTimeout(() => {
      visible.value = false
      emit('close')
    }, 3000)
  }
})
</script>

<template>
  <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 1080">
    <div
      v-if="visible"
      class="toast show align-items-center border-0"
      :class="`text-bg-${type}`"
      role="alert"
    >
      <div class="d-flex">
        <div class="toast-body">{{ message }}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" @click="visible = false; emit('close')"></button>
      </div>
    </div>
  </div>
</template>
