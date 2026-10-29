<template>
  <div class="stage-stepper-container" dir="rtl">
    <div class="stepper-track">
      <div
        v-for="(stage, idx) in stages"
        :key="stage.key"
        class="step-node"
        :class="{
          'step-completed': currentStageIndex > idx,
          'step-active': currentStageIndex === idx && isRunning,
          'step-pending': currentStageIndex < idx || (!isRunning && currentStageIndex === idx)
        }"
      >
        <!-- Connector Line -->
        <div v-if="idx > 0" class="step-line" :class="{ 'line-active': currentStageIndex >= idx }"></div>

        <!-- Step Icon / Circle -->
        <div class="step-circle">
          <span v-if="currentStageIndex > idx" class="check-icon">✓</span>
          <span v-else-if="currentStageIndex === idx && isRunning" class="step-spinner"></span>
          <span v-else>{{ stage.icon }}</span>
        </div>

        <!-- Step Label -->
        <div class="step-info">
          <span class="step-title">{{ stage.title }}</span>
          <span class="step-sub">{{ stage.sub }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  currentStage?: string; // e.g. 'isolation', 'asr', 'translation', 'alignment', 'export'
  isRunning?: boolean;
}>();

const stages = [
  { key: 'isolation', icon: '🎙️', title: 'عزل الصوت', sub: 'Demucs / Spleeter' },
  { key: 'asr', icon: '📝', title: 'تفريغ الكلام', sub: 'Whisper ASR Engine' },
  { key: 'translation', icon: '🌐', title: 'ترجمة النصوص', sub: 'Gemini / GTX AI' },
  { key: 'alignment', icon: '⏱️', title: 'التزامن الصوتي', sub: 'Grounding & Timestamps' },
  { key: 'export', icon: '🎬', title: 'جاهز للمعاينة', sub: 'SRT / VTT / Preview' }
];

const currentStageIndex = computed(() => {
  if (!props.currentStage) return 0;
  const stageMap: Record<string, number> = {
    'upload': 0,
    'isolation': 0,
    'vocal_isolation': 0,
    'audio_processing': 0,
    'asr': 1,
    'transcription': 1,
    'translation': 2,
    'translating': 2,
    'alignment': 3,
    'grounding': 3,
    'export': 4,
    'completed': 5,
    'done': 5
  };
  return stageMap[props.currentStage.toLowerCase()] ?? 1;
});
</script>

<style scoped>
.stage-stepper-container {
  width: 100%;
  background: #0F172A;
  border: 1px solid #1E293B;
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.stepper-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.step-node {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
  text-align: center;
  z-index: 1;
}

.step-line {
  position: absolute;
  top: 18px;
  right: -50%;
  left: 50%;
  height: 2px;
  background: #334155;
  z-index: -1;
  transition: background 0.3s;
}

.line-active {
  background: linear-gradient(90deg, #10B981, #3B82F6);
}

.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #090E1A;
  border: 2px solid #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #94A3B8;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.step-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.step-title {
  font-size: 12px;
  font-weight: 700;
  color: #94A3B8;
  transition: color 0.2s;
}

.step-sub {
  font-size: 10px;
  color: #64748B;
}

/* Completed Step */
.step-completed .step-circle {
  background: #064E3B;
  border-color: #10B981;
  color: #FFFFFF;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.35);
}

.step-completed .check-icon {
  font-weight: 900;
  font-size: 14px;
  color: #34D399;
}

.step-completed .step-title {
  color: #E2E8F0;
}

/* Active Step */
.step-active .step-circle {
  background: #1E3A8A;
  border-color: #3B82F6;
  color: #FFFFFF;
  box-shadow: 0 0 14px rgba(59, 130, 246, 0.5);
  animation: glow 1.8s infinite;
}

.step-active .step-title {
  color: #60A5FA;
  font-weight: 800;
}

.step-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes glow {
  0%, 100% { box-shadow: 0 0 8px rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 18px rgba(59, 130, 246, 0.8); }
}

@media (max-width: 768px) {
  .step-sub {
    display: none;
  }
  .step-title {
    font-size: 10px;
  }
}
</style>
