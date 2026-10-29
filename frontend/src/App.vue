<template>
  <div class="app-container" :class="{ 'light-mode': !isDarkMode }" dir="rtl">
    <!-- Modern Top Navigation Bar (Header) -->
    <header class="top-nav-bar">
      <!-- Right: App Branding -->
      <div class="top-nav-brand">
        <div class="top-logo-icon">Σ</div>
        <div class="top-logo-text">
          <span class="brand-title">SIGMA ASR VTT</span>
          <span class="brand-badge">v3.0.0 Pro Studio</span>
        </div>
      </div>

      <!-- Center: Navigation Tabs -->
      <nav class="top-nav-links">
        <button
          v-for="nav in navItems"
          :key="nav.key"
          class="top-nav-tab"
          :class="{ active: activePage === nav.key }"
          @click="activePage = nav.key"
        >
          <span class="nav-tab-icon">{{ nav.icon }}</span>
          <span class="nav-tab-label">{{ nav.label }}</span>
          <div v-if="activePage === nav.key" class="active-glow-pill"></div>
        </button>
      </nav>

      <!-- Left: Quick Actions & Status -->
      <div class="top-nav-actions">
        <!-- License Pill -->
        <button class="top-action-pill license-pill" @click="showLicenseModal = true" title="إدارة الترخيص">
          <span>🛡️</span>
          <span class="pill-label">الترخيص:</span>
          <span :class="isLicenseActive ? 'badge-pill-on' : 'badge-pill-off'">
            {{ isLicenseActive ? 'مفعّل' : 'تفعيل' }}
          </span>
        </button>

        <!-- Theme Toggle -->
        <button class="top-action-pill theme-pill" @click="toggleTheme" title="تبديل النمط">
          <span>{{ isDarkMode ? '🌙' : '☀️' }}</span>
        </button>

        <!-- Language Toggle -->
        <button class="top-action-pill lang-pill" @click="toggleLang" title="تغيير اللغة">
          <span>🌐</span>
          <span>{{ currentLang === 'ar' ? 'AR' : 'EN' }}</span>
        </button>
      </div>
    </header>

    <!-- Main Workspace Content -->
    <main class="main-content">
      <ProcessingPage v-if="activePage === 'processing'" />
      <SubtitlePage v-if="activePage === 'sub_translator'" />
      <SettingsPage v-if="activePage === 'settings'" />
      <SystemInfoPage v-if="activePage === 'hardware'" />
      <AboutPage v-if="activePage === 'about'" />
    </main>

    <!-- License Lock Screen -->
    <LicenseLockModal
      v-if="showLicenseModal"
      @activated="onLicenseActivated"
      @close="onModalClose"
    />

    <!-- Global Toast Notifications -->
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import ProcessingPage from './components/ProcessingPage.vue';
import SubtitlePage from './components/SubtitlePage.vue';
import SettingsPage from './components/SettingsPage.vue';
import SystemInfoPage from './components/SystemInfoPage.vue';
import AboutPage from './components/AboutPage.vue';
import LicenseLockModal from './components/LicenseLockModal.vue';
import ToastContainer from './components/ToastContainer.vue';
import { fetchLicenseStatus } from './services/api';

const activePage = ref('processing');
const isDarkMode = ref(true);
const currentLang = ref<'ar' | 'en'>('ar');
const showLicenseModal = ref(true);
const isLicenseActive = ref(false);

async function checkLicense() {
  const status = await fetchLicenseStatus();
  if (status) {
    isLicenseActive.value = status.is_authorized;
    if (status.is_authorized) {
      showLicenseModal.value = false;
    } else {
      showLicenseModal.value = true;
    }
  } else {
    showLicenseModal.value = true;
  }
}

function onLicenseActivated() {
  isLicenseActive.value = true;
  showLicenseModal.value = false;
}

function onModalClose() {
  if (isLicenseActive.value) {
    showLicenseModal.value = false;
  }
}

onMounted(() => {
  checkLicense();
});

function toggleTheme() {
  isDarkMode.value = !isDarkMode.value;
  if (!isDarkMode.value) {
    document.documentElement.classList.add('light-theme');
  } else {
    document.documentElement.classList.remove('light-theme');
  }
}

function toggleLang() {
  currentLang.value = currentLang.value === 'ar' ? 'en' : 'ar';
}

const navItems = [
  { key: 'processing', icon: '🎬', label: 'المعالجة' },
  { key: 'sub_translator', icon: '📄', label: 'مترجم الملفات' },
  { key: 'settings', icon: '⚙️', label: 'الإعدادات' },
  { key: 'hardware', icon: '🖥️', label: 'معلومات الجهاز' },
  { key: 'about', icon: 'ℹ️', label: 'حول' },
];
</script>

<style scoped>
.top-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
  background: rgba(10, 16, 30, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  height: 64px;
  flex-shrink: 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.top-nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 50%, #8B5CF6 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 900;
  color: #fff;
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
}

.top-logo-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 16px;
  font-weight: 800;
  color: #F8FAFC;
  letter-spacing: 0.5px;
}

.brand-badge {
  font-size: 10px;
  color: #38BDF8;
  font-weight: 600;
}

.top-nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(15, 23, 42, 0.6);
  padding: 5px 8px;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.top-nav-tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 9999px;
  background: transparent;
  border: none;
  color: #94A3B8;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.top-nav-tab:hover {
  color: #F8FAFC;
  background: rgba(255, 255, 255, 0.05);
}

.top-nav-tab.active {
  color: #FFFFFF;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(139, 92, 246, 0.25) 100%);
  border: 1px solid rgba(59, 130, 246, 0.4);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);
}

.top-nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.top-action-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 6px 12px;
  border-radius: 9999px;
  color: #CBD5E1;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.top-action-pill:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.badge-pill-on {
  background: rgba(16, 185, 129, 0.2);
  color: #34D399;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: bold;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.badge-pill-off {
  background: rgba(239, 68, 68, 0.2);
  color: #F87171;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: bold;
  border: 1px solid rgba(239, 68, 68, 0.4);
}
</style>

