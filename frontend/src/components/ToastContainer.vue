<template>
  <div class="toast-container" dir="rtl">
    <transition-group name="toast-anim" tag="div" class="toast-list">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast-item"
        :class="'toast-' + toast.type"
      >
        <div class="toast-icon">
          <span v-if="toast.type === 'success'">✅</span>
          <span v-else-if="toast.type === 'error'">❌</span>
          <span v-else-if="toast.type === 'warning'">⚠️</span>
          <span v-else>ℹ️</span>
        </div>

        <div class="toast-body">
          <div v-if="toast.title" class="toast-title">{{ toast.title }}</div>
          <div class="toast-message">{{ toast.message }}</div>
        </div>

        <button class="toast-close" @click="remove(toast.id)" title="إغلاق">✕</button>

        <div
          class="toast-progress-bar"
          :style="{ animationDuration: toast.duration + 'ms' }"
        ></div>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '../composables/useToast';

const { toasts, remove } = useToast();
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 24px;
  z-index: 9999999;
  pointer-events: none;
  max-width: 380px;
  width: calc(100% - 48px);
}

.toast-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast-item {
  pointer-events: auto;
  position: relative;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.94);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(51, 65, 85, 0.8);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.toast-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: right;
}

.toast-title {
  font-size: 13px;
  font-weight: 700;
  color: #F8FAFC;
}

.toast-message {
  font-size: 12px;
  color: #CBD5E1;
  line-height: 1.4;
  word-break: break-word;
}

.toast-close {
  background: transparent;
  border: none;
  color: #64748B;
  font-size: 14px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.15s;
}

.toast-close:hover {
  color: #F8FAFC;
}

/* Colors */
.toast-success {
  border-color: rgba(16, 185, 129, 0.4);
}
.toast-success .toast-progress-bar {
  background: #10B981;
}

.toast-error {
  border-color: rgba(239, 68, 68, 0.4);
}
.toast-error .toast-progress-bar {
  background: #EF4444;
}

.toast-warning {
  border-color: rgba(245, 158, 11, 0.4);
}
.toast-warning .toast-progress-bar {
  background: #F59E0B;
}

.toast-info {
  border-color: rgba(59, 130, 246, 0.4);
}
.toast-info .toast-progress-bar {
  background: #3B82F6;
}

/* Progress bar */
.toast-progress-bar {
  position: absolute;
  bottom: 0;
  right: 0;
  left: 0;
  height: 3px;
  transform-origin: right;
  animation: toastTimer linear forwards;
}

@keyframes toastTimer {
  from {
    transform: scaleX(1);
  }
  to {
    transform: scaleX(0);
  }
}

/* Transitions */
.toast-anim-enter-active,
.toast-anim-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-anim-enter-from {
  opacity: 0;
  transform: translateX(-30px) scale(0.9);
}

.toast-anim-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
</style>
