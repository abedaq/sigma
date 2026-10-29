<template>
  <div v-if="isOpen" class="history-overlay" dir="rtl">
    <div class="history-modal">
      <div class="history-header">
        <div class="header-title-box">
          <span class="header-icon">📂</span>
          <div>
            <h3>سجل المشاريع والملفات السابقة</h3>
            <p>الملفات التي تمت معالجتها وترجمتها مؤخراً على هذا الجهاز</p>
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <button
            v-if="historyItems.length > 0"
            class="btn-clear"
            @click="handleClearAll"
            title="مسح السجل بالكامل"
          >
            🗑️ مسح السجل
          </button>
          <button class="btn-close" @click="close" title="إغلاق">✕</button>
        </div>
      </div>

      <div class="history-body">
        <div v-if="historyItems.length === 0" class="history-empty">
          <div class="empty-icon">📁</div>
          <p>لا توجد ملفات سابقة مسجلة في هذا الجهاز بعد.</p>
          <small>ستظهر الملفات هنا تلقائياً فور اكتمال معالجتها وترجمتها.</small>
        </div>

        <div v-else class="history-list">
          <div
            v-for="item in historyItems"
            :key="item.id"
            class="history-card"
          >
            <div class="card-meta">
              <span class="file-icon">🎬</span>
              <div class="file-details">
                <span class="file-name" :title="item.fileName">{{ item.fileName }}</span>
                <span class="file-sub">
                  {{ formatDate(item.timestamp) }} •
                  <span class="lang-tag">{{ item.sourceLang }} ➔ {{ item.targetLang }}</span>
                  <span v-if="item.fileSize">• {{ item.fileSize }}</span>
                </span>
              </div>
            </div>

            <div class="card-actions">
              <button
                v-if="item.srtContent"
                class="btn-preview"
                @click="openPreview(item)"
                title="معاينة الترجمة"
              >
                👁️ معاينة
              </button>
              <button
                v-if="item.srtContent"
                class="btn-download"
                @click="downloadSRT(item)"
                title="تحميل ملف SRT"
              >
                📥 تحميل
              </button>
              <button
                class="btn-delete"
                @click="removeItem(item.id)"
                title="إزالة من السجل"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useHistory, HistoryItem } from '../composables/useHistory';
import { useToast } from '../composables/useToast';

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'preview', item: HistoryItem): void;
}>();

const { historyItems, removeItem, clearAll } = useHistory();
const toast = useToast();
const isOpen = ref(true);

function formatDate(ts: number): string {
  const d = new Date(ts);
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function handleClearAll() {
  if (confirm('هل أنت متأكد من رغبتك في مسح سجل الملفات بالكامل؟')) {
    clearAll();
    toast.info('تم مسح سجل الملفات بنجاح.');
  }
}

function openPreview(item: HistoryItem) {
  emit('preview', item);
  close();
}

function downloadSRT(item: HistoryItem) {
  if (!item.srtContent) return;
  const baseName = item.fileName.replace(/\.[^/.]+$/, '');
  const blob = new Blob([item.srtContent], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${baseName}_translated.srt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  toast.success('تم تنزيل ملف الترجمة بنجاح!');
}

function close() {
  isOpen.value = false;
  emit('close');
}
</script>

<style scoped>
.history-overlay {
  position: fixed;
  inset: 0;
  z-index: 999998;
  background: rgba(6, 11, 25, 0.88);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: fadeIn 0.25s ease-out;
}

.history-modal {
  width: 100%;
  max-width: 680px;
  max-height: 80vh;
  background: #0F172A;
  border: 1px solid #1E293B;
  border-radius: 16px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
  border-bottom: 1px solid #1E293B;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
}

.header-title-box h3 {
  font-size: 16px;
  font-weight: 700;
  color: #F8FAFC;
  margin: 0;
}

.header-title-box p {
  font-size: 11px;
  color: #94A3B8;
  margin: 2px 0 0;
}

.btn-clear {
  background: transparent;
  color: #F87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: #EF4444;
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

.history-body {
  padding: 16px 20px;
  overflow-y: auto;
  max-height: calc(80vh - 80px);
}

.history-empty {
  text-align: center;
  padding: 40px 10px;
  color: #64748B;
}

.empty-icon {
  font-size: 42px;
  margin-bottom: 10px;
  opacity: 0.6;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-card {
  background: #090E1A;
  border: 1px solid #1E293B;
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  transition: all 0.2s;
}

.history-card:hover {
  border-color: #3B82F6;
  background: #111B33;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  flex: 1;
}

.file-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow: hidden;
}

.file-name {
  font-size: 13px;
  font-weight: 700;
  color: #F8FAFC;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-sub {
  font-size: 11px;
  color: #64748B;
  display: flex;
  align-items: center;
  gap: 6px;
}

.lang-tag {
  background: rgba(59, 130, 246, 0.15);
  color: #60A5FA;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.btn-preview {
  background: #1E3A8A;
  color: #93C5FD;
  border: 1px solid #3B82F6;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-preview:hover {
  background: #2563EB;
  color: #FFFFFF;
}

.btn-download {
  background: #064E3B;
  color: #A7F3D0;
  border: 1px solid #10B981;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-download:hover {
  background: #059669;
  color: #FFFFFF;
}

.btn-delete {
  background: transparent;
  color: #64748B;
  border: none;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 0.2s;
}

.btn-delete:hover {
  color: #EF4444;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
