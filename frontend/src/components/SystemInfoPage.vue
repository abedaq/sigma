<template>
  <div class="system-info-page" dir="rtl">
    <!-- Toast Notification -->
    <transition name="toast-slide">
      <div v-if="toast" class="sigma-toast" :class="toast.type">
        <span>{{ toast.msg }}</span>
      </div>
    </transition>

    <!-- Header -->
    <div class="page-header">
      <div class="header-title-box">
        <div class="header-icon-badge">🖥️</div>
        <div>
          <h2>مؤشرات العتاد وتشخيص الأخطاء المباشر</h2>
          <p>مراقبة موارد النظام وعتاد المعالجة وتسجيل الأخطاء البرمجية اللحظي</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="refreshAll" :disabled="loading">
          <span :class="{ 'spin-icon': loading }">🔄</span>
          <span>{{ loading ? 'جارٍ الفحص...' : 'تحديث المؤشرات' }}</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !info" class="loading-state card">
      <div class="loading-spinner"></div>
      <p>جارٍ فحص عتاد وموارد الجهاز عبر النواة...</p>
    </div>

    <div v-else class="system-content-wrapper">
      <!-- Hardware Metrics Grid -->
      <div v-if="info" class="info-grid">
        <!-- Card 1: المعالج (CPU) -->
        <div class="card stat-card hardware-card">
          <div class="card-icon cpu-icon">⚡</div>
          <div class="card-content">
            <div class="stat-title">المعالج الرئيسي (CPU)</div>
            <div class="stat-main">{{ info.cpu_name }}</div>
            <div class="stat-meta">
              <div class="meta-row">
                <span>الأنوية الفيزيائية:</span>
                <strong>{{ info.cpu_cores_physical }} Cores</strong>
              </div>
              <div class="meta-row">
                <span>المسارات المنطقية:</span>
                <strong>{{ info.cpu_cores_logical }} Threads</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 2: الذاكرة العشوائية (RAM) -->
        <div class="card stat-card hardware-card">
          <div class="card-icon ram-icon">🧠</div>
          <div class="card-content">
            <div class="stat-title">الذاكرة العشوائية (RAM)</div>
            <div class="stat-main">{{ (info.ram_total_gb - info.ram_available_gb).toFixed(1) }} GB / {{ info.ram_total_gb }} GB مستهلكة</div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: ramUsedPercent + '%' }"></div>
            </div>
            <div class="stat-meta" style="margin-top: 8px;">
              <div class="meta-row">
                <span>المتبقي متاح:</span>
                <strong style="color: #34D399;">{{ info.ram_available_gb }} GB</strong>
              </div>
              <div class="meta-row">
                <span>نسبة الاستهلاك:</span>
                <strong :style="{ color: ramUsedPercent > 85 ? '#EF4444' : '#60A5FA' }">{{ ramUsedPercent }}%</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 3: معالجة الذكاء الاصطناعي (AI Acceleration) -->
        <div class="card stat-card hardware-card">
          <div class="card-icon ai-icon">🚀</div>
          <div class="card-content">
            <div class="stat-title">تسريع الذكاء الاصطناعي (AI Runtime)</div>
            <div class="stat-main neon-text">ONNX Runtime (DirectML / CPU)</div>
            <div class="stat-meta">
              <div class="meta-row">
                <span>سياسة PyTorch:</span>
                <strong class="badge-tag-safe">محظورة بنجاح (Zero-PyTorch) 🛡️</strong>
              </div>
              <div class="meta-row">
                <span>عزل الغناء:</span>
                <strong>UVR MDX-Net ONNX</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 4: نظام التشغيل والبيئة (OS & Runtime) -->
        <div class="card stat-card hardware-card">
          <div class="card-icon os-icon">🪟</div>
          <div class="card-content">
            <div class="stat-title">نظام التشغيل والبيئة</div>
            <div class="stat-main">{{ info.os_name }}</div>
            <div class="stat-meta">
              <div class="meta-row">
                <span>إصدار Python:</span>
                <strong>{{ info.python_version }}</strong>
              </div>
              <div class="meta-row">
                <span>إصدار التطبيق:</span>
                <strong>v{{ info.app_version }}</strong>
              </div>
              <div class="meta-row">
                <span>محرك FFmpeg:</span>
                <strong style="color: #34D399;">جاهز ومفعل 🎬</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Live Diagnostics & Error Telemetry Console -->
      <div class="card diagnostics-console-card">
        <div class="console-header">
          <div class="console-title">
            <span class="pulse-indicator"></span>
            <span style="font-size: 16px;">📊</span>
            <h4>لوحة تشخيص ومراقبة الأخطاء اللحظية (Diagnostic & Error Telemetry)</h4>
            <span class="log-count-badge">{{ debugLogs.length }} حدث مسجل</span>
          </div>
          <div class="console-actions">
            <button class="btn btn-copy-report" @click="copyReportForAI" :disabled="debugLogs.length === 0" title="نسخ السجل المشفر كاملاً لإرساله للذكاء الاصطناعي لتشخيص أي خطأ فوراً">
              <span>📋</span>
              <span>نسخ التقرير للذكاء الاصطناعي</span>
            </button>
            <button class="btn btn-clear-logs" @click="handleClearLogs" :disabled="debugLogs.length === 0" title="تفريغ سجل الأحداث">
              <span>🗑️</span>
              <span>مسح</span>
            </button>
            <button class="btn btn-refresh-logs" @click="loadLogs" :disabled="loadingLogs" title="إعادة تحميل السجل">
              <span :class="{ 'spin-icon': loadingLogs }">🔄</span>
            </button>
          </div>
        </div>

        <div class="console-log-body">
          <div v-if="debugLogs.length === 0" class="console-empty-state">
            <div style="font-size: 32px; margin-bottom: 8px;">✨</div>
            <p>لا توجد أخطاء أو استثناءات مسجلة حتى الآن — جميع المحركات تعمل بسلاسة تامة!</p>
          </div>

          <div v-else class="console-logs-list">
            <div v-for="log in debugLogs" :key="log.id" class="log-entry" :class="'level-' + (log.level || 'INFO').toLowerCase()">
              <div class="log-header-row">
                <span class="level-badge" :class="'badge-' + (log.level || 'INFO').toLowerCase()">
                  {{ log.level }}
                </span>
                <span class="log-module-name">[{{ log.module }}]</span>
                <span class="log-time-stamp">{{ log.timestamp }}</span>
              </div>
              <div class="log-message-text">{{ log.message }}</div>
              <div v-if="log.exception" class="log-exception-block">
                <strong>Exception:</strong> {{ log.exception }}
              </div>
              <pre v-if="log.traceback" class="log-traceback-block"><code>{{ log.traceback }}</code></pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { fetchHardwareInfo, fetchDebugLogs, clearDebugLogs, DebugLogItem } from '../services/api';
import { SystemHardwareInfo } from '../types';

const info = ref<SystemHardwareInfo | null>(null);
const loading = ref(false);
const debugLogs = ref<DebugLogItem[]>([]);
const loadingLogs = ref(false);

const toast = ref<{ msg: string; type: 'success' | 'error' | 'info' } | null>(null);
let toastTimer: any = null;

function showToast(msg: string, type: 'success' | 'error' | 'info' = 'info') {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = { msg, type };
  toastTimer = setTimeout(() => {
    toast.value = null;
  }, 3500);
}

const ramUsedPercent = computed(() => {
  if (!info.value || info.value.ram_total_gb <= 0) return 0;
  const used = info.value.ram_total_gb - info.value.ram_available_gb;
  return Math.min(100, Math.max(0, Math.round((used / info.value.ram_total_gb) * 100)));
});

async function loadInfo() {
  loading.value = true;
  try {
    const res = await fetchHardwareInfo();
    if (res) {
      info.value = res;
    }
  } catch (err) {
    console.error('Failed to load hardware info:', err);
  } finally {
    loading.value = false;
  }
}

async function loadLogs() {
  loadingLogs.value = true;
  try {
    const logs = await fetchDebugLogs(60);
    debugLogs.value = logs;
  } catch (err) {
    console.error('Failed to load debug logs:', err);
  } finally {
    loadingLogs.value = false;
  }
}

async function refreshAll() {
  await Promise.all([loadInfo(), loadLogs()]);
  showToast('تم تحديث مؤشرات العتاد وسجل التشخيص بنجاح', 'success');
}

async function handleClearLogs() {
  const success = await clearDebugLogs();
  if (success) {
    debugLogs.value = [];
    showToast('تم تفريغ سجل التشخيص بنجاح', 'info');
  } else {
    showToast('تعذر تفريغ السجل', 'error');
  }
}

async function copyReportForAI() {
  if (debugLogs.value.length === 0) return;
  
  const reportHeader = `=== SIGMA_ASR_VTT DIAGNOSTIC ERROR REPORT ===\nGenerated at: ${new Date().toISOString()}\nOS: ${info.value?.os_name || 'Windows'}\nPython: ${info.value?.python_version || '3.11'}\nRAM: ${info.value?.ram_available_gb}GB free / ${info.value?.ram_total_gb}GB total\nAI Runtime: ONNX DirectML (Zero-PyTorch Policy Active)\nTotal Events: ${debugLogs.value.length}\n=============================================\n\n`;
  
  const logsText = debugLogs.value.map((l, i) => {
    let entry = `[#${i + 1}] [${l.timestamp}] [${l.level}] [${l.module}]: ${l.message}\n`;
    if (l.exception) entry += `  Exception: ${l.exception}\n`;
    if (l.traceback) entry += `  Traceback:\n${l.traceback}\n`;
    return entry;
  }).join('\n---------------------------------------------\n');

  const fullReport = reportHeader + logsText;

  try {
    await navigator.clipboard.writeText(fullReport);
    showToast('📋 تم نسخ تقرير التشخيص بالكامل إلى الحافظة! يمكنك لصقه مباشرة للذكاء الاصطناعي.', 'success');
  } catch (err) {
    console.error('Clipboard error:', err);
    showToast('فشل النسخ إلى الحافظة تلقائياً', 'error');
  }
}

onMounted(() => {
  loadInfo();
  loadLogs();
});
</script>

<style scoped>
.system-info-page {
  padding: 16px 20px;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  direction: rtl;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-card);
  flex-shrink: 0;
}

.header-title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-badge {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.2));
  border: 1px solid rgba(59, 130, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.header-title-box h2 {
  font-size: 18px;
  font-weight: 800;
  color: #FFFFFF;
  margin: 0;
}

.header-title-box p {
  font-size: 12px;
  color: var(--text-dim);
  margin: 2px 0 0;
}

.system-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.hardware-card {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  transition: all 0.25s ease;
}

.hardware-card:hover {
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.card-icon {
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.cpu-icon { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); }
.ram-icon { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); }
.ai-icon { background: rgba(236, 72, 153, 0.15); border: 1px solid rgba(236, 72, 153, 0.3); }
.os-icon { background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.3); }

.card-content {
  flex: 1;
  min-width: 0;
}

.stat-title {
  font-size: 11.5px;
  color: var(--text-dim);
  margin-bottom: 4px;
  font-weight: 600;
}

.stat-main {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.neon-text {
  color: #34D399;
}

.stat-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11.5px;
  color: var(--text-dim);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta-row strong {
  color: var(--text-mid);
}

.badge-tag-safe {
  color: #60A5FA !important;
  background: rgba(59, 130, 246, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10.5px;
}

/* ── Live Diagnostics & Telemetry Console ── */
.diagnostics-console-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 320px;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.console-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.console-title h4 {
  font-size: 14px;
  font-weight: 700;
  color: #FFFFFF;
  margin: 0;
}

.pulse-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px #10B981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.log-count-badge {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-mid);
  padding: 2px 8px;
  border-radius: 10px;
}

.console-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-copy-report {
  background: linear-gradient(135deg, #3B82F6, #6366F1);
  color: #FFFFFF;
  border: none;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  font-family: inherit;
}

.btn-copy-report:hover:not(:disabled) {
  box-shadow: var(--shadow-glow);
  transform: translateY(-1px);
}

.btn-clear-logs {
  background: rgba(239, 68, 68, 0.15);
  color: #EF4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
  font-family: inherit;
}

.btn-clear-logs:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.25);
}

.btn-refresh-logs {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-card);
  color: var(--text-mid);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.console-log-body {
  background: #060B16;
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius-sm);
  padding: 12px;
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
  font-family: var(--font-mono);
}

.console-empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-dim);
  font-size: 12.5px;
  font-family: var(--font-family);
}

.console-logs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-entry {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-right: 3px solid #3B82F6;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 11.5px;
}

.log-entry.level-error, .log-entry.level-critical {
  border-right-color: #EF4444;
  background: rgba(239, 68, 68, 0.08);
}

.log-entry.level-warning {
  border-right-color: #F59E0B;
  background: rgba(245, 158, 11, 0.08);
}

.log-entry.level-info {
  border-right-color: #3B82F6;
}

.log-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.level-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.badge-error, .badge-critical { background: rgba(239, 68, 68, 0.2); color: #FCA5A5; }
.badge-warning { background: rgba(245, 158, 11, 0.2); color: #FCD34D; }
.badge-info { background: rgba(59, 130, 246, 0.2); color: #93C5FD; }

.log-module-name {
  color: var(--text-dim);
  font-size: 10.5px;
}

.log-time-stamp {
  margin-right: auto;
  color: var(--text-muted);
  font-size: 10px;
}

.log-message-text {
  color: #E2E8F0;
  line-height: 1.4;
  font-family: var(--font-family);
  word-break: break-word;
}

.log-exception-block {
  margin-top: 4px;
  color: #F87171;
  font-size: 11px;
}

.log-traceback-block {
  margin-top: 6px;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 4px;
  padding: 8px;
  color: #FCA5A5;
  font-size: 10.5px;
  overflow-x: auto;
  direction: ltr;
  text-align: left;
}

.spin-icon {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sigma-toast {
  position: fixed;
  bottom: 24px;
  left: 24px;
  padding: 10px 18px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  z-index: 9999;
  box-shadow: 0 10px 25px rgba(0,0,0,0.4);
}

.sigma-toast.success { background: #065F46; color: #6EE7B7; border: 1px solid #10B981; }
.sigma-toast.error { background: #991B1B; color: #FCA5A5; border: 1px solid #EF4444; }
.sigma-toast.info { background: #1E3A8A; color: #93C5FD; border: 1px solid #3B82F6; }

.toast-slide-enter-active, .toast-slide-leave-active {
  transition: all 0.3s ease;
}
.toast-slide-enter-from, .toast-slide-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
