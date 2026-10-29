<template>
  <div class="about-page">
    <!-- Header -->
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
      <span style="flex: 1;"></span>
      <span style="color: #fff; font-size: 16px; font-weight: bold;">Sigma VTT</span>
      <span>ℹ️</span>
    </div>

    <!-- Hero Banner -->
    <div class="hero-banner">
      <div class="hero-logo">Σ</div>
      <div class="hero-info" style="flex: 1;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <h2>Sigma VTT</h2>
          <span class="badge badge-primary">الإصدار 3.0.0</span>
        </div>
        <p class="subtitle">ذكاء اصطناعي يحول الفيديو إلى ترجمة احترافية بدقة عالية</p>
        <p class="description">
          Sigma VTT هو تطبيق مكتبي متقدم يعتمد على الذكاء الاصطناعي لتحويل ملفات الفيديو والصوت إلى ترجمات دقيقة وسريعة. يدعم أكثر من لغة ويقدم أدوات احترافية للمراجعة والتعديل والتصدير بجودة عالية.
        </p>
      </div>
      <div class="hero-sigma">Σ</div>
    </div>

    <!-- Development Team -->
    <div style="display: flex; align-items: center; gap: 8px; margin: 28px 0 16px;">
      <span style="font-size: 20px;">👥</span>
      <span style="color: #60A5FA; font-size: 22px; font-weight: bold;">فريق التطوير</span>
    </div>

    <div class="grid-4">
      <div v-for="dev in team" :key="dev.name" class="hover-card dev-card">
        <div class="dev-top">
          <div style="flex: 1; text-align: right;">
            <div class="dev-name">{{ dev.name }}</div>
            <div class="dev-role" :style="{ color: dev.color }">{{ dev.role }}</div>
          </div>
          <div class="dev-avatar" :style="{ border: '2px solid ' + dev.color + '77' }">{{ dev.icon }}</div>
        </div>
        <div class="dev-desc">{{ dev.desc }}</div>
      </div>
    </div>

    <!-- Contributors Section -->
    <div class="section-container" style="margin-top: 28px;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 18px;">
        <span style="font-size: 18px;">❤️</span>
        <span style="color: #E2E8F0; font-size: 18px; font-weight: bold;">المساهمون والداعمون</span>
      </div>

      <div class="grid-5">
        <div v-for="c in contributors" :key="c.name" class="hover-card contrib-card">
          <div style="flex: 1; text-align: right;">
            <div class="contrib-name">{{ c.name }}</div>
            <div class="contrib-role">{{ c.role }}</div>
          </div>
          <div class="contrib-icon" :style="{ border: '2px solid ' + c.color + '66' }">{{ c.icon }}</div>
        </div>
      </div>

      <div style="text-align: center; margin-top: 16px;">
        <div style="color: #fff; font-size: 24px; font-weight: bold;">شكراً لجميع المساهمين والداعمين لمشروع سيجما VTT!</div>
        <div style="color: #64748B; font-size: 14px; margin-top: 6px;">شكراً لكل من ساهم في دعم هذا المشروع وتطويره.</div>
      </div>
    </div>

    <!-- Contact Section -->
    <div style="display: flex; align-items: center; gap: 8px; margin: 28px 0 8px; justify-content: flex-end;">
      <span style="color: #3B82F6; font-size: 18px; font-weight: bold;">التواصل</span>
      <span>✈️</span>
    </div>
    <p style="text-align: right; color: #9CA3AF; font-size: 13px; margin-bottom: 12px;">نسعد بتواصلكم معنا لأي استفسار أو اقتراح أو دعم.</p>

    <div style="display: flex; gap: 20px;">
      <a href="mailto:support@sigmavtt.com" class="hover-card contact-card" style="flex: 1; text-decoration: none;">
        <div style="text-align: center;">
          <div class="contact-title">البريد الإلكتروني</div>
          <div class="contact-value">support@sigmavtt.com</div>
        </div>
        <span class="contact-icon">📧</span>
      </a>
      <a href="https://t.me/SigmaVTT" target="_blank" class="hover-card contact-card" style="flex: 1; text-decoration: none;">
        <div style="text-align: center;">
          <div class="contact-title">تليجرام</div>
          <div class="contact-value">@SigmaVTT</div>
        </div>
        <span class="contact-icon">💬</span>
      </a>
    </div>

    <!-- Footer -->
    <div style="text-align: center; margin-top: 20px; display: flex; align-items: center; justify-content: center; gap: 6px;">
      <span style="color: #4B5563; font-size: 12px;">جميع الحقوق محفوظة © Sigma VTT 2023-2026</span>
      <span style="font-size: 10px;">🟢</span>
    </div>
  </div>
</template>

<script setup lang="ts">
const team = [
  { icon: '👑', name: 'أشرف منصور سلطان', role: 'المدير والمطور الرئيسي', desc: 'المؤسس والمطور الرئيسي للمشروع، يقود الرؤية التقنية والاستراتيجية.', color: '#FACC15' },
  { icon: '💻', name: 'عبدالرحمن أحمد محمد عقل', role: 'المبرمج والمصمم', desc: 'مطور ومصمم واجهات وتجربة المستخدم، شغوف ببناء حلول محكمة ومتقنة.', color: '#EF4444' },
  { icon: '🎨', name: 'أنور عبد العالم', role: 'مصمم واجهات', desc: 'مصمم واجهات وتجربة مستخدم محترف، يعمل على تحسين المظهر الجمالي وسهولة الاستخدام.', color: '#A855F7' },
  { icon: '🔧', name: 'أمجد صادق الشلبي', role: 'الدعم وصيانة النظام', desc: 'متخصص في دعم الأنظمة وضمان استقرار الأداء وحل المشكلات التقنية.', color: '#06B6D4' },
];

const contributors = [
  { name: 'أصيل السويدي', role: 'مختبر التطبيق وتحسين تجربة المستخدم', icon: '✨', color: '#F472B6' },
  { name: 'ربيع محمد', role: 'مراقبة الجودة واختبار الأداء', icon: '✅', color: '#F59E0B' },
  { name: 'رامي أمين', role: 'الدعم الفني والمتابعة التقنية', icon: '🎧', color: '#6366F1' },
  { name: 'إيهاب العليمي', role: 'البرمجة وتحسين الأداء', icon: '</>', color: '#10B981' },
  { name: 'عبدالله', role: 'تطوير الأنظمة المساندة', icon: '🔑', color: '#94A3B8' },
  { name: 'زيد محمد', role: 'التنسيق والدعم العام', icon: '📅', color: '#14B8A6' },
  { name: 'سام محمد', role: 'تطوير الأدوات الداخلية', icon: '🛠️', color: '#FACC15' },
  { name: 'حسام الحميدي', role: 'إدارة المجتمع والعلاقات العامة', icon: '🤝', color: '#8B5CF6' },
  { name: 'مهند عبد السلام', role: 'الحماية والأمن السيبراني', icon: '🛡️', color: '#EF4444' },
  { name: 'أيمن عمر', role: 'إدارة الشبكات والخوادم', icon: '🖥️', color: '#3B82F6' },
];
</script>

<style scoped>
.about-page {
  padding: 25px 35px 35px;
  overflow-y: auto;
  height: 100%;
  background: linear-gradient(135deg, #060A14 0%, #0B1120 30%, #0E1529 70%, #060A14 100%);
}
</style>
