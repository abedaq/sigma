<template>
  <div class="processing-page">
    <!-- Hero Drop Zone with Full-Width Dynamic Audio Waves (Icon Only) -->
    <section class="hero-dropzone-section">
      <div
        class="hero-drop-card"
        @click="browseFiles"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="onDrop"
        :class="{ 'drag-over': isDragging }"
        title="اسحب وأفلت الملفات هنا أو انقر للاختيار"
      >
        <!-- Full-Width Dynamic SVG Audio Waves Background -->
        <div class="full-waveform-bg">
          <svg viewBox="0 0 1200 120" preserveAspectRatio="none" class="full-wave-svg">
            <defs>
              <linearGradient id="neonFullGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#F59E0B" />
                <stop offset="25%" stop-color="#EC4899" />
                <stop offset="50%" stop-color="#8B5CF6" />
                <stop offset="75%" stop-color="#06B6D4" />
                <stop offset="100%" stop-color="#10B981" />
              </linearGradient>
              <linearGradient id="neonFullGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#3B82F6" />
                <stop offset="50%" stop-color="#A855F7" />
                <stop offset="100%" stop-color="#F43F5E" />
              </linearGradient>
              <linearGradient id="neonFullGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#10B981" />
                <stop offset="50%" stop-color="#06B6D4" />
                <stop offset="100%" stop-color="#6366F1" />
              </linearGradient>
            </defs>
            <!-- Wave 1 -->
            <path d="M0 60 C 100 15, 200 105, 300 60 C 400 15, 500 110, 600 55 C 700 0, 800 115, 900 60 C 1000 20, 1100 95, 1200 60" 
                  stroke="url(#neonFullGrad1)" stroke-width="4" stroke-linecap="round" fill="none" class="wave-layer layer-1" />
            <!-- Wave 2 -->
            <path d="M0 60 C 120 95, 240 25, 360 70 C 480 110, 600 10, 720 70 C 840 115, 960 30, 1080 75 C 1140 90, 1180 40, 1200 60" 
                  stroke="url(#neonFullGrad2)" stroke-width="3" stroke-linecap="round" fill="none" class="wave-layer layer-2" opacity="0.8" />
            <!-- Wave 3 -->
            <path d="M0 60 C 150 30, 300 90, 450 40 C 600 100, 750 20, 900 80 C 1050 35, 1150 75, 1200 60" 
                  stroke="url(#neonFullGrad3)" stroke-width="2.5" stroke-linecap="round" fill="none" class="wave-layer layer-3" opacity="0.65" />
          </svg>
        </div>

        <!-- Center Stage: Glowing Icon, Floating Format Badges, and Micro Hint -->
        <div class="dropzone-center-content-box">
          <!-- Left Floating Badges -->
          <div class="floating-badge-group left-badges">
            <span class="floating-format-badge cyan">🎬 MP4</span>
            <span class="floating-format-badge purple">🎥 MKV</span>
          </div>

          <!-- Main Center Action Anchor -->
          <div class="dropzone-core-interactive">
            <div class="hero-upload-icon-glow">
              <span class="upload-icon-symbol">📤</span>
            </div>
            <div class="dropzone-micro-hint">
              <span class="main-hint">اسحب الفيديو أو الصوت هنا للبدء</span>
              <span class="sub-hint">أو اضغط للاستعراض من جهازك</span>
            </div>
          </div>

          <!-- Right Floating Badges -->
          <div class="floating-badge-group right-badges">
            <span class="floating-format-badge pink">🎵 MP3</span>
            <span class="floating-format-badge amber">📄 SRT</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Mid Workspace: Split Panels (Left: Live Progress & Logs | Right: Files & Config) -->
    <div class="proc-grid-layout">
      <!-- Right/Main: Files List & Quick Configuration -->
      <div class="proc-workspace-column">
        <!-- Quick Configuration Strip -->
        <div class="glass-config-strip">
          <div class="strip-header">
            <span>⚙️ إعدادات المعالجة السريعة</span>
          </div>
          <div class="strip-controls">
            <!-- Target Lang -->
            <div class="strip-group">
              <label for="selectLang" class="strip-label">🌐 لغة الترجمة:</label>
              <select id="selectLang" v-model="targetLang" class="strip-select">
                <option value="ar">العربية (Arabic)</option>
                <option value="en">الإنجليزية (English)</option>
                <option value="fr">الفرنسية (Français)</option>
                <option value="es">الإسبانية (Español)</option>
                <option value="de">الألمانية (Deutsch)</option>
                <option value="tr">التركية (Türkçe)</option>
              </select>
            </div>

            <!-- Engine -->
            <div class="strip-group">
              <label for="selectEngine" class="strip-label">🤖 المحرك:</label>
              <select id="selectEngine" v-model="engine" class="strip-select">
                <option value="cloud_auto">⚡ سحابي ذكي (Groq / Gemini)</option>
                <option value="local_onnx">🔒 أوفلاين 100% (ONNX Local)</option>
                <option value="gemini">✨ جوجل جيميني فائق (Gemini Pro)</option>
                <option value="gtx">🌐 Google Translate Engine</option>
              </select>
            </div>

            <!-- Checkbox toggles -->
            <div class="strip-checkboxes">
              <label class="strip-check">
                <input type="checkbox" v-model="keepSrt" />
                <span>حفظ ملف SRT</span>
              </label>
              <label class="strip-check">
                <input type="checkbox" v-model="enableVocalIsolation" />
                <span>🎙️ عزل صوت بشري</span>
              </label>
              <label class="strip-check">
                <input type="checkbox" v-model="enableLyricsGrounding" />
                <span>🎵 مطابقة الكلمات</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Files Management Hub (Queue & Completed) -->
        <div class="files-hub-grid">
          <!-- Queue Column -->
          <div class="files-box glass-card">
            <div class="files-box-header">
              <div class="box-title">
                <span>📋 قائمة الانتظار</span>
                <span class="count-badge amber">{{ queueFiles.length }}</span>
              </div>
              <div class="box-actions">
                <button class="btn-box-action" @click="browseFiles">➕ إضافة ملفات</button>
                <button class="btn-box-action text-danger" @click="clearQueue" :disabled="queueFiles.length === 0">🗑 مسح</button>
              </div>
            </div>
            <div class="files-box-body">
              <div v-for="(file, i) in queueFiles" :key="'q-' + i" class="file-item-card">
                <div class="file-index-pill">{{ i + 1 }}</div>
                <div class="file-details">
                  <span class="file-main-name">{{ file.name }}</span>
                  <span class="file-meta-sub">{{ file.duration || '--:--' }} • {{ file.size || '0 MB' }}</span>
                </div>
                <button class="btn-item-remove" @click="removeFile(i)" title="إزالة من القائمة">✕</button>
              </div>
              <div v-if="queueFiles.length === 0" class="empty-state-text">
                لا توجد ملفات في الانتظار. اسحب ملفاً للأعلى لبدء المعالجة.
              </div>
            </div>
          </div>

          <!-- Completed Column -->
          <div class="files-box glass-card">
            <div class="files-box-header">
              <div class="box-title">
                <span>✅ الملفات المكتملة</span>
                <span class="count-badge green">{{ completedFiles.length }}</span>
              </div>
              <div class="box-actions">
                <button class="btn-box-action" @click="openOutputFolder">📂 فتح المجلد</button>
                <button class="btn-box-action text-danger" @click="clearCompleted" :disabled="completedFiles.length === 0">🗑 مسح</button>
              </div>
            </div>
            <div class="files-box-body">
              <div v-for="(file, i) in completedFiles" :key="'c-' + i" class="file-item-card completed">
                <div class="file-index-pill green">✓</div>
                <div class="file-details">
                  <span class="file-main-name">{{ file.name }}</span>
                  <span class="file-meta-sub text-success">تمت الترجمة والحفظ بنجاح</span>
                </div>
                <button class="btn-item-open" @click="openFile(file)" title="فتح الملف">📂 فتح</button>
              </div>
              <div v-if="completedFiles.length === 0" class="empty-state-text">
                ستظهر الملفات المترجمة والمكتملة هنا فور الانتهاء.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Left: Live Progress, Metrics & System Logs -->
      <div class="proc-metrics-column">
        <!-- Live Progress Status Card -->
        <div class="glass-card live-status-card">
          <div class="status-card-header">
            <span class="status-title">📊 التقدم وحالة المعالجة</span>
            <span class="live-pulse" :class="{ active: isProcessing }"></span>
          </div>

          <!-- Progress Ring & Overall Count -->
          <div class="progress-hero-row">
            <div class="circular-progress-glow">
              <svg viewBox="0 0 70 70">
                <defs>
                  <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#06B6D4" />
                    <stop offset="50%" stop-color="#3B82F6" />
                    <stop offset="100%" stop-color="#10B981" />
                  </linearGradient>
                </defs>
                <circle class="track" cx="35" cy="35" r="28" stroke-width="6" />
                <circle
                  class="fill"
                  cx="35"
                  cy="35"
                  r="28"
                  stroke-width="6"
                  :stroke-dasharray="175.9"
                  :stroke-dashoffset="175.9 - (175.9 * overallProgress / 100)"
                />
              </svg>
              <div class="progress-ring-text">
                <span class="pct">{{ Math.round(overallProgress) }}%</span>
                <span class="lbl">{{ overallLabel }}</span>
              </div>
            </div>

            <div class="metrics-summary-list">
              <div class="metric-row">
                <span class="m-label">الملف الحالي:</span>
                <span class="m-value truncate" :title="currentFileName">{{ currentFileName || '—' }}</span>
              </div>
              <div class="metric-row">
                <span class="m-label">المرحلة:</span>
                <span class="m-value highlight">{{ currentPhase || 'جاهز' }}</span>
              </div>
              <div class="metric-row">
                <span class="m-label">الوقت المنقضي:</span>
                <span class="m-value font-mono">{{ elapsed || '00:00:00' }}</span>
              </div>
            </div>
          </div>

          <!-- Single File Progress Bar -->
          <div class="linear-progress-wrapper" v-if="isProcessing">
            <div class="linear-progress-bar">
              <div class="linear-progress-fill" :style="{ width: fileProgress + '%' }"></div>
            </div>
            <div class="linear-progress-labels">
              <span>تقدم الملف</span>
              <span>{{ fileProgress }}%</span>
            </div>
          </div>
        </div>

        <!-- Live Diagnostics & Terminal Logs -->
        <div class="glass-card live-terminal-card">
          <div class="terminal-header">
            <div class="terminal-dots">
              <span class="dot red"></span>
              <span class="dot yellow"></span>
              <span class="dot green"></span>
            </div>
            <span class="terminal-title">سجل العمليات المباشر</span>
            <span class="terminal-status">{{ isProcessing ? '🟢 جاري المعالجة' : '⚪ خامل' }}</span>
          </div>
          <div class="terminal-body">
            <div v-for="(log, i) in logs" :key="'log-' + i" class="terminal-line">
              <span class="t-icon">{{ log.icon }}</span>
              <span class="t-msg" :style="{ color: log.color }">{{ log.message }}</span>
            </div>
            <div v-if="logs.length === 0" class="terminal-empty">
              بانتظار بدء المعالجة... سجل الأحداث فارغ
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Futuristic Floating Action Dock at Bottom -->
    <div class="floating-action-dock">
      <!-- 🟢 Start Processing / Merge -->
      <button
        class="dock-btn dock-btn-emerald"
        @click="startMerge"
        :disabled="isProcessing || queueFiles.length === 0"
        title="معالجة وترجمة ودمج الفيديو في خطوة واحدة"
      >
        <span v-if="isProcessing && processMode === 'merge'" class="spin-icon">⏳</span>
        <span v-else class="btn-icon">⚡</span>
        <div class="btn-text-block">
          <span class="btn-primary-text">بدء المعالجة والدمج</span>
          <span class="btn-sub-text">فيديو كامل + ترجمة مدمجة</span>
        </div>
      </button>

      <!-- 🟠 Translate & Subtitle Only -->
      <button
        class="dock-btn dock-btn-amber"
        @click="startSrtOnly"
        :disabled="isProcessing || queueFiles.length === 0"
        title="توليد ملفات الترجمة SRT / ASS فقط بسرعة فائقة"
      >
        <span v-if="isProcessing && processMode === 'srt_only'" class="spin-icon">⏳</span>
        <span v-else class="btn-icon">📄</span>
        <div class="btn-text-block">
          <span class="btn-primary-text">ترجمة الفيديوهات فقط</span>
          <span class="btn-sub-text">إخراج ملفات SRT / ASS</span>
        </div>
      </button>

      <!-- 🟣 Stop Processing -->
      <button
        class="dock-btn dock-btn-danger"
        @click="stopProcessing"
        :disabled="!isProcessing"
        title="إيقاف المعالجة الحالية فوراً"
      >
        <span class="btn-icon">⏹</span>
        <div class="btn-text-block">
          <span class="btn-primary-text">إيقاف المعالجة</span>
          <span class="btn-sub-text">إلغاء الدفعة الحالية</span>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { getSessionToken } from '../services/api';
import { useToast } from '../composables/useToast';

const toast = useToast();

// ──────────────────────────────────────────────────────────────────
// أنواع البيانات
// ──────────────────────────────────────────────────────────────────
interface QueueFile {
  name: string;
  path: string;
  duration?: string;
  size?: string;
  file?: File;       // الملف الحقيقي من المتصفح
  outputPath?: string; // مسار الناتج بعد المعالجة
}

interface LogEntry {
  icon: string;
  message: string;
  color: string;
  time: string;
}

// ──────────────────────────────────────────────────────────────────
// حالة الواجهة
// ──────────────────────────────────────────────────────────────────
const targetLang       = ref('ar');
const engine           = ref('cloud_auto');
const processMode      = ref('merge');
const keepSrt          = ref(true);
const keepOriginal     = ref(false);
const bilingual        = ref(false);
const autoDetectMedia  = ref(true);
const enableVocalIsolation = ref(false);
const enableLyricsGrounding = ref(true);

const detectedMediaType  = ref('');
const detectedMediaLabel = ref('');
const detectedConfidence = ref(0);
const fontSize         = ref(15);
const fontColor        = ref('#ffffff');
const isDragging       = ref(false);
const isProcessing     = ref(false);
const overallProgress  = ref(0);
const overallLabel     = ref('جاهز');
const fileProgress     = ref(0);
const currentFileName  = ref('');
const speed            = ref('0.0x');
const remaining        = ref('00:00:00');
const elapsed          = ref('00:00:00');
const statusMessage    = ref('جاهز للمعالجة...');
const currentPhase     = ref('');
const queueFiles       = ref<QueueFile[]>([]);
const completedFiles   = ref<QueueFile[]>([]);
const logs             = ref<LogEntry[]>([]);

// أنواع الملفات المدعومة
const SUPPORTED_TYPES = new Set([
  'video/mp4', 'video/x-matroska', 'video/avi', 'video/quicktime',
  'video/x-msvideo', 'video/webm', 'audio/mpeg', 'audio/wav',
  'audio/mp4', 'audio/ogg', 'audio/flac', 'audio/aac',
  'audio/x-m4a', 'audio/webm',
]);
const SUPPORTED_EXT = /\.(mp4|mkv|avi|mov|mp3|wav|m4a|ogg|flac|aac|webm)$/i;

function addLog(icon: string, message: string, color = '#E2E8F0') {
  const now = new Date();
  logs.value.unshift({
    icon, message, color,
    time: now.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  });
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// ──────────────────────────────────────────────────────────────────
// إضافة ملفات
// ──────────────────────────────────────────────────────────────────
/** تحقق ما إذا كان الملف مدعوماً */
function isSupported(file: File): boolean {
  return SUPPORTED_TYPES.has(file.type) || SUPPORTED_EXT.test(file.name);
}

/** أضف ملفاً للقائمة مع منع التكرار */
function addToQueue(file: File) {
  if (!isSupported(file)) {
    addLog('❌', `نوع غير مدعوم: ${file.name}`, '#FCA5A5');
    return;
  }
  const duplicate = queueFiles.value.some(f => f.name === file.name && f.size === formatBytes(file.size));
  if (duplicate) {
    addLog('⚠️', `الملف موجود بالفعل: ${file.name}`, '#FDE68A');
    return;
  }
  queueFiles.value.push({
    name: file.name,
    path: file.name,
    size: formatBytes(file.size),
    file,
  });
  addLog('📁', `تمت إضافة: ${file.name}`, '#DBEAFE');
}

/** اختيار ملفات بالحوار */
function browseFiles() {
  const input = document.createElement('input');
  input.type     = 'file';
  input.multiple = true;
  input.accept   = '.mp4,.mkv,.avi,.mov,.mp3,.wav,.m4a,.ogg,.flac,.aac,.webm,.srt,.vtt,.ass';

  input.onchange = () => {
    if (!input.files) return;
    Array.from(input.files).forEach(addToQueue);
  };
  input.click();
}

/** اختيار مجلد بالحوار — يضيف كل ملفات الوسائط */
function browseFolder() {
  const input = document.createElement('input');
  input.type      = 'file';
  input.multiple  = true;
  // @ts-ignore - webkitdirectory is non-standard but widely supported
  input.webkitdirectory = true;
  input.onchange = () => {
    if (!input.files) return;
    const mediaFiles = Array.from(input.files).filter(isSupported);
    if (mediaFiles.length === 0) {
      addLog('⚠️', 'لم يتم العثور على ملفات وسائط في المجلد المحدد', '#FDE68A');
      return;
    }
    mediaFiles.forEach(addToQueue);
    addLog('📂', `تمت إضافة ${mediaFiles.length} ملف من المجلد`, '#D1FAE5');
  };
  input.click();
}

/** السحب والإفلات */
function onDrop(event: DragEvent) {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (!files || files.length === 0) return;
  const added = Array.from(files).filter(isSupported);
  const skipped = files.length - added.length;
  added.forEach(addToQueue);
  if (skipped > 0) addLog('⚠️', `تم تخطي ${skipped} ملف غير مدعوم`, '#FDE68A');
}

// ──────────────────────────────────────────────────────────────────
// إدارة القوائم
// ──────────────────────────────────────────────────────────────────
function removeFile(index: number) {
  const removed = queueFiles.value.splice(index, 1);
  if (removed[0]) addLog('🗑', `تمت إزالة: ${removed[0].name}`, '#FEE2E2');
}

function clearQueue() {
  const count = queueFiles.value.length;
  queueFiles.value = [];
  addLog('🗑', `تم مسح قائمة الانتظار (${count} ملف)`, '#FEE2E2');
}

function clearCompleted() {
  const count = completedFiles.value.length;
  completedFiles.value = [];
  addLog('🗑', `تم مسح قائمة المكتملة (${count} ملف)`, '#FEE2E2');
}

/** فتح / تنزيل ملف مكتمل */
function openFile(file: QueueFile) {
  if (file.outputPath) {
    fetch('/api/v1/process/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: file.outputPath })
    }).catch(() => {
        addLog('⚠️', `فشل فتح الملف محلياً. المسار: ${file.outputPath}`, '#FDE68A');
    });
  } else if (file.file) {
    const url = URL.createObjectURL(file.file);
    const a   = document.createElement('a');
    a.href    = url;
    a.target  = '_blank';
    a.rel     = 'noopener';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  } else {
    addLog('⚠️', `لا يمكن فتح الملف مباشرة: ${file.name} — انتقل إلى مجلد الناتج`, '#FDE68A');
  }
}

/** فتح مجلد الناتج */
function openOutputFolder() {
  fetch('/api/v1/process/open-folder', { method: 'POST' })
    .catch(() => addLog('📂', 'الملفات الناتجة محفوظة في مجلد outputs', '#DBEAFE'));
}

// ──────────────────────────────────────────────────────────────────
// المعالجة الحقيقية (API → Backend)
// ──────────────────────────────────────────────────────────────────
let processingInterval: ReturnType<typeof setInterval> | null = null;
let elapsedSeconds = 0;

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600).toString().padStart(2, '0');
  const m = Math.floor((sec % 3600) / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
}

/** تنزيل Blob كملف */
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href     = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

/** استخرج اسم الملف بدون امتداد */
function baseName(name: string): string {
  return name.replace(/\.[^/.]+$/, '');
}

// ──────────────────────────────────────────────────────────────────
// دالة مشتركة — ترسل للـ API وتُنزّل الناتج
// ──────────────────────────────────────────────────────────────────
function formatErrorMessage(err: unknown): string {
  if (err instanceof TypeError && err.message.toLowerCase().includes('fetch')) {
    return '❌ تعذّر الاتصال بالخادم — تأكد أن الخادم شغّال على المنفذ 8000';
  }
  if (err instanceof Error) {
    const m = err.message;
    if (m.includes('401'))      return '🔑 مفتاح API غير صالح أو منتهي الصلاحية';
    if (m.includes('403'))      return '🚫 ليس لديك صلاحية الوصول لهذا الخادم';
    if (m.includes('413'))      return '📦 حجم الملف أكبر من المسموح به';
    if (m.includes('429'))      return '⏱️ تجاوزت حد الطلبات — انتظر قليلاً';
    if (m.includes('500'))      return '🔥 خطأ داخلي في الخادم — راجع الـ Backend';
    if (m.includes('504') || m.includes('timeout')) return '⌛ انتهت مهلة الاتصال — الخادم بطيء';
    return m;
  }
  return 'خطأ غير معروف';
}

async function handleDownloads(result: any, item: QueueFile, mode: 'srt_only' | 'merge') {
  if (result.srt_url) {
    const srtRes  = await fetch(result.srt_url);
    const srtBlob = await srtRes.blob();
    downloadBlob(srtBlob, `${baseName(item.name)}.srt`);
    addLog('📄', `تم تنزيل SRT: ${baseName(item.name)}.srt`, '#D1FAE5');
  } else if (result.srt_content) {
    const srtBlob = new Blob([result.srt_content], { type: 'text/plain;charset=utf-8' });
    downloadBlob(srtBlob, `${baseName(item.name)}.srt`);
    addLog('📄', `تم تنزيل SRT: ${baseName(item.name)}.srt`, '#D1FAE5');
  }

  if (mode === 'merge' && result.video_url) {
    currentPhase.value  = 'تنزيل الفيديو المدموج';
    fileProgress.value  = 92;
    const vidRes  = await fetch(result.video_url);
    const vidBlob = await vidRes.blob();
    const ext     = result.video_url.split('.').pop() || 'mp4';
    downloadBlob(vidBlob, `${baseName(item.name)}_translated.${ext}`);
    addLog('🎬', `تم تنزيل الفيديو: ${baseName(item.name)}_translated.${ext}`, '#D1FAE5');
  }
}

function buildProcessFormData(item: QueueFile, mode: 'srt_only' | 'merge'): FormData {
  const formData = new FormData();
  formData.append('file',        item.file!);
  formData.append('target_lang', targetLang.value);
  formData.append('engine',      engine.value);
  formData.append('mode',        mode);
  formData.append('keep_srt',    String(keepSrt.value));
  formData.append('bilingual',   String(bilingual.value));
  formData.append('font_size',   String(fontSize.value));
  formData.append('font_color',  fontColor.value);
  formData.append('enable_vocal_isolation', String(enableVocalIsolation.value));
  formData.append('auto_detect_media',      String(autoDetectMedia.value));
  formData.append('enable_lyrics_grounding', String(enableLyricsGrounding.value));
  return formData;
}

async function runProcessing(mode: 'srt_only' | 'merge') {
  if (queueFiles.value.length === 0) {
    addLog('⚠️', 'لا توجد ملفات في القائمة — أضف ملفاً أولاً', '#FDE68A');
    return;
  }
  if (isProcessing.value) return;

  processMode.value     = mode;
  isProcessing.value    = true;
  overallProgress.value = 0;
  overallLabel.value    = 'جارٍ...';
  fileProgress.value    = 0;
  elapsedSeconds        = 0;
  elapsed.value         = '00:00:00';
  remaining.value       = '00:00:00';
  speed.value           = '0.0x';
  statusMessage.value   = 'جاري الإعداد...';
  currentPhase.value    = 'تحضير';

  processingInterval = setInterval(() => {
    elapsedSeconds++;
    elapsed.value = formatTime(elapsedSeconds);
  }, 1000);

  const modeLabel = mode === 'srt_only' ? 'ترجمة فقط (SRT)' : 'ترجمة + دمج (فيديو)';
  const total = queueFiles.value.length;
  addLog('🚀', `بدأت معالجة الدفعة [${modeLabel}] لـ ${total} ملفات`, '#DBEAFE');

  const formData = new FormData();
  queueFiles.value.forEach((item) => {
    if (item.file) formData.append('files', item.file);
  });
  formData.append('target_lang', targetLang.value);
  formData.append('engine',      engine.value);
  formData.append('mode',        mode);
  formData.append('keep_srt',               String(keepSrt.value));
  formData.append('bilingual',              String(bilingual.value));
  formData.append('font_size',              String(fontSize.value));
  formData.append('font_color',             fontColor.value);
  formData.append('enable_vocal_isolation', String(enableVocalIsolation.value));
  formData.append('auto_detect_media',      String(autoDetectMedia.value));
  formData.append('enable_lyrics_grounding', String(enableLyricsGrounding.value));

  currentPhase.value = 'رفع الملفات (Batch)';

  let ws: WebSocket | null = null;
  try {
    const response = await fetch('/api/v1/process/batch', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    const batchId = result.batch_id;
    addLog('📦', `تم إنشاء الدفعة بنجاح (${batchId}). جاري المعالجة في الخلفية...`, '#E0F2FE');

    // Connect to WebSocket for real-time event streaming
    try {
      const sessionToken = await getSessionToken();
      if (sessionToken) {
        ws = new WebSocket(`ws://localhost:8000/ws/progress/${sessionToken}`);
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.batch_id === batchId || (data.file_name && !data.batch_id)) {
              if (data.file_name) currentFileName.value = data.file_name;
              if (data.progress_percent !== undefined) fileProgress.value = data.progress_percent;
              if (data.current_step_description) {
                currentPhase.value = data.current_step_description;
                addLog('⚡', `[${data.file_name || 'تقدم'}]: ${data.current_step_description}`, '#E0F2FE');
              }
            }
          } catch {
            // Heartbeat ping/pong or non-json message
          }
        };
      }
    } catch (wsErr) {
      console.warn('WebSocket connection notice:', wsErr);
    }

    // Monitoring for batch completion
    let isBatchCompleted = false;
    let completedCount = 0;
    const doneFiles: QueueFile[] = [];

    while (!isBatchCompleted && isProcessing.value) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const statRes = await fetch(`/api/v1/process/batch/${batchId}`);
      if (!statRes.ok) continue;
      
      const statData = await statRes.json();
      
      const totalF = statData.total_files;
      const comp = statData.completed_files;
      const failed = statData.failed_files;
      
      overallProgress.value = Math.round(((comp + failed) / totalF) * 100);
      statusMessage.value = `معالجة الدفعة: ${comp + failed} / ${totalF}`;
      
      const processingFile = statData.files.find((f: any) => f.status === 'processing' || f.status === 'completed');
      if (processingFile) {
        currentFileName.value = processingFile.original_filename;
        if (!ws) {
          fileProgress.value = processingFile.progress_percent || 50;
          currentPhase.value = processingFile.current_phase || 'جاري المعالجة';
        }
        if (processingFile.detected_media_label) {
          detectedMediaType.value = processingFile.detected_media_type;
          detectedMediaLabel.value = processingFile.detected_media_label;
          detectedConfidence.value = processingFile.detected_confidence;
        }
      }

      if (statData.status === 'completed' || statData.status === 'failed') {
        isBatchCompleted = true;
        statData.files.forEach((f: any) => {
          const qFile = queueFiles.value.find(q => q.name === f.original_filename);
          if (qFile && f.status === 'completed') {
            doneFiles.push({ ...qFile, outputPath: f.result_srt_path });
            addLog('✅', `اكتملت: ${f.original_filename}`, '#D1FAE5');
            
            if (f.result_srt_path) {
                addLog('📄', `ملف الناتج محفوظ في: ${f.result_srt_path}`, '#D1FAE5');
            }
          } else if (f.status === 'failed') {
             addLog('❌', `فشل: ${f.original_filename} - ${f.error_message}`, '#FEE2E2');
          }
        });
      }
    }

    if (ws) {
      try { ws.close(); } catch {}
    }

    // Finish
    if (processingInterval) clearInterval(processingInterval);
    isProcessing.value = false;
    currentPhase.value = doneFiles.length > 0 ? 'مكتمل' : 'فشل';
    overallLabel.value = doneFiles.length > 0 ? 'مكتمل ✅' : 'فشل ❌';
    overallProgress.value = 100;
    speed.value = '—';

    completedFiles.value.push(...doneFiles);
    queueFiles.value = queueFiles.value.filter(
      f => !doneFiles.some(d => d.name === f.name)
    );

    statusMessage.value = `✅ اكتملت الدفعة: ${doneFiles.length} ناجح`;
    addLog('🎉', statusMessage.value, '#D1FAE5');
    if (doneFiles.length > 0) {
      toast.success(statusMessage.value, 'نجاح العملية');
    } else {
      toast.warning('انتهت العملية مع وجود ملفات لم تكتمل', 'تنبيه');
    }

  } catch (err: unknown) {
    if (processingInterval) clearInterval(processingInterval);
    isProcessing.value = false;
    const msg = formatErrorMessage(err);
    addLog('❌', `فشل إنشاء الدفعة: ${msg}`, '#FEE2E2');
    toast.error(`حدث خطأ أثناء المعالجة: ${msg}`, 'خطأ في المعالجة');
  }
}

// ── واجهة الأزرار ─────────────────────────────────────────────────
/** زر "ترجمة فقط" → يُنزّل فقط ملف .srt */
function startSrtOnly() { runProcessing('srt_only'); }

/** زر "ترجمة مع الدمج" → يُنزّل .srt + الفيديو مع الترجمة */
function startMerge()   { runProcessing('merge'); }

function stopProcessing() {
  if (processingInterval) clearInterval(processingInterval);
  isProcessing.value  = false;
  overallLabel.value  = 'متوقف';
  statusMessage.value = 'تم إيقاف المعالجة بواسطة المستخدم';
  currentPhase.value  = '';
  addLog('⏹', 'تم إيقاف المعالجة يدوياً', '#FDE68A');
}


</script>

<style scoped>
.processing-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px 24px;
  gap: 16px;
  overflow-y: auto;
  position: relative;
  background: radial-gradient(circle at 50% 0%, rgba(6, 182, 212, 0.08) 0%, transparent 50%),
              radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
              var(--bg-dark);
}

/* ── Hero Drop Zone ───────────────────────────── */
.hero-dropzone-section {
  width: 100%;
  flex-shrink: 0;
}

.hero-drop-card {
  position: relative;
  border-radius: 16px;
  border: 1px dashed rgba(6, 182, 212, 0.4);
  background: rgba(10, 16, 30, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 28px 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 0 25px rgba(6, 182, 212, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 110px;
}

.hero-drop-card:hover,
.hero-drop-card.drag-over {
  border-color: #38BDF8;
  background: rgba(14, 23, 42, 0.9);
  box-shadow: 0 12px 45px rgba(6, 182, 212, 0.3), inset 0 0 35px rgba(6, 182, 212, 0.2);
  transform: translateY(-2px);
}

/* ── Full Width Dynamic SVG Waves ─────────────── */
.full-waveform-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  z-index: 1;
  opacity: 0.9;
}

.full-wave-svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 12px rgba(6, 182, 212, 0.5));
}

.wave-layer {
  animation: dynamicWave 4s ease-in-out infinite alternate;
}

.layer-1 {
  animation-duration: 3.5s;
}

.layer-2 {
  animation-duration: 4.5s;
  animation-delay: -1s;
}

.layer-3 {
  animation-duration: 5.5s;
  animation-delay: -2s;
}

@keyframes dynamicWave {
  0% {
    transform: scaleY(0.7) translateY(2px);
    opacity: 0.7;
  }
  50% {
    transform: scaleY(1.2) translateY(-2px);
    opacity: 1;
  }
  100% {
    transform: scaleY(0.8) translateY(1px);
    opacity: 0.75;
  }
}

/* ── Center Stage: Icon, Badges & Micro-Hint ─── */
.dropzone-center-content-box {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  width: 100%;
}

.dropzone-core-interactive {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.hero-upload-icon-glow {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.3) 0%, rgba(59, 130, 246, 0.3) 50%, rgba(139, 92, 246, 0.3) 100%);
  border: 1.5px solid rgba(6, 182, 212, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 30px rgba(6, 182, 212, 0.5), inset 0 0 15px rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-drop-card:hover .hero-upload-icon-glow {
  transform: scale(1.12);
  box-shadow: 0 0 45px rgba(6, 182, 212, 0.85), inset 0 0 25px rgba(255, 255, 255, 0.35);
  border-color: #38BDF8;
}

.upload-icon-symbol {
  font-size: 30px;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.4));
}

.dropzone-micro-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  text-align: center;
}

.dropzone-micro-hint .main-hint {
  font-size: 13px;
  font-weight: 700;
  color: #F8FAFC;
  letter-spacing: -0.2px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}

.dropzone-micro-hint .sub-hint {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 500;
}

/* ── Floating Format Badges ───────────────────── */
.floating-badge-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.floating-format-badge {
  font-size: 11px;
  font-weight: 800;
  padding: 4px 12px;
  border-radius: 9999px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  cursor: default;
}

.floating-format-badge:hover {
  transform: translateY(-2px) scale(1.05);
}

.floating-format-badge.cyan {
  background: rgba(6, 182, 212, 0.18);
  color: #38BDF8;
  border: 1px solid rgba(6, 182, 212, 0.45);
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.25);
}

.floating-format-badge.purple {
  background: rgba(139, 92, 246, 0.18);
  color: #C084FC;
  border: 1px solid rgba(139, 92, 246, 0.45);
  box-shadow: 0 0 15px rgba(139, 92, 246, 0.25);
}

.floating-format-badge.pink {
  background: rgba(236, 72, 153, 0.18);
  color: #F472B6;
  border: 1px solid rgba(236, 72, 153, 0.45);
  box-shadow: 0 0 15px rgba(236, 72, 153, 0.25);
}

.floating-format-badge.amber {
  background: rgba(245, 158, 11, 0.18);
  color: #FBBF24;
  border: 1px solid rgba(245, 158, 11, 0.45);
  box-shadow: 0 0 15px rgba(245, 158, 11, 0.25);
}

/* ── Mid Workspace Grid ───────────────────────── */
.proc-grid-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.proc-workspace-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

/* ── Configuration Strip ──────────────────────── */
.glass-config-strip {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strip-header {
  font-size: 12px;
  font-weight: 700;
  color: #CBD5E1;
}

.strip-controls {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.strip-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.strip-label {
  font-size: 11px;
  color: #94A3B8;
  white-space: nowrap;
}

.strip-select {
  background: rgba(10, 16, 30, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #FFFFFF;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-family: inherit;
  outline: none;
}

.strip-select:focus {
  border-color: #38BDF8;
}

.strip-checkboxes {
  display: flex;
  align-items: center;
  gap: 12px;
}

.strip-check {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: #E2E8F0;
  cursor: pointer;
  white-space: nowrap;
}

.strip-check input {
  accent-color: #06B6D4;
}

/* ── Files Hub Grid ───────────────────────────── */
.files-hub-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  flex: 1;
  min-height: 200px;
}

.files-box {
  display: flex;
  flex-direction: column;
  padding: 12px;
  border-radius: 12px;
  min-height: 0;
}

.files-box-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.box-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #F8FAFC;
}

.count-badge {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 9999px;
  font-weight: 800;
}

.count-badge.amber {
  background: rgba(245, 158, 11, 0.2);
  color: #FBBF24;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.count-badge.green {
  background: rgba(16, 185, 129, 0.2);
  color: #34D399;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.box-actions {
  display: flex;
  gap: 6px;
}

.btn-box-action {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #CBD5E1;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.btn-box-action:hover {
  background: rgba(255, 255, 255, 0.12);
}

.btn-box-action.text-danger:hover {
  color: #F87171;
  border-color: rgba(239, 68, 68, 0.4);
}

.files-box-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(10, 16, 30, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.file-index-pill {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: rgba(6, 182, 212, 0.2);
  color: #38BDF8;
  font-size: 10px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-index-pill.green {
  background: rgba(16, 185, 129, 0.2);
  color: #34D399;
}

.file-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.file-main-name {
  font-size: 11px;
  font-weight: 700;
  color: #F1F5F9;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta-sub {
  font-size: 10px;
  color: #64748B;
}

.file-meta-sub.text-success {
  color: #34D399;
}

.btn-item-remove {
  background: transparent;
  border: none;
  color: #94A3B8;
  cursor: pointer;
  font-size: 11px;
  padding: 2px 6px;
}

.btn-item-remove:hover {
  color: #F87171;
}

.btn-item-open {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34D399;
  cursor: pointer;
  font-family: inherit;
}

.empty-state-text {
  text-align: center;
  color: #64748B;
  font-size: 11px;
  padding: 30px 10px;
}

/* ── Metrics Column ───────────────────────────── */
.proc-metrics-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.live-status-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-title {
  font-size: 13px;
  font-weight: 700;
  color: #FFFFFF;
}

.live-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748B;
}

.live-pulse.active {
  background: #10B981;
  box-shadow: 0 0 10px #10B981;
  animation: pulseAnim 1.5s infinite;
}

@keyframes pulseAnim {
  0% { opacity: 0.6; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.2); }
  100% { opacity: 0.6; transform: scale(0.9); }
}

.progress-hero-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.circular-progress-glow {
  position: relative;
  width: 72px;
  height: 72px;
  flex-shrink: 0;
}

.circular-progress-glow svg {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.circular-progress-glow .track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.08);
}

.circular-progress-glow .fill {
  fill: none;
  stroke: url(#neonGradient);
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
}

.progress-ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.progress-ring-text .pct {
  font-size: 14px;
  font-weight: 900;
  color: #FFFFFF;
}

.progress-ring-text .lbl {
  font-size: 9px;
  color: #94A3B8;
}

.metrics-summary-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
}

.m-label {
  color: #94A3B8;
}

.m-value {
  font-weight: 700;
  color: #F8FAFC;
}

.m-value.highlight {
  color: #38BDF8;
}

.linear-progress-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.linear-progress-bar {
  height: 6px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.linear-progress-fill {
  height: 100%;
  border-radius: 9999px;
  background: linear-gradient(90deg, #06B6D4 0%, #10B981 100%);
  transition: width 0.3s ease;
}

.linear-progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #94A3B8;
}

/* ── Live Terminal Logs ───────────────────────── */
.live-terminal-card {
  flex: 1;
  min-height: 140px;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 6px;
}

.terminal-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.red { background: #EF4444; }
.dot.yellow { background: #F59E0B; }
.dot.green { background: #10B981; }

.terminal-title {
  font-size: 11px;
  font-weight: 700;
  color: #CBD5E1;
}

.terminal-status {
  font-size: 10px;
  color: #94A3B8;
}

.terminal-body {
  flex: 1;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.terminal-line {
  display: flex;
  align-items: baseline;
  gap: 6px;
  line-height: 1.4;
}

.terminal-empty {
  text-align: center;
  color: #64748B;
  font-size: 10px;
  padding: 20px 0;
}

/* ── Floating Action Dock (Bottom) ────────────── */
.floating-action-dock {
  position: sticky;
  bottom: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 10px 20px;
  background: rgba(10, 16, 30, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  z-index: 50;
  margin-top: auto;
}

.dock-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 24px;
  border-radius: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.dock-btn .btn-icon {
  font-size: 20px;
}

.dock-btn .btn-text-block {
  display: flex;
  flex-direction: column;
  text-align: right;
}

.dock-btn .btn-primary-text {
  font-size: 13px;
  font-weight: 800;
}

.dock-btn .btn-sub-text {
  font-size: 10px;
  opacity: 0.8;
}

.dock-btn-emerald {
  background: linear-gradient(135deg, #059669 0%, #10B981 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
  border-color: rgba(52, 211, 153, 0.4);
}

.dock-btn-emerald:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(16, 185, 129, 0.6);
}

.dock-btn-amber {
  background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.4);
  border-color: rgba(251, 191, 36, 0.4);
}

.dock-btn-amber:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(245, 158, 11, 0.6);
}

.dock-btn-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #F87171;
  border-color: rgba(239, 68, 68, 0.3);
}

.dock-btn-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.3);
  transform: translateY(-2px);
}

.dock-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}
</style>
