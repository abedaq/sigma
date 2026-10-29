<template>
  <div v-if="isOpen" class="license-overlay" dir="rtl">
    <div class="license-modal">
      <!-- Header -->
      <div class="modal-header">
        <div class="header-icon-box">
          <span class="shield-icon">🛡️</span>
        </div>
        <div class="header-text">
          <h2>تفعيل البرنامج - SIGMA VTT</h2>
          <p>يرجى نسخ بصمة جهازك وإرسالها للمطور للحصول على كود التفعيل المخصص لجهازك.</p>
        </div>
      </div>

      <!-- Body -->
      <div class="modal-body">
        <!-- 1. HWID Section -->
        <div class="form-group">
          <label class="form-label">
            <span>🖥️</span>
            <span>بصمة الجهاز المعتمدة (Hardware ID):</span>
          </label>
          <div class="hwid-container">
            <input
              type="text"
              class="hwid-input"
              :value="hwid || 'جاري استخراج بصمة الجهاز...'"
              readonly
            />
            <button
              class="btn-copy"
              @click="copyHWID"
              :disabled="!hwid || isCopying"
              title="نسخ بصمة الجهاز"
            >
              <span v-if="copied">✅ تم النسخ</span>
              <span v-else>📋 نسخ البصمة</span>
            </button>
          </div>
          <p class="field-hint">
            هذه البصمة فريدة ومبنية على مواصفات اللوحة الأم، المعالج، ونظام التشغيل.
          </p>
        </div>

        <!-- 2. Key Input Section -->
        <div class="form-group">
          <label class="form-label">
            <span>🔑</span>
            <span>كود مفتاح التفعيل (License Key):</span>
          </label>
          <textarea
            v-model="licenseKey"
            class="key-textarea"
            rows="3"
            placeholder="الصق كود مفتاح التفعيل هنا (مثال: SIGMA-LIC-...)"
            :disabled="isActivating"
          ></textarea>
        </div>

        <!-- 3. Verify Button (Under Key Input) -->
        <div class="verify-action-box">
          <button
            class="btn-verify"
            @click="handleActivate"
            :disabled="isActivating || !licenseKey.trim()"
          >
            <span v-if="isActivating" class="spinner">⏳</span>
            <span v-if="isActivating">جاري التحقق والتشفير...</span>
            <span v-else>🔍 التحقق من الرمز وتفعيل البرنامج</span>
          </button>
        </div>

        <!-- Feedback Alert Messages -->
        <div v-if="feedback" :class="['alert-box', feedback.type]">
          <span class="alert-icon">{{ feedback.type === 'success' ? '🎉' : '⚠️' }}</span>
          <div class="alert-content">
            <strong>{{ feedback.title }}</strong>
            <p>{{ feedback.message }}</p>
            <div v-if="feedback.details" class="alert-details">
              <span v-if="feedback.details.client_name">العميل: {{ feedback.details.client_name }} | </span>
              <span v-if="feedback.details.expiry">الصلاحية: {{ feedback.details.expiry }} | </span>
              <span v-if="feedback.details.plan">الباقة: {{ feedback.details.plan }}</span>
            </div>
          </div>
        </div>

        <!-- 4. Contact Buttons (WhatsApp & Telegram) -->
        <div class="contact-section">
          <div class="contact-title">
            <span>💬</span>
            <span>لطلب مفتاح التفعيل أو المساعدة تواصل مع المطور مباشرة:</span>
          </div>
          <div class="contact-buttons-row">
            <!-- WhatsApp Button -->
            <button
              class="btn-contact btn-whatsapp"
              @click="openWhatsApp"
              title="تواصل عبر واتساب"
            >
              <span class="contact-icon">📱</span>
              <div class="contact-info">
                <span class="contact-label">تواصل عبر واتساب</span>
                <span class="contact-sub">WhatsApp Support</span>
              </div>
            </button>

            <!-- Telegram Button -->
            <button
              class="btn-contact btn-telegram"
              @click="openTelegram"
              title="تواصل عبر تلجرام"
            >
              <span class="contact-icon">✈️</span>
              <div class="contact-info">
                <span class="contact-label">تواصل عبر تلجرام</span>
                <span class="contact-sub">Telegram Channel</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- 5. Footer: OK Button (موافق) -->
      <div class="modal-footer">
        <button
          class="btn-ok"
          :class="{ 'btn-ok-active': isAuthorized }"
          @click="handleConfirmOk"
        >
          <span v-if="isAuthorized">موافق - الدخول للبرنامج 🚀</span>
          <span v-else>موافق</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { fetchLicenseStatus, activateLicenseKey, LicenseStatusResponse } from '../services/api';

const props = defineProps<{
  modelValue?: boolean;
}>();

const emit = defineEmits<{
  (e: 'activated', status: LicenseStatusResponse): void;
  (e: 'close'): void;
}>();

const isOpen = ref(true);
const hwid = ref('');
const licenseKey = ref('');
const isCopying = ref(false);
const copied = ref(false);
const isActivating = ref(false);
const isAuthorized = ref(false);

const contactWhatsApp = ref('+967777000000');
const contactTelegram = ref('https://t.me/sigma_support');

interface Feedback {
  type: 'success' | 'error';
  title: string;
  message: string;
  details?: any;
}
const feedback = ref<Feedback | null>(null);

async function loadStatus() {
  const status = await fetchLicenseStatus();
  if (status) {
    hwid.value = status.hwid;
    isAuthorized.value = status.is_authorized;

    if (status.support) {
      if (status.support.whatsapp) contactWhatsApp.value = status.support.whatsapp;
      if (status.support.telegram) contactTelegram.value = status.support.telegram;
    }

    if (status.is_authorized) {
      feedback.value = {
        type: 'success',
        title: 'البرنامج مفعل رسمياً!',
        message: status.message || 'ترخيص جهازك سليم وموثق.',
        details: status.data
      };
    } else if (status.message) {
      feedback.value = {
        type: 'error',
        title: 'التفعيل مطلوب',
        message: status.message
      };
    }
  }
}

async function copyHWID() {
  if (!hwid.value) return;
  try {
    isCopying.value = true;
    await navigator.clipboard.writeText(hwid.value);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
      isCopying.value = false;
    }, 2500);
  } catch (err) {
    isCopying.value = false;
  }
}

async function handleActivate() {
  if (!licenseKey.value.trim()) return;
  isActivating.value = true;
  feedback.value = null;

  try {
    const res = await activateLicenseKey(licenseKey.value.trim());
    if (res.status === 'success') {
      isAuthorized.value = true;
      feedback.value = {
        type: 'success',
        title: 'تم التفعيل بنجاح!',
        message: 'تم التحقق من التوقيع الرقمي وحفظ الترخيص المشفر على جهازك.',
        details: res.data
      };

      // Refresh status and notify parent
      const newStatus = await fetchLicenseStatus();
      if (newStatus) {
        emit('activated', newStatus);
      }
    } else {
      isAuthorized.value = false;
      feedback.value = {
        type: 'error',
        title: 'فشل التفعيل',
        message: res.message || 'المفتاح المدخل غير صالح أو لا يخص هذا الجهاز.'
      };
    }
  } catch (err: any) {
    feedback.value = {
      type: 'error',
      title: 'خطأ في الاتصال',
      message: err.message || 'تعذر التواصل مع محرك التحقق.'
    };
  } finally {
    isActivating.value = false;
  }
}

function handleConfirmOk() {
  if (isAuthorized.value) {
    isOpen.value = false;
    emit('close');
  } else {
    feedback.value = {
      type: 'error',
      title: 'التفعيل إلزامي',
      message: 'لا يمكن استخدام البرنامج بدون تفعيل. يرجى إدخال مفتاح صالح والنقر على زر التحقق أولاً.'
    };
  }
}

function openWhatsApp() {
  let phone = contactWhatsApp.value.replace(/[^0-9]/g, '');
  if (!phone) phone = '967777000000';
  const text = encodeURIComponent(`مرحباً، أود الحصول على كود تفعيل SIGMA VTT لجهازي.\nبصمة الجهاز (HWID): ${hwid.value}`);
  const url = `https://wa.me/${phone}?text=${text}`;
  window.open(url, '_blank');
}

function openTelegram() {
  let url = contactTelegram.value;
  if (!url.startsWith('http')) {
    url = `https://t.me/${url.replace('@', '')}`;
  }
  window.open(url, '_blank');
}

onMounted(() => {
  loadStatus();
});
</script>

<style scoped>
.license-overlay {
  position: fixed;
  inset: 0;
  z-index: 999999;
  background: rgba(8, 12, 22, 0.88);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: fadeIn 0.3s ease-out;
}

.license-modal {
  width: 100%;
  max-width: 640px;
  background: #0F172A;
  border: 1px solid #334155;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(59, 130, 246, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.modal-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border-bottom: 1px solid #1E293B;
}

.header-icon-box {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563EB, #1D4ED8);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 15px rgba(37, 99, 235, 0.4);
}

.shield-icon {
  font-size: 24px;
}

.header-text h2 {
  font-size: 18px;
  font-weight: 700;
  color: #F8FAFC;
  margin: 0 0 4px 0;
}

.header-text p {
  font-size: 12px;
  color: #94A3B8;
  margin: 0;
  line-height: 1.5;
}

/* Body */
.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-height: calc(85vh - 140px);
  overflow-y: auto;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #E2E8F0;
}

.hwid-container {
  display: flex;
  gap: 8px;
}

.hwid-input {
  flex: 1;
  background: #090E1A;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px 14px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  font-weight: 700;
  color: #38BDF8;
  letter-spacing: 0.5px;
  direction: ltr;
  text-align: center;
}

.btn-copy {
  background: #1E293B;
  color: #F8FAFC;
  border: 1px solid #475569;
  border-radius: 8px;
  padding: 0 16px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-copy:hover:not(:disabled) {
  background: #334155;
  border-color: #64748B;
  color: #38BDF8;
}

.field-hint {
  font-size: 11px;
  color: #64748B;
  margin: 0;
}

.key-textarea {
  width: 100%;
  background: #090E1A;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px 14px;
  font-family: monospace;
  font-size: 12px;
  color: #E2E8F0;
  direction: ltr;
  resize: vertical;
  min-height: 70px;
  box-sizing: border-box;
}

.key-textarea:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

/* Verify Action */
.verify-action-box {
  display: flex;
}

.btn-verify {
  width: 100%;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.25s;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-verify:hover:not(:disabled) {
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.45);
  transform: translateY(-1px);
}

.btn-verify:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Alerts */
.alert-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  animation: slideDown 0.2s ease-out;
}

.alert-box.success {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34D399;
}

.alert-box.error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #F87171;
}

.alert-icon {
  font-size: 18px;
}

.alert-content strong {
  display: block;
  font-weight: 700;
  margin-bottom: 2px;
}

.alert-content p {
  margin: 0;
  line-height: 1.4;
}

.alert-details {
  margin-top: 6px;
  font-size: 11px;
  color: #94A3B8;
}

/* Contact Section */
.contact-section {
  background: #090E1A;
  border: 1px solid #1E293B;
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.contact-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #94A3B8;
}

.contact-buttons-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.btn-contact {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  text-align: right;
}

.contact-icon {
  font-size: 20px;
}

.contact-info {
  display: flex;
  flex-direction: column;
}

.contact-label {
  font-size: 13px;
  font-weight: 700;
  color: #FFFFFF;
}

.contact-sub {
  font-size: 10px;
  opacity: 0.8;
}

/* WhatsApp */
.btn-whatsapp {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  border-color: #10B981;
}

.btn-whatsapp:hover {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
  transform: translateY(-1px);
}

/* Telegram */
.btn-telegram {
  background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
  border-color: #38BDF8;
}

.btn-telegram:hover {
  background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%);
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.35);
  transform: translateY(-1px);
}

/* Footer OK button */
.modal-footer {
  padding: 16px 24px;
  background: #090E1A;
  border-top: 1px solid #1E293B;
  display: flex;
  justify-content: flex-end;
}

.btn-ok {
  background: #334155;
  color: #94A3B8;
  border: 1px solid #475569;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ok-active {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  color: #FFFFFF;
  border-color: #34D399;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-ok-active:hover {
  background: linear-gradient(135deg, #34D399 0%, #10B981 100%);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.45);
  transform: translateY(-1px);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
