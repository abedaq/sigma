<template>
  <div class="subtitle-page" dir="rtl">
    <div class="grid-2" style="gap: 16px;">
      <!-- RIGHT: Files & Workspace (Primary Action) -->
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div class="card">
          <div class="card-title"><span>📄</span> مترجم ملفات الترجمة المباشر</div>

          <div class="drop-zone" @click="browseSubFiles" @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="onDropSub" :class="{ 'drag-over': isDragging }">
            <div class="drop-icon">📄</div>
            <h3>اسحب وأفلت ملفات الترجمة هنا أو انقر للاختيار</h3>
            <p>يدعم الصيغ العالمية: (.srt / .vtt / .ass)</p>
          </div>

          <div style="display: flex; gap: 8px; margin-top: 10px;">
            <button class="btn btn-transparent" style="flex: 1;" @click="browseSubFiles">📁 اختيار ملفات</button>
            <button class="btn btn-transparent" style="flex: 1;" @click="browseSubFolder">📂 اختيار مجلد</button>
          </div>

          <!-- Pending Files -->
          <div style="margin-top: 14px; color: #60A5FA; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
            <span>📋 الملفات قيد الانتظار</span>
            <span class="badge-count">{{ pendingFiles.length }}</span>
          </div>
          <div style="max-height: 220px; overflow-y: auto; margin-top: 6px; padding-right: 2px;">
            <div v-for="(file, i) in pendingFiles" :key="file.id" class="file-row">
              <span style="flex: 1; font-size: 12px; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                📄 {{ file.name }} <small style="color: var(--text-dim);">({{ (file.file.size / 1024).toFixed(1) }} KB)</small>
              </span>
              <button class="btn-remove" @click="removePending(i)" title="إزالة">✕</button>
            </div>
            <div v-if="pendingFiles.length === 0" style="text-align: center; padding: 16px 0; color: var(--text-dim); font-size: 12px;">
              لا توجد ملفات قيد الانتظار — أضف ملفات للبدء
            </div>
          </div>

          <!-- Completed Files -->
          <div style="margin-top: 14px; color: #34D399; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
            <span>✅ الملفات المكتملة</span>
            <span class="badge-count" style="background: rgba(52, 211, 153, 0.15); color: #34D399;">{{ completedSubFiles.length }}</span>
          </div>
          <div style="max-height: 140px; overflow-y: auto; margin-top: 6px;">
            <div v-for="(file, i) in completedSubFiles" :key="'cs-' + i" style="padding: 4px 8px; font-size: 12px; color: #34D399; background: rgba(52, 211, 153, 0.08); border-radius: 6px; margin-bottom: 4px;">
              ✅ {{ file }}
            </div>
          </div>
        </div>
      </div>

      <!-- LEFT: Settings & Actions Panel -->
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div class="card">
          <div class="card-title"><span>⚙️</span> إعدادات الترجمة</div>

          <div class="form-group">
            <label for="subEngine">محرك الترجمة:</label>
            <select id="subEngine" v-model="engine" class="form-control">
              <option value="gemini">الذكاء الاصطناعي (Google Gemini AI)</option>
              <option value="gtx">المحرك القياسي السريع (Google GTX)</option>
            </select>
          </div>
          <p style="font-size: 11px; color: var(--text-dim); margin-bottom: 10px; line-height: 1.4;">{{ engineHelper }}</p>

          <div class="form-group">
            <label for="subProfile">ملف التخصيص اللغوي (Profile):</label>
            <select id="subProfile" v-model="profile" class="form-control">
              <option value="auto">تلقائي — ذكي شامل (Auto)</option>
              <option value="general">عام ومحادثات (General)</option>
              <option value="movie">أفلام وسينما ودراما (Cinema / Drama)</option>
              <option value="song">أغاني وشعر وكلمات (Songs / Lyrics)</option>
              <option value="technical">تقني وأكاديمي وعلمي (Technical)</option>
              <option value="anime">أنمي وحواريات يابانية (Anime)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="subTiming">وضع التوقيت والمزامنة (Timing):</label>
            <select id="subTiming" v-model="timing" class="form-control">
              <option value="normal">عادي ومتوازن (Normal)</option>
              <option value="lyrics">أغاني وتزامن إيقاعي (Lyrics)</option>
            </select>
          </div>
          <p v-if="timing === 'lyrics'" style="font-size: 11px; color: #FBBF24; font-weight: 600; margin-bottom: 8px;">
            ⚡ وضع الأغاني يحافظ على قِصر الأسطر وتزامنها مع الغناء بدقة المللي ثانية.
          </p>

          <div class="form-group">
            <label for="subQuality">مستوى المعالجة والجودة (Quality):</label>
            <select id="subQuality" v-model="quality" class="form-control">
              <option value="fast">سريع وفوري (Fast)</option>
              <option value="balanced">متوازن ومحسّن (Balanced)</option>
              <option value="ultra">فائق التدقيق اللغوي (Ultra)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="subTargetLang">اللغة المستهدفة للترجمة:</label>
            <select id="subTargetLang" v-model="targetLang" class="form-control" @change="updateSuffix">
              <option value="ar">العربية (Arabic)</option>
              <option value="en">الإنجليزية (English)</option>
              <option value="fr">الفرنسية (Français)</option>
              <option value="es">الإسبانية (Español)</option>
              <option value="de">الألمانية (Deutsch)</option>
              <option value="ru">الروسية (Русский)</option>
              <option value="zh">الصينية (中文)</option>
              <option value="ja">اليابانية (日本語)</option>
              <option value="ko">الكورية (한국어)</option>
              <option value="tr">التركية (Türkçe)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="subSuffix">لاحقة اسم الملف المترجم:</label>
            <input id="subSuffix" v-model="suffix" class="form-control" style="direction: ltr; text-align: left;" />
          </div>

          <label class="checkbox-styled" style="margin-top: 6px;">
            <input type="checkbox" v-model="bilingualSub" />
            <span style="font-weight: 600;">ترجمة ثنائية اللغة (Bilingual Subtitles)</span>
          </label>

          <div style="margin-top: 10px;">
            <span style="font-size: 12px; color: var(--text-mid); display: inline-block; font-weight: 600; margin-bottom: 4px;">مجلد الحفظ:</span>
            <div style="display: flex; gap: 14px;">
              <label class="radio-styled">
                <input type="radio" v-model="saveMode" value="same" />
                <span>نفس مجلد الملف</span>
              </label>
              <label class="radio-styled">
                <input type="radio" v-model="saveMode" value="custom" />
                <span>مجلد مخصص</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="card" style="display: flex; flex-direction: column; gap: 8px;">
          <button class="btn btn-success" style="height: 46px; font-size: 14px; font-weight: 700;" @click="startTranslation" :disabled="isTranslating || pendingFiles.length === 0">
            {{ isTranslating ? '⏳ جارٍ ترجمة الملفات...' : '🚀 بدء الترجمة الفورية' }}
          </button>
          <button v-if="isTranslating" class="btn btn-danger" style="height: 42px; font-size: 13px;" @click="stopTranslation">
            ⏹️ إيقاف المعالجة
          </button>
        </div>

        <!-- Progress -->
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 13px; font-weight: 700; color: var(--text-main);">مؤشر التقدم</span>
            <span style="font-size: 12px; color: var(--primary-light); font-weight: 700;">{{ transProgress }}%</span>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: transProgress + '%' }"></div>
          </div>
          <div style="font-size: 11px; color: var(--text-dim); margin-top: 6px;">{{ transMessage }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { translateSubtitleFile } from '../services/api';

interface QueueSubItem {
  id: string;
  name: string;
  file: File;
  format: string;
}

const engine = ref('gemini');
const profile = ref('auto');
const timing = ref('normal');
const quality = ref('balanced');
const targetLang = ref('ar');
const suffix = ref('_ar');
const bilingualSub = ref(false);
const saveMode = ref('same');
const isDragging = ref(false);
const isTranslating = ref(false);
const transProgress = ref(0);
const transMessage = ref('جاهز للترجمة');
const pendingFiles = ref<QueueSubItem[]>([]);
const completedSubFiles = ref<string[]>([]);
let cancelTranslationFlag = false;

const engineHelper = computed(() => {
  if (engine.value === 'gemini') return 'Gemini AI: أفضل جودة للترجمة السياقية والشعرية والأفلام بدقة عالية.';
  if (engine.value === 'gtx') return 'Google GTX: محرك مجاني سريع للترجمة الأساسية.';
  return 'Local AI: ترجمة محلية خفيفة بدون إنترنت.';
});

function updateSuffix() {
  const map: Record<string, string> = { ar: '_ar', en: '_en', fr: '_fr', es: '_es', ru: '_ru', zh: '_zh', tr: '_tr' };
  suffix.value = map[targetLang.value] || '_ar';
}

function getFormat(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase();
  return ext === 'vtt' ? 'vtt' : ext === 'ass' ? 'ass' : 'srt';
}

function addFilesToQueue(fileList: FileList | File[]) {
  const allowed = ['.srt', '.vtt', '.ass'];
  Array.from(fileList).forEach(file => {
    const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || '');
    if (allowed.includes(ext)) {
      pendingFiles.value.push({
        id: `${file.name}-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        name: file.name,
        file: file,
        format: getFormat(file.name)
      });
    }
  });
}

function browseSubFiles() {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.accept = '.srt,.vtt,.ass';
  input.onchange = () => {
    if (input.files && input.files.length > 0) {
      addFilesToQueue(input.files);
    }
  };
  input.click();
}

function browseSubFolder() {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  // @ts-ignore
  input.webkitdirectory = true;
  input.onchange = () => {
    if (input.files && input.files.length > 0) {
      addFilesToQueue(input.files);
    }
  };
  input.click();
}

function onDropSub(event: DragEvent) {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    addFilesToQueue(files);
  }
}

function removePending(index: number) {
  pendingFiles.value.splice(index, 1);
}

function downloadTextFile(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

async function startTranslation() {
  if (pendingFiles.value.length === 0 || isTranslating.value) return;
  isTranslating.value = true;
  cancelTranslationFlag = false;
  transProgress.value = 0;
  transMessage.value = 'جاري قراءة الملفات وبدء الترجمة...';

  const total = pendingFiles.value.length;
  let finishedCount = 0;
  const toProcess = [...pendingFiles.value];

  for (let i = 0; i < toProcess.length; i++) {
    if (cancelTranslationFlag) break;
    const item = toProcess[i];
    transMessage.value = `جاري ترجمة (${i + 1}/${total}): ${item.name}`;

    try {
      const rawContent = await item.file.text();
      const translated = await translateSubtitleFile(
        rawContent,
        'auto',
        targetLang.value,
        item.format,
        bilingualSub.value,
        item.name
      );

      if (translated) {
        const dotIdx = item.name.lastIndexOf('.');
        const base = dotIdx !== -1 ? item.name.substring(0, dotIdx) : item.name;
        const ext = dotIdx !== -1 ? item.name.substring(dotIdx) : '.srt';
        const outName = `${base}${suffix.value}${ext}`;

        downloadTextFile(translated, outName);
        completedSubFiles.value.push(outName);
        finishedCount++;
      } else {
        transMessage.value = `فشل ترجمة الملف: ${item.name}`;
      }
    } catch (err) {
      console.error('File translation error:', err);
    }

    transProgress.value = Math.round(((i + 1) / total) * 100);
    // Remove from pending
    const pIdx = pendingFiles.value.findIndex(p => p.id === item.id);
    if (pIdx !== -1) {
      pendingFiles.value.splice(pIdx, 1);
    }
  }

  isTranslating.value = false;
  if (cancelTranslationFlag) {
    transMessage.value = 'تم إيقاف الترجمة بواسطة المستخدم.';
  } else {
    transMessage.value = `اكتملت العملية بنجاح! تم حفظ ${finishedCount} ملف.`;
  }
}

function stopTranslation() {
  cancelTranslationFlag = true;
  isTranslating.value = false;
  transMessage.value = 'تم إيقاف العملية.';
}
</script>

<style scoped>
.subtitle-page {
  padding: 15px;
  height: 100%;
  overflow-y: auto;
}
</style>
