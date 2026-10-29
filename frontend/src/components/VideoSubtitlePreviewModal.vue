<template>
  <div v-if="isOpen" class="preview-overlay" dir="rtl">
    <div class="preview-modal">
      <!-- Modal Header -->
      <div class="preview-header">
        <div class="header-info">
          <span class="header-icon">🎬</span>
          <div>
            <h3 class="header-title">مشغل المعاينة المباشرة وتدقيق الترجمة</h3>
            <p class="header-sub">{{ fileName || 'معاينة الترجمة المتزامنة مع الفيديو' }}</p>
          </div>
        </div>
        <div class="header-actions">
          <button class="btn-export" @click="downloadSRT" title="تحميل ملف SRT">
            <span>📥</span> تحميل SRT
          </button>
          <button class="btn-export" @click="downloadVTT" title="تحميل ملف VTT">
            <span>📄</span> تحميل VTT
          </button>
          <button class="btn-close" @click="close" title="إغلاق المعاينة">✕</button>
        </div>
      </div>

      <!-- Modal Body (2 Columns) -->
      <div class="preview-body">
        <!-- RIGHT: Video Player with Subtitle Overlay -->
        <div class="player-column">
          <div class="video-wrapper">
            <video
              ref="videoRef"
              class="main-video"
              :src="videoUrl"
              controls
              @timeupdate="onTimeUpdate"
            ></video>

            <!-- Live Subtitle Overlay on Video Screen -->
            <div v-if="activeSubtitle" class="video-subtitle-overlay">
              <span class="subtitle-text">{{ activeSubtitle.text }}</span>
            </div>
          </div>

          <!-- Video playback hint -->
          <div class="player-toolbar">
            <span class="time-badge">⏱️ التوقيت الحالي: {{ formatTime(currentTime) }}</span>
            <span class="cue-count-badge">عدد الأسطر: {{ cues.length }} سطر</span>
          </div>
        </div>

        <!-- LEFT: Interactive Subtitle Editor List -->
        <div class="cues-column">
          <div class="cues-header">
            <span>📝 قائمة الأسطر والتوقيتات (انقر للانتقال أو التعديل):</span>
          </div>

          <div class="cues-list" ref="cuesListRef">
            <div
              v-for="(cue, idx) in cues"
              :key="'cue-' + idx"
              class="cue-item"
              :class="{ 'cue-active': currentCueIndex === idx }"
              @click="seekToCue(cue, idx)"
            >
              <div class="cue-top">
                <span class="cue-num">#{{ idx + 1 }}</span>
                <span class="cue-time">
                  {{ formatSeconds(cue.start) }} ➔ {{ formatSeconds(cue.end) }}
                </span>
                <span v-if="currentCueIndex === idx" class="cue-playing-badge">نشط الآن ▶</span>
              </div>
              <input
                v-model="cue.text"
                class="cue-text-input"
                placeholder="نص الترجمة..."
                @click.stop
              />
            </div>

            <div v-if="cues.length === 0" class="cues-empty">
              <span>لا توجد أسطر ترجمة لعرضها حالياً.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { useToast } from '../composables/useToast';

export interface SubtitleCue {
  start: number; // in seconds
  end: number;   // in seconds
  text: string;
}

const props = defineProps<{
  modelValue?: boolean;
  videoUrl?: string;
  fileName?: string;
  initialCues?: SubtitleCue[];
  srtContent?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
  (e: 'close'): void;
}>();

const toast = useToast();
const isOpen = ref(true);
const videoRef = ref<HTMLVideoElement | null>(null);
const cuesListRef = ref<HTMLElement | null>(null);
const currentTime = ref(0);
const cues = ref<SubtitleCue[]>([]);

// Parse SRT content to cues if provided
function parseSRT(srt: string): SubtitleCue[] {
  if (!srt) return [];
  const normalized = srt.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const blocks = normalized.split(/\n\n+/);
  const parsed: SubtitleCue[] = [];

  for (const block of blocks) {
    const lines = block.trim().split('\n');
    if (lines.length >= 2) {
      let timeLineIdx = 0;
      if (/^\d+$/.test(lines[0].trim())) {
        timeLineIdx = 1;
      }
      const timeLine = lines[timeLineIdx];
      if (timeLine && timeLine.includes('-->')) {
        const [startStr, endStr] = timeLine.split('-->').map(s => s.trim());
        const startSec = timeStringToSeconds(startStr);
        const endSec = timeStringToSeconds(endStr);
        const textLines = lines.slice(timeLineIdx + 1).join('\n');
        if (!isNaN(startSec) && !isNaN(endSec)) {
          parsed.push({
            start: startSec,
            end: endSec,
            text: textLines.trim()
          });
        }
      }
    }
  }
  return parsed;
}

function timeStringToSeconds(str: string): number {
  if (!str) return 0;
  const parts = str.replace(',', '.').split(':');
  if (parts.length === 3) {
    const h = parseFloat(parts[0]);
    const m = parseFloat(parts[1]);
    const s = parseFloat(parts[2]);
    return h * 3600 + m * 60 + s;
  }
  return 0;
}

function formatSeconds(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 1000);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(3, '0').slice(0, 2)}`;
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// Watch initial content
watch(
  () => props.srtContent,
  (newSrt) => {
    if (newSrt) {
      cues.value = parseSRT(newSrt);
    }
  },
  { immediate: true }
);

watch(
  () => props.initialCues,
  (newCues) => {
    if (newCues && newCues.length > 0) {
      cues.value = [...newCues];
    }
  },
  { immediate: true }
);

// Active cue calculation
const currentCueIndex = computed(() => {
  const t = currentTime.value;
  return cues.value.findIndex(c => t >= c.start && t <= c.end);
});

const activeSubtitle = computed(() => {
  const idx = currentCueIndex.value;
  return idx !== -1 ? cues.value[idx] : null;
});

function onTimeUpdate(e: Event) {
  const target = e.target as HTMLVideoElement;
  if (target) {
    currentTime.value = target.currentTime;
  }
}

function seekToCue(cue: SubtitleCue, idx: number) {
  if (videoRef.value) {
    videoRef.value.currentTime = cue.start;
    videoRef.value.play();
  }
}

// Auto scroll cue into view
watch(currentCueIndex, (newIdx) => {
  if (newIdx !== -1 && cuesListRef.value) {
    const el = cuesListRef.value.children[newIdx] as HTMLElement;
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }
});

function generateSRT(): string {
  return cues.value
    .map((c, i) => {
      const startStr = formatSRTTime(c.start);
      const endStr = formatSRTTime(c.end);
      return `${i + 1}\n${startStr} --> ${endStr}\n${c.text}\n`;
    })
    .join('\n');
}

function generateVTT(): string {
  const body = cues.value
    .map((c, i) => {
      const startStr = formatVTTTime(c.start);
      const endStr = formatVTTTime(c.end);
      return `${i + 1}\n${startStr} --> ${endStr}\n${c.text}\n`;
    })
    .join('\n');
  return `WEBVTT\n\n${body}`;
}

function formatSRTTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}

function formatVTTTime(sec: number): string {
  return formatSRTTime(sec).replace(',', '.');
}

function downloadFile(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function downloadSRT() {
  const baseName = (props.fileName || 'subtitles').replace(/\.[^/.]+$/, '');
  downloadFile(generateSRT(), `${baseName}_translated.srt`, 'text/plain;charset=utf-8');
  toast.success('تم تنزيل ملف SRT بنجاح!');
}

function downloadVTT() {
  const baseName = (props.fileName || 'subtitles').replace(/\.[^/.]+$/, '');
  downloadFile(generateVTT(), `${baseName}_translated.vtt`, 'text/vtt;charset=utf-8');
  toast.success('تم تنزيل ملف VTT بنجاح!');
}

function close() {
  isOpen.value = false;
  emit('update:modelValue', false);
  emit('close');
}
</script>

<style scoped>
.preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 999998;
  background: rgba(6, 11, 25, 0.92);
  backdrop-filter: blur(14px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  animation: fadeIn 0.25s ease-out;
}

.preview-modal {
  width: 100%;
  max-width: 1100px;
  height: 85vh;
  max-height: 750px;
  background: #0B132B;
  border: 1px solid #1E293B;
  border-radius: 16px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8), 0 0 35px rgba(59, 130, 246, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.preview-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
  border-bottom: 1px solid #1E293B;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
}

.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #F8FAFC;
  margin: 0;
}

.header-sub {
  font-size: 11px;
  color: #94A3B8;
  margin: 2px 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-export {
  background: #1E293B;
  color: #E2E8F0;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-export:hover {
  background: #2563EB;
  border-color: #3B82F6;
  color: #FFFFFF;
}

.btn-close {
  background: transparent;
  color: #94A3B8;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 6px;
  transition: all 0.2s;
}

.btn-close:hover {
  color: #EF4444;
  background: rgba(239, 68, 68, 0.1);
}

/* Body */
.preview-body {
  flex: 1;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  overflow: hidden;
}

/* Player Column */
.player-column {
  background: #030712;
  border-left: 1px solid #1E293B;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  flex: 1;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-video {
  width: 100%;
  height: 100%;
  max-height: 480px;
  object-fit: contain;
}

.video-subtitle-overlay {
  position: absolute;
  bottom: 40px;
  left: 20px;
  right: 20px;
  text-align: center;
  pointer-events: none;
  z-index: 10;
}

.subtitle-text {
  display: inline-block;
  background: rgba(0, 0, 0, 0.78);
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  line-height: 1.4;
  max-width: 90%;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
}

.player-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #94A3B8;
  padding: 0 4px;
}

.time-badge {
  background: #1E293B;
  padding: 4px 10px;
  border-radius: 6px;
  font-family: monospace;
  color: #38BDF8;
}

.cue-count-badge {
  background: #1E293B;
  padding: 4px 10px;
  border-radius: 6px;
}

/* Cues Column */
.cues-column {
  background: #0F172A;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cues-header {
  padding: 14px 16px;
  border-bottom: 1px solid #1E293B;
  font-size: 12px;
  font-weight: 700;
  color: #94A3B8;
}

.cues-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cue-item {
  background: #090E1A;
  border: 1px solid #1E293B;
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cue-item:hover {
  border-color: #3B82F6;
  background: #131E3A;
}

.cue-active {
  background: rgba(37, 99, 235, 0.15) !important;
  border-color: #3B82F6 !important;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.25);
}

.cue-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
}

.cue-num {
  font-weight: 700;
  color: #64748B;
}

.cue-time {
  font-family: monospace;
  color: #38BDF8;
  direction: ltr;
}

.cue-playing-badge {
  font-size: 10px;
  color: #10B981;
  font-weight: 700;
  animation: pulse 1.5s infinite;
}

.cue-text-input {
  width: 100%;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 4px 6px;
  color: #F8FAFC;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  box-sizing: border-box;
}

.cue-text-input:focus {
  background: #030712;
  border-color: #3B82F6;
}

.cues-empty {
  text-align: center;
  padding: 40px 10px;
  color: #64748B;
  font-size: 13px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
