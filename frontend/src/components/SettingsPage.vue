<template>
  <div class="settings-page">
    <!-- Toast Notification -->
    <transition name="toast-slide">
      <div v-if="toast" class="sigma-toast" :class="toast.type">
        <span>{{ toast.msg }}</span>
      </div>
    </transition>

    <div class="main-settings-nav" role="tablist" aria-label="أقسام الإعدادات الرئيسية">
      <button class="nav-tab-btn api-tab" :class="{ active: activeMainTab === 'api' }" @click="activeMainTab = 'api'" role="tab" :aria-selected="activeMainTab === 'api'">
        <span class="nav-icon">🔑</span>
        <div class="nav-texts">
          <strong>خدمات ومفاتيح السحابة (Cloud API & Models)</strong>
          <small>إدارة مفاتيح Gemini, OpenAI, Whisper, والشركات والموديلات</small>
        </div>
      </button>
      <button class="nav-tab-btn engine-tab" :class="{ active: activeMainTab === 'engine' }" @click="activeMainTab = 'engine'" role="tab" :aria-selected="activeMainTab === 'engine'">
        <span class="nav-icon">⚙️</span>
        <div class="nav-texts">
          <strong>باقي الإعدادات والقياسات (Engine & Formatting)</strong>
          <small>نبرة الذكاء الاصطناعي، تبريد الطلبات، قياسات السينما VTT، والقاموس</small>
        </div>
      </button>
    </div>

    <div class="settings-grid-layout">
      <!-- ================= LEFT / TOP SECTION: API KEYS MANAGEMENT ================= -->
      <div v-show="activeMainTab === 'api'" class="settings-section main-api-section animated-view">
        <div class="section-header">
          <span class="header-icon">🔑</span>
          <h4>إدارة مفاتيح واجهات السحابة (Cloud API Keys)</h4>
          <span class="badge-tag">القلب النابض للنظام</span>
        </div>

        <!-- API Sub Tabs -->
        <div class="api-sub-tabs" role="tablist">
          <button class="api-sub-tab asr" :class="{ active: apiSubTab === 'asr' }" @click="apiSubTab = 'asr'" role="tab" :aria-selected="apiSubTab === 'asr'">
            <span style="font-size: 16px;">🎙️</span> تفريغ الصوت عبر ASR API
          </button>
          <button class="api-sub-tab translate" :class="{ active: apiSubTab === 'translate' }" @click="apiSubTab = 'translate'" role="tab" :aria-selected="apiSubTab === 'translate'">
            <span style="font-size: 16px;">🌐</span> الترجمة والذكاء الاصطناعي عبر API
          </button>
        </div>

        <div class="card api-card-box">
          <!-- Stats Row -->
          <div class="api-stats-row">
            <div class="api-stat-card">
              <div class="stat-icon" style="background: #1E3A8A; color: #BFDBFE;">🔑</div>
              <div class="stat-info">
                <span class="stat-label">إجمالي المفاتيح</span>
                <span class="stat-value">{{ currentApiKeys.length }}</span>
              </div>
            </div>
            <div class="api-stat-card">
              <div class="stat-icon" style="background: #064E3B; color: #86EFAC;">🟢</div>
              <div class="stat-info">
                <span class="stat-label">مفاتيح نشطة</span>
                <span class="stat-value">{{ currentApiKeys.filter(k => k.status === 'active').length }}</span>
              </div>
            </div>
            <div class="api-stat-card">
              <div class="stat-icon" style="background: #78350F; color: #FEF08A;">🟡</div>
              <div class="stat-info">
                <span class="stat-label">بديل احتياطي</span>
                <span class="stat-value">{{ currentApiKeys.filter(k => k.status === 'fallback').length }}</span>
              </div>
            </div>
            <div class="api-stat-card">
              <div class="stat-icon" style="background: #7F1D1D; color: #FECACA;">🔴</div>
              <div class="stat-info">
                <span class="stat-label">مستنفدة / خطأ</span>
                <span class="stat-value">{{ currentApiKeys.filter(k => k.status === 'error' || k.status === 'exhausted').length }}</span>
              </div>
            </div>
          </div>

          <!-- Add New Key Section (CLEANED: Removed redundant provider list) -->
          <div class="add-key-section">
            <button class="btn btn-primary btn-add-key" @click="showAddKeyForm = !showAddKeyForm" :aria-expanded="showAddKeyForm">
              {{ showAddKeyForm ? '➖ إغلاق النافذة' : '➕ إضافة مفتاح جديد' }}
            </button>
            
            <div class="add-key-controls">
               <div class="form-group" style="margin: 0; width: 150px;">
                  <label for="sortOrderSelect" class="visually-hidden" style="display: none;">ترتيب المفاتيح</label>
                  <select id="sortOrderSelect" aria-label="ترتيب القائمة" class="form-control compact-select">
                    <option>ترتيب: الأولوية ▲</option>
                    <option>ترتيب: التناوب الذكي</option>
                  </select>
               </div>
            </div>
          </div>

          <!-- Add Key Form (Expandable & Full Labeled) -->
          <div v-if="showAddKeyForm" class="add-key-form">
            <div class="add-key-grid">

              <!-- صف 1: المزود + الموديل -->
              <div class="form-group">
                <label for="newKeyProviderSelect">المزود السحابي:</label>
                <select id="newKeyProviderSelect" v-model="newKeyProvider"
                        @change="onProviderChange"
                        class="form-control" aria-label="المزود السحابي">
                  <option disabled value="">-- اختر المزود --</option>
                  <option v-for="prov in currentProviders" :key="prov.value" :value="prov.value">
                    {{ prov.label }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label for="newKeyModelSelect">الموديل المشغل (Model):</label>
                <select id="newKeyModelSelect" v-model="newKeyModel"
                        class="form-control"
                        style="border-color: #93C5FD; font-weight: bold; color: #E2E8F0;"
                        aria-label="اختيار الموديل السحابي"
                        :disabled="!newKeyProvider">
                  <option v-if="!newKeyProvider" value="">-- اختر المزود أولاً --</option>
                  <option v-for="mod in availableModels" :key="mod.value" :value="mod.value">
                    {{ mod.label }}
                  </option>
                </select>
              </div>

              <!-- صف 2: اسم المفتاح + قيمته -->
              <div class="form-group">
                <label for="newKeyNameInput">اسم المفتاح المرجعي:</label>
                <input id="newKeyNameInput" v-model="newKeyName"
                       class="form-control"
                       :placeholder="newKeyNamePlaceholder"
                       aria-label="اسم المفتاح المرجعي" />
              </div>

              <div class="form-group">
                <label for="newKeyValueInput">قيمة المفتاح (API Key):</label>
                <input id="newKeyValueInput" v-model="newKeyValue"
                       type="password"
                       class="form-control"
                       placeholder="sk-... / gsk_... / AIza..."
                       aria-label="قيمة المفتاح" />
              </div>

              <!-- صف 3: نوع الاشتراك (عرض كامل) -->
              <div class="form-group" style="grid-column: 1 / -1;">
                <label for="newKeyTypeSelect">نوع الاشتراك:</label>
                <select id="newKeyTypeSelect" v-model="newKeyType"
                        class="form-control" aria-label="نوع الاشتراك"
                        style="max-width: 320px;">
                  <option :value="false">مجاني / تجريبي (Free)</option>
                  <option :value="true">مدفوع مفتوح (Paid Pro 💲)</option>
                </select>
              </div>

            </div>
            <div style="display: flex; gap: 10px; margin-top: 16px;">
               <button class="btn btn-primary" @click="addApiKey">💾 تشفير وحفظ المفتاح</button>
               <button class="btn btn-transparent" @click="showAddKeyForm = false">إلغاء</button>
            </div>
          </div>



          <!-- Table Header -->
          <div class="api-table-header">
             <div style="width: 28px; text-align: center;">☐</div>
             <div style="width: 55px; text-align: center;">الترتيب</div>
             <div style="width: 260px;">الموديل / الخدمة السحابية</div>
             <div style="width: 160px;">قيمة المفتاح</div>
             <div style="flex: 1;">حالة الحصة والطلبات (Quota & Rate)</div>
             <div style="width: 85px; text-align: center;">آخر فحص</div>
             <div style="width: 155px; text-align: center;">الإجراءات</div>
          </div>

          <!-- Key Rows -->
          <transition-group name="list-anim" tag="div" class="api-keys-list">
            <div v-for="(key, i) in currentApiKeys" :key="key.id"
                 class="api-key-row" :class="{ disabled: !key.enabled }">

              <!-- ☐ تفعيل / إيقاف -->
              <div style="width: 28px; text-align: center;">
                <input :id="'checkbox_key_' + key.id" type="checkbox"
                       :checked="key.enabled"
                       @change="toggleKeyEnabled(key)"
                       class="styled-checkbox"
                       :aria-label="'تفعيل ' + key.name" />
              </div>

              <!-- ▲▼ الأولوية -->
              <div style="width: 55px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;">
                <button class="btn-icon" title="رفع الأولوية" aria-label="رفع الأولوية"
                        :disabled="i === 0"
                        @click="moveKey(key.id, 'up')">▲</button>
                <span style="font-weight: bold; font-size: 13px; color: var(--primary-light);">{{ i + 1 }}</span>
                <button class="btn-icon" title="خفض الأولوية" aria-label="خفض الأولوية"
                        :disabled="i === currentApiKeys.length - 1"
                        @click="moveKey(key.id, 'down')">▼</button>
              </div>

              <!-- الموديل / الخدمة -->
              <div style="width: 260px; display: flex; align-items: center; gap: 10px;">
                <div class="provider-icon" :class="key.provider">{{ getProviderIcon(key.provider) }}</div>
                <div style="display: flex; flex-direction: column; gap: 3px;">
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-weight: bold; font-size: 13px; color: #FFFFFF;">{{ key.name }}</span>
                    <span v-if="key.isPaid" class="paid-badge" title="حساب مدفوع (VIP)">💲</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 5px; flex-wrap: wrap;">
                    <span class="status-tag" :class="key.status">{{ getStatusLabel(key.status) }}</span>
                    <span style="font-size: 11px; color: #BFDBFE; background: #1E3A8A; padding: 2px 7px; border-radius: 5px; font-weight: bold;">⚡ {{ getModelLabel(key.provider, key.model) }}</span>
                  </div>
                  <span style="font-size: 10px; color: #CBD5E1;">{{ getProviderLabel(key.provider) }}</span>
                </div>
              </div>

              <!-- قيمة المفتاح + نسخ -->
              <div style="width: 160px; display: flex; align-items: center; gap: 6px;">
                 <span class="key-masked">{{ formatKey(key.value) }}</span>
                 <button class="btn-icon copy-btn"
                         title="نسخ المفتاح إلى الحافظة"
                         aria-label="نسخ المفتاح"
                         @click="copyKey(key.value)">📋</button>
              </div>

              <!-- شريط الحصة -->
              <div style="flex: 1; padding: 0 12px; display: flex; flex-direction: column; justify-content: center;">
                 <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 5px;">
                   <span style="color: var(--text-dim);">معدل الاستلام: <strong style="color: var(--text-mid);">{{ key.usage }}/دقيقة</strong></span>
                   <span :style="{ color: getUsageColor(key.usage, key.limit), fontWeight: 'bold' }">{{ Math.round((key.usage / key.limit) * 100) }}% متاح ({{ key.limit - key.usage }} متبقي)</span>
                 </div>
                 <div class="usage-bar-bg">
                   <div class="usage-bar-fill" :style="{ width: ((key.usage / key.limit) * 100) + '%', background: getUsageColor(key.usage, key.limit) }"></div>
                 </div>
              </div>

              <!-- آخر فحص -->
              <div style="width: 85px; text-align: center;">
                <span v-if="checkingId === key.id" style="color: #FDE047; font-size: 11px;">⏳ جارٍ...</span>
                <span v-else-if="key.lastCheckStatus === 'ok'" style="color: #4ADE80; font-size: 11px; font-weight: bold;">صالح ✅</span>
                <span v-else-if="key.lastCheckStatus === 'error'" style="color: #FCA5A5; font-size: 11px; font-weight: bold;">تعطل ❌</span>
                <span v-else style="color: var(--text-dim); font-size: 11px;">—</span>
              </div>

              <!-- الإجراءات -->
              <div style="width: 155px; display: flex; justify-content: center; gap: 6px;">
                <button class="btn-action check"
                        title="فحص الاتصال والطلب"
                        :disabled="checkingId === key.id"
                        @click="checkKey(key)">🔍 فحص</button>
                <button class="btn-action edit"
                        title="تعديل المفتاح"
                        @click="openEdit(key)">✏️ تعديل</button>
                <button class="btn-action delete"
                        title="حذف من النظام"
                        @click="confirmDelete(key.id)">🗑 حذف</button>
              </div>
            </div>

            <div v-if="currentApiKeys.length === 0" class="empty-state" key="empty">
              <span>✨ لا توجد مفاتيح مضافة حالياً في تبويب {{ apiSubTab === 'asr' ? 'التفريغ السحابي ASR' : 'الترجمة الآلية' }}.</span>
              <p>اضغط على زر "➕ إضافة مفتاح جديد" بالأعلى للربط الفوري وبدء الإنتاج السريع!</p>
            </div>
          </transition-group>

          <!-- ═══ نافذة التعديل الـ Inline ═══ -->
          <transition name="toast-slide">
            <div v-if="editingKey" class="edit-modal-overlay" @click.self="editingKey = null">
              <div class="edit-modal-box">
                <h4 style="margin: 0 0 16px; color: #FFFFFF;">✏️ تعديل مفتاح: {{ editingKey.name }}</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                  <div class="form-group">
                    <label for="editKeyName">اسم المفتاح المرجعي:</label>
                    <input id="editKeyName" v-model="editForm.name" class="form-control" placeholder="اسم المفتاح" />
                  </div>
                  <div class="form-group">
                    <label for="editKeyValue">قيمة المفتاح (API Key):</label>
                    <input id="editKeyValue" v-model="editForm.value" type="password" class="form-control" placeholder="sk-..." />
                  </div>
                  <div class="form-group">
                    <label for="editKeyModel">الموديل:</label>
                    <select id="editKeyModel" v-model="editForm.model" class="form-control">
                      <option v-for="m in (providerModels[editingKey.provider] || [])"
                              :key="m.value" :value="m.value">{{ m.label }}</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label for="editKeyPaid">نوع الاشتراك:</label>
                    <select id="editKeyPaid" v-model="editForm.isPaid" class="form-control">
                      <option :value="false">مجاني / تجريبي (Free)</option>
                      <option :value="true">مدفوع مفتوح (Paid 💲)</option>
                    </select>
                  </div>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 16px; justify-content: flex-end;">
                  <button class="btn btn-transparent" @click="editingKey = null">إلغاء</button>
                  <button class="btn btn-primary" @click="saveEdit">💾 حفظ التعديلات</button>
                </div>
              </div>
            </div>
          </transition>

          <!-- ═══ نافذة تأكيد الحذف ═══ -->
          <transition name="toast-slide">
            <div v-if="deletingId" class="edit-modal-overlay" @click.self="deletingId = null">
              <div class="edit-modal-box" style="max-width: 380px; text-align: center;">
                <div style="font-size: 40px; margin-bottom: 12px;">🗑️</div>
                <h4 style="color: #FCA5A5; margin: 0 0 10px;">تأكيد الحذف</h4>
                <p style="color: #CBD5E1; font-size: 13px; margin: 0 0 20px;">هل أنت متأكد من حذف هذا المفتاح؟ لا يمكن التراجع عن هذا الإجراء.</p>
                <div style="display: flex; gap: 10px; justify-content: center;">
                  <button class="btn btn-transparent" @click="deletingId = null">إلغاء</button>
                  <button class="btn" style="background: #DC2626; color: white;" @click="executeDelete">🗑 نعم، احذف</button>
                </div>
              </div>
            </div>
          </transition>

          <!-- Bottom Actions & Legend -->
          <div class="api-bottom-area">
             <div class="api-legend">
               <span class="legend-item"><span class="dot active"></span> نشط (Active)</span>
               <span class="legend-item"><span class="dot fallback"></span> احتياطي بديل (Fallback)</span>
               <span class="legend-item"><span class="dot error"></span> متوقف أو خطأ (Disabled)</span>
             </div>
             
             <div class="api-actions">
               <button class="btn btn-transparent btn-sm"
                       :disabled="isCheckingAll"
                       @click="checkAllKeys">
                 {{ isCheckingAll ? '⏳ جارٍ الفحص...' : '🔒 فحص كل المفاتيح آلياً' }}
               </button>
             </div>
          </div>
        </div>
      </div>

      <!-- ================= RIGHT / BOTTOM: ADVANCED CLOUD & VTT CONTROLS ================= -->
      <div v-show="activeMainTab === 'engine'" class="settings-secondary-grid animated-view">
        
        <!-- BOX 1: AI TONE & CLOUD RATE LIMITING -->
        <div class="settings-section">
          <div class="section-header">
            <span class="header-icon">🧠</span>
            <h4>محرك صياغة الذكاء الاصطناعي وحفظ السياق</h4>
          </div>
          <div class="card settings-box-card">
            <!-- Tone selector replacing numbers -->
            <div class="form-group-block">
              <span class="section-label" style="display: block; font-weight: bold; margin-bottom: 8px;">🎯 نبرة وسياق الترجمة (AI Translation Tone):</span>
              <div class="tone-selector">
                <label v-for="tone in toneOptions" :key="tone.key" class="tone-btn" :class="{ active: selectedTone === tone.key }" style="cursor: pointer;">
                  <input type="radio" v-model="selectedTone" :value="tone.key" style="display: none;" />
                  <span>{{ tone.icon }}</span>
                  <div class="tone-info">
                    <strong>{{ tone.title }}</strong>
                    <p>{{ tone.desc }}</p>
                  </div>
                </label>
              </div>
            </div>

            <div class="divider-line"></div>

            <!-- Advanced AI features -->
            <div class="checkbox-group-block">
              <label class="checkbox-styled premium-check" for="chkSlidingWindow">
                <input id="chkSlidingWindow" type="checkbox" v-model="slidingWindowContext" aria-label="الترجمة بالسياق الممتد" />
                <div class="check-text">
                  <strong>✨ الترجمة بالسياق الممتد (Sliding Window Context)</strong>
                  <span>ربط الحوار بالفقرات السابقة واللاحقة لتفادي الأخطاء في ترجمة الضمائر وسياق القصة.</span>
                </div>
              </label>

              <label class="checkbox-styled premium-check" for="chkAutoFallback">
                <input id="chkAutoFallback" type="checkbox" v-model="autoFallbackEnabled" aria-label="التحويل السحابي الذكي الفوري" />
                <div class="check-text">
                  <strong>🔄 التحويل السحابي الذكي الفوري (Automatic Key & Provider Fallback)</strong>
                  <span>التبديل التلقائي لمفتاح أو محرك آخر دون توقف عند نفاذ الحصة أو حدوث خطأ من المزود.</span>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- BOX 2: API PROTECTION & RATE LIMITER (ANTI-429) -->
        <div class="settings-section">
          <div class="section-header">
            <span class="header-icon">🛡️</span>
            <h4>حماية واجهات API ومكافحة الأخطاء (Rate Limit Protection)</h4>
          </div>
          <div class="card settings-box-card">
            <div class="rate-limit-box">
              <div class="rate-info">
                <label for="rateDelaySelect" style="font-weight: bold; font-size: 13px; color: var(--text-main); display: block; margin-bottom: 4px;">⚡ فترة التبريد التلقائي بين الطلبات (Anti-429 Ban Shield)</label>
                <p style="font-size: 11px; color: var(--text-dim); margin: 0;">إدراج فاصل زمني ذكي بمقدار الميلي ثانية بين الدفعات عند الرفع الحاشد لمنع السقوط في أخطاء تجاوز معدل الطلبات.</p>
              </div>
              <div class="form-group" style="width: 170px; margin: 0;">
                <select id="rateDelaySelect" v-model="rateDelay" aria-label="فترة التبريد التلقائي" class="form-control compact-select" style="font-weight: bold; color: var(--primary-light);">
                  <option value="100">100ms (سريع جداً)</option>
                  <option value="300">300ms (متزن ومستقر)</option>
                  <option value="500">500ms (حماية آمنة)</option>
                  <option value="1000">1000ms (للمفاتيح المجانية)</option>
                </select>
              </div>
            </div>

            <div class="divider-line"></div>

            <div class="checkbox-group-block">
              <label class="checkbox-styled premium-check" for="chkAntiHallucination">
                <input id="chkAntiHallucination" type="checkbox" v-model="antiHallucination" aria-label="مرشح مكافحة هلوسات الصوت" />
                <div class="check-text">
                  <strong>🚫 مرشح مكافحة هلوسات الصوت (ASR Anti-Hallucination & Repetition Filter)</strong>
                  <span>تصفية الأسطر الوهمية والتكرارية التي قد تنتج من نماذج Whisper السحابية في أوقات الصمت.</span>
                </div>
              </label>

              <label class="checkbox-styled premium-check" for="chkTrimSilence">
                <input id="chkTrimSilence" type="checkbox" v-model="trimSilence" aria-label="تخطي فترات الصمت قبل الإرسال للسحابة" />
                <div class="check-text">
                  <strong>🤐 تخطي فترات الصمت قبل الإرسال للسحابة (Smart Silence Skipping / Token Saver)</strong>
                  <span>اقتطاع المسافات الفارغة برمجياً قبل الرفع لتسريع التفريغ وتوفير تكلفة ومفاتيح الـ API!</span>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- BOX 3: SUBTITLE GOLDEN MEASUREMENTS (CPL / CPS) & GLOSSARY -->
        <div class="settings-section">
          <div class="section-header">
            <span class="header-icon">🎞️</span>
            <h4>هندسة وقياسات ملفات الترجمة والقاموس (VTT / SRT Formatting)</h4>
          </div>
          <div class="card settings-box-card">
            <div class="grid-2 formatting-grid">
              <div class="format-input-card">
                <label for="rangeCpl">الحد الأقصى لطول السطر (CPL):</label>
                <div class="slider-row">
                  <input id="rangeCpl" type="range" v-model="maxCpl" min="30" max="60" step="2" class="range-slider" aria-label="الحد الأقصى لطول السطر" />
                  <span class="value-badge">{{ maxCpl }} حرف/سطر</span>
                </div>
                <small>المعيار السينمائي لعدم خروج النص عن الشاشة هو 42.</small>
              </div>

              <div class="format-input-card">
                <label for="rangeCps">معدل الحروف بالثانية (CPS - قراءة العين):</label>
                <div class="slider-row">
                  <input id="rangeCps" type="range" v-model="maxCps" min="15" max="30" step="1" class="range-slider" aria-label="معدل الحروف بالثانية" />
                  <span class="value-badge">{{ maxCps }} حرف/ثانية</span>
                </div>
                <small>يضمن سرعة ظهور مناسبة للمشاهد بدون اختفاء مفاجئ.</small>
              </div>
            </div>

            <div class="divider-line"></div>

            <div class="glossary-quick-box">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <label for="glossaryTermEn" style="font-size: 13px; font-weight: bold; color: var(--text-main);">📖 قاموس حماية وتثبيت المصطلحات (Smart Glossary Protection)</label>
                <span class="badge" style="background: #064E3B; color: #86EFAC; font-size: 11px; font-weight: bold;">{{ glossaryItems.length }} مصطلح محمي</span>
              </div>
              <p style="font-size: 11px; color: var(--text-dim); margin-bottom: 10px;">أدرج أسماء العلم، أسماء الـ API، أو المصطلحات المتخصصة التي تود حمايتها من التلاعب الحرفي أثناء الترجمة.</p>
              
              <div class="glossary-inputs">
                <input id="glossaryTermEn" v-model="newTermEn" class="form-control compact-select" placeholder="المصطلح الأجنبي (مثال: TensorFlow / DeepMind)" style="flex: 1;" aria-label="المصطلح الأجنبي" />
                <input id="glossaryTermAr" v-model="newTermAr" class="form-control compact-select" placeholder="المقابل في الترجمة (مثال: تنانين السحاب / ديب مايند)" style="flex: 1;" aria-label="المقابل في الترجمة" />
                <button class="btn btn-primary" style="height: 34px; padding: 0 16px; font-size: 12px;" @click="addGlossaryTerm">➕ إدراج</button>
              </div>

              <div class="terms-chips-list" v-if="glossaryItems.length > 0">
                <span v-for="(item, idx) in glossaryItems" :key="idx" class="term-chip">
                  <span><strong>{{ item.en }}</strong> = {{ item.ar }}</span>
                  <button @click="removeGlossaryTerm(idx)" :aria-label="'حذف المصطلح ' + item.en">✕</button>
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- GLOBAL BOTTOM ACTIONS BAR -->
    <div class="global-settings-footer">
      <div class="left-footer-actions">
        <button class="btn btn-transparent" @click="exportConfig" title="تصدير نسخة احتياطية من كافة المفاتيح والإعدادات">📤 تصدير الإعدادات والمفاتيح (JSON)</button>
        <button class="btn btn-transparent" @click="importConfig" title="استيراد إعدادات جاهزة من ملف محلي">📥 استيراد ملف إعدادات</button>
      </div>

      <div class="right-footer-actions">
        <button class="btn btn-transparent" style="color: #FDE047; font-weight: bold;" @click="resetToDefaults">🔄 إعادة الضبط للمنظومة الذكية</button>
        <button class="btn btn-primary save-main-btn" @click="saveSettings">💾 حفظ وتطبيق كافة الإعدادات</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { fetchKeys, addKey, deleteKey, fetchGlossary, addGlossaryTerm as addGlossaryTermApi } from '../services/api';

// ────────────────────────────────────────────────────────────────
// مفاتيح التخزين المحلي (localStorage keys)
// ────────────────────────────────────────────────────────────────
const LS_KEYS      = 'sigma_api_keys';
const LS_SETTINGS  = 'sigma_settings';

// Toast notification helper
const toast = ref<{ msg: string; type: 'success' | 'error' | 'info' } | null>(null);
function showToast(msg: string, type: 'success' | 'error' | 'info' = 'success') {
  toast.value = { msg, type };
  setTimeout(() => { toast.value = null; }, 3000);
}

const activeMainTab = ref<'api' | 'engine'>('api');

interface ApiKey {
  id: string;
  type: 'asr' | 'translate';
  name: string;
  provider: string;
  model: string;
  value: string;
  isPaid: boolean;
  enabled: boolean;
  status: 'active' | 'fallback' | 'exhausted' | 'error';
  usage: number;
  limit: number;
  lastCheckStatus?: 'ok' | 'error' | null;
}

const apiSubTab = ref<'asr' | 'translate'>('asr');

const asrProviders = [
  { value: 'whisper', label: 'OpenAI Whisper Cloud API' },
  { value: 'groq', label: 'Groq Cloud (Fast Whisper)' },
  { value: 'deepgram', label: 'Deepgram Nova API' },
  { value: 'assemblyai', label: 'AssemblyAI Cloud' },
  { value: 'speechmatics', label: 'Speechmatics ASR API' },
  { value: 'google_stt', label: 'Google Cloud Speech-to-Text' },
];

const translateProviders = [
  { value: 'gemini', label: 'Google Gemini Pro / Flash API' },
  { value: 'openai', label: 'OpenAI (GPT-4o / Turbo API)' },
  { value: 'deepl', label: 'DeepL Pro Translation API' },
  { value: 'claude', label: 'Anthropic Claude API' },
  { value: 'microsoft', label: 'Microsoft Azure Translator' },
];

const providerModels: Record<string, { value: string; label: string }[]> = {
  // ASR Providers
  whisper: [
    { value: 'whisper-1', label: 'Whisper Large V3 (Cloud Default ✨)' },
    { value: 'whisper-timestamped', label: 'Whisper Timestamped Pro ⏱️' }
  ],
  groq: [
    { value: 'whisper-large-v3-turbo', label: 'Whisper Large V3 Turbo (فائق السرعة وينصح به ⚡)' },
    { value: 'whisper-large-v3', label: 'Whisper Large V3 (أقصى دقة 🎯)' },
    { value: 'distil-whisper-large-v3-en', label: 'Distil Whisper English' }
  ],
  deepgram: [
    { value: 'nova-2', label: 'Nova-2 General (النموذج الذهبي ✨)' },
    { value: 'nova-2-meeting', label: 'Nova-2 Meeting & Dialogs' },
    { value: 'whisper-large', label: 'Deepgram Hosted Whisper' }
  ],
  assemblyai: [
    { value: 'best', label: 'AssemblyAI Best (أعلى دقة 🎯)' },
    { value: 'nano', label: 'AssemblyAI Nano (فوري وبأقل تكلفة ⚡)' }
  ],
  speechmatics: [
    { value: 'enhanced', label: 'Enhanced AI Engine (دقة فائقة)' },
    { value: 'standard', label: 'Standard Speed Engine' }
  ],
  google_stt: [
    { value: 'chirp-2', label: 'Google Chirp-2 Universal Model 🌐' },
    { value: 'latest_long', label: 'Latest Long Video & Audio' }
  ],
  // Translate Providers
  gemini: [
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (فائق السرعة والاقتصادية ⚡)' },
    { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro (الأقوى والأعمق سياقاً 🚀)' },
    { value: 'gemini-1.5-pro-002', label: 'Gemini 1.5 Pro V2' },
    { value: 'gemini-1.5-flash-002', label: 'Gemini 1.5 Flash V2' }
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o Omnimodal (الأفضل للترجمة السينمائية 🎭)' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini (اقتصادي وسريع ⚡)' },
    { value: 'o1-preview', label: 'O1 Reasoning Model' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo Engine' }
  ],
  deepl: [
    { value: 'deepl-pro-next-gen', label: 'DeepL Next-Gen AI Model ✨' },
    { value: 'deepl-pro-v2', label: 'DeepL Pro Classic Engine' }
  ],
  claude: [
    { value: 'claude-3-5-sonnet-latest', label: 'Claude 3.5 Sonnet (أفضل صياغة أدبية 🌟)' },
    { value: 'claude-3-5-haiku-latest', label: 'Claude 3.5 Haiku (سريع جداً ⚡)' },
    { value: 'claude-3-opus-latest', label: 'Claude 3 Opus (تحليل عميق)' }
  ],
  microsoft: [
    { value: 'azure-neural-v2', label: 'Azure Neural HD NMT 🪟' }
  ]
};

const currentProviders = computed(() => {
  return apiSubTab.value === 'asr' ? asrProviders : translateProviders;
});

const availableModels = computed(() => {
  return providerModels[newKeyProvider.value] || [{ value: 'default', label: 'النموذج القياسي (Default)' }];
});

// ────────────────────────────────────────────────────────────────
// الحالة الابتدائية — تُحمَّل من localStorage أو تبدأ فارغة
// ────────────────────────────────────────────────────────────────
const allKeys = ref<ApiKey[]>([]);

const currentApiKeys = computed(() => {
  return allKeys.value.filter(k => k.type === apiSubTab.value);
});

// Add Key Form
const showAddKeyForm = ref(false);
const newKeyName = ref('');
const newKeyProvider = ref('');
const newKeyModel = ref('');
const newKeyValue = ref('');
const newKeyType = ref(true); // default to Pro Paid

// ── خريطة رموز وأسماء مختصرة للمزودين ─────────────────────────
const PROVIDER_META: Record<string, { icon: string; short: string }> = {
  groq:         { icon: '⚡', short: 'Groq'       },
  openai:       { icon: '🧠', short: 'OpenAI'     },
  gemini:       { icon: '✨', short: 'Gemini'      },
  claude:       { icon: '🤖', short: 'Claude'      },
  microsoft:    { icon: '🪟', short: 'Azure'       },
  whisper:      { icon: '🎙️', short: 'Whisper'    },
  deepgram:     { icon: '🌊', short: 'Deepgram'   },
  assemblyai:   { icon: '🧩', short: 'AssemblyAI' },
  speechmatics: { icon: '🗣️', short: 'Speechmatics'},
  google_stt:   { icon: '🌐', short: 'Google STT' },
  deepl:        { icon: '🌍', short: 'DeepL'       },
};

/** يولّد اسماً فريداً للمفتاح بناءً على المزود والعدد الحالي */
function generateKeyName(provider: string): string {
  const meta  = PROVIDER_META[provider];
  const icon  = meta?.icon  ?? '☁️';
  const short = meta?.short ?? provider;
  // عدد المفاتيح الموجودة لنفس المزود + 1
  const count = allKeys.value.filter(k => k.provider === provider).length + 1;
  return `${icon} ${short} #${count}`;
}

/** placeholder يُظهر الاسم المقترح قبل أن يكتب المستخدم */
const newKeyNamePlaceholder = computed(() => {
  if (!newKeyProvider.value) return 'مثال: ⚡ Groq #1';
  return generateKeyName(newKeyProvider.value);
});

function onProviderChange() {
  // اختر الموديل الأول تلقائياً
  const models = providerModels[newKeyProvider.value];
  newKeyModel.value = (models && models.length > 0) ? models[0].value : 'default';

  // ولّد الاسم تلقائياً (يمكن للمستخدم تعديله)
  newKeyName.value = generateKeyName(newKeyProvider.value);
}



async function addApiKey() {
  if (!newKeyName.value || !newKeyProvider.value || !newKeyValue.value) return;
  const limit = newKeyType.value ? 10000 : 1500;
  const keyId = Date.now().toString();

  allKeys.value.push({
    id: keyId,
    type: apiSubTab.value,
    name: newKeyName.value,
    provider: newKeyProvider.value,
    model: newKeyModel.value || 'default',
    value: newKeyValue.value,
    isPaid: newKeyType.value,
    enabled: true,
    status: 'active',
    usage: 0,
    limit: limit,
    lastCheckStatus: null,
  });

  // Sync to Backend Secure Vault & Database
  try {
    await addKey(newKeyName.value, newKeyProvider.value, newKeyValue.value, newKeyType.value ? 1 : 2);
  } catch (err) {
    console.error('Backend key sync failed:', err);
  }

  newKeyName.value = '';
  newKeyProvider.value = '';
  newKeyModel.value = '';
  newKeyValue.value = '';
  newKeyType.value = true;
  showAddKeyForm.value = false;
  showToast('✅ تم إضافة المفتاح ومزامنته مع الخادم بنجاح!');
}

// ── ☐ تفعيل / إيقاف ────────────────────────────────────────────
function toggleKeyEnabled(key: ApiKey) {
  const idx = allKeys.value.findIndex(k => k.id === key.id);
  if (idx === -1) return;
  allKeys.value[idx].enabled = !allKeys.value[idx].enabled;
  allKeys.value[idx].status  = allKeys.value[idx].enabled ? 'active' : 'fallback';
  showToast(allKeys.value[idx].enabled ? '🟢 تم تفعيل المفتاح' : '🟡 تم إيقاف المفتاح', 'info');
}

// ── ▲▼ تغيير الأولوية ──────────────────────────────────────────
function moveKey(id: string, dir: 'up' | 'down') {
  const sameType = allKeys.value.filter(k => k.type === apiSubTab.value);
  const other    = allKeys.value.filter(k => k.type !== apiSubTab.value);
  const idx      = sameType.findIndex(k => k.id === id);
  if (idx === -1) return;
  const target = dir === 'up' ? idx - 1 : idx + 1;
  if (target < 0 || target >= sameType.length) return;
  [sameType[idx], sameType[target]] = [sameType[target], sameType[idx]];
  allKeys.value = [...sameType, ...other];
}

// ── 📋 نسخ المفتاح ─────────────────────────────────────────────
async function copyKey(val: string) {
  try {
    await navigator.clipboard.writeText(val);
    showToast('📋 تم نسخ المفتاح إلى الحافظة!', 'info');
  } catch {
    showToast('❌ فشل النسخ — تأكد من صلاحيات المتصفح', 'error');
  }
}

// ── 🔍 فحص مفتاح واحد ──────────────────────────────────────────
const checkingId = ref<string | null>(null);

/** خريطة نقاط فحص الاتصال لكل مزود */
const PROVIDER_CHECK_URLS: Record<string, { url: string; method: string; headers: (k: string) => Record<string, string>; body?: string }> = {
  groq: {
    url: 'https://api.groq.com/openai/v1/models',
    method: 'GET',
    headers: k => ({ Authorization: `Bearer ${k}` }),
  },
  openai: {
    url: 'https://api.openai.com/v1/models',
    method: 'GET',
    headers: k => ({ Authorization: `Bearer ${k}` }),
  },
  gemini: {
    url: `https://generativelanguage.googleapis.com/v1beta/models`,
    method: 'GET',
    headers: k => ({ 'x-goog-api-key': k }),
  },
  assemblyai: {
    url: 'https://api.assemblyai.com/v2/transcript',
    method: 'GET',
    headers: k => ({ authorization: k }),
  },
  deepgram: {
    url: 'https://api.deepgram.com/v1/projects',
    method: 'GET',
    headers: k => ({ Authorization: `Token ${k}` }),
  },
  claude: {
    url: 'https://api.anthropic.com/v1/models',
    method: 'GET',
    headers: k => ({ 'x-api-key': k, 'anthropic-version': '2023-06-01' }),
  },
  deepl: {
    url: 'https://api-free.deepl.com/v2/languages',
    method: 'GET',
    headers: k => ({ Authorization: `DeepL-Auth-Key ${k}` }),
  },
};

async function checkKey(key: ApiKey) {
  checkingId.value = key.id;
  const idx = allKeys.value.findIndex(k => k.id === key.id);
  if (idx === -1) { checkingId.value = null; return; }

  try {
    const cfg = PROVIDER_CHECK_URLS[key.provider];
    if (!cfg) {
      // مزود غير معروف — اعتبره صالحاً
      allKeys.value[idx].lastCheckStatus = 'ok';
      showToast(`✅ ${key.name}: تم قبول المفتاح (لا يوجد endpoint للفحص)`);
      return;
    }

    const res = await fetch(cfg.url, {
      method: cfg.method,
      headers: cfg.headers(key.value),
      body: cfg.body,
    });

    const ok = res.status < 400 || res.status === 422; // 422 = unprocessable = key valid
    allKeys.value[idx].lastCheckStatus = ok ? 'ok' : 'error';
    allKeys.value[idx].status = ok ? 'active' : 'error';
    showToast(
      ok ? `✅ ${key.name}: المفتاح صالح وجاهز!` : `❌ ${key.name}: المفتاح رفضه السيرفر (${res.status})`,
      ok ? 'success' : 'error'
    );
  } catch (e: any) {
    console.error(`Error checking key ${key.name}:`, e);
    allKeys.value[idx].lastCheckStatus = 'error';
    allKeys.value[idx].status = 'error';
    showToast(`⚠️ ${key.name}: تعذّر الاتصال بالسيرفر (CORS أو شبكة)`, 'error');
  } finally {
    checkingId.value = null;
  }
}

// ── 🔒 فحص كل المفاتيح دفعة واحدة ─────────────────────────────
const isCheckingAll = ref(false);
async function checkAllKeys() {
  if (isCheckingAll.value) return;
  isCheckingAll.value = true;
  showToast('🔍 بدء الفحص الشامل لجميع المفاتيح...', 'info');
  for (const key of allKeys.value) {
    await checkKey(key);
    await new Promise(r => setTimeout(r, 300)); // تأخير بسيط بين الطلبات
  }
  isCheckingAll.value = false;
  showToast('✅ اكتمل الفحص الشامل لجميع المفاتيح!');
}

// ── ✏️ تعديل مفتاح ─────────────────────────────────────────────
interface EditForm { name: string; value: string; model: string; isPaid: boolean; }
const editingKey = ref<ApiKey | null>(null);
const editForm   = ref<EditForm>({ name: '', value: '', model: '', isPaid: false });

function openEdit(key: ApiKey) {
  editingKey.value = key;
  editForm.value   = { name: key.name, value: key.value, model: key.model, isPaid: key.isPaid };
}

function saveEdit() {
  if (!editingKey.value) return;
  const idx = allKeys.value.findIndex(k => k.id === editingKey.value!.id);
  if (idx === -1) return;
  allKeys.value[idx].name   = editForm.value.name;
  allKeys.value[idx].value  = editForm.value.value;
  allKeys.value[idx].model  = editForm.value.model;
  allKeys.value[idx].isPaid = editForm.value.isPaid;
  allKeys.value[idx].limit  = editForm.value.isPaid ? 10000 : 1500;
  allKeys.value[idx].lastCheckStatus = null; // أعد الفحص
  editingKey.value = null;
  showToast('💾 تم حفظ التعديلات بنجاح!');
}

// ── 🗑 حذف مع تأكيد ────────────────────────────────────────────
const deletingId = ref<string | null>(null);

function confirmDelete(id: string) {
  deletingId.value = id;
}

async function executeDelete() {
  if (!deletingId.value) return;
  const targetId = deletingId.value;
  allKeys.value = allKeys.value.filter(k => k.id !== targetId);
  deletingId.value = null;

  try {
    await deleteKey(targetId);
  } catch (err) {
    console.error('Failed to delete key from backend:', err);
  }

  showToast('🗑 تم حذف المفتاح بنجاح!', 'info');
}



// AI Tone Options
const toneOptions = [
  { key: 'literal', icon: '🎯', title: 'حرفي ودقيق', desc: 'تفريغ وترجمة مطابقة للنص بدون تصرف، ممتاز للتقنية والوثائق.' },
  { key: 'balanced', icon: '⚖️', title: 'التوازن الذكي (افتراضي)', desc: 'يوازن بين الدقة واصطفاف الأسلوب ليدون حواراً طبيعياً ومرناً.' },
  { key: 'creative', icon: '🎨', title: 'سينمائي وإبداعي', desc: 'يصوغ العبارات بمرونة أدبية فائقة، مثالي للمحاضرات والأفلام والدراما.' }
];
const selectedTone = ref('balanced');

// AI Settings & Limiters state
const slidingWindowContext = ref(true);
const autoFallbackEnabled = ref(true);
const antiHallucination = ref(true);
const trimSilence = ref(true);
const rateDelay = ref('500');
const maxCpl = ref(42);
const maxCps = ref(20);

// Glossary — يجب أن يكون قبل persistSettings و watch
const newTermEn = ref('');
const newTermAr = ref('');
const glossaryItems = ref([
  { en: 'Sigma VTT', ar: 'سيجما VTT (محمية)' },
  { en: 'API Token', ar: 'رمز الاستوثاق' }
]);

// ────────────────────────────────────────────────────────────────
// دوال الحفظ والتحميل من localStorage
// ────────────────────────────────────────────────────────────────
function persistKeys() {
  try {
    localStorage.setItem(LS_KEYS, JSON.stringify(allKeys.value));
  } catch { /* تجاهل خطأ الحصة */ }
}

function persistSettings() {
  try {
    const snapshot = {
      selectedTone:        selectedTone.value,
      slidingWindowContext: slidingWindowContext.value,
      autoFallbackEnabled: autoFallbackEnabled.value,
      antiHallucination:   antiHallucination.value,
      trimSilence:         trimSilence.value,
      rateDelay:           rateDelay.value,
      maxCpl:              maxCpl.value,
      maxCps:              maxCps.value,
      glossaryItems:       glossaryItems.value,
    };
    localStorage.setItem(LS_SETTINGS, JSON.stringify(snapshot));
  } catch { /* تجاهل خطأ الحصة */ }
}

function applySettingsFromObject(s: any) {
  if (!s) return;
  if (s.selectedTone         !== undefined) selectedTone.value         = s.selectedTone;
  if (s.slidingWindowContext !== undefined) slidingWindowContext.value = s.slidingWindowContext;
  if (s.autoFallbackEnabled  !== undefined) autoFallbackEnabled.value  = s.autoFallbackEnabled;
  if (s.antiHallucination    !== undefined) antiHallucination.value    = s.antiHallucination;
  if (s.trimSilence          !== undefined) trimSilence.value          = s.trimSilence;
  if (s.rateDelay            !== undefined) rateDelay.value            = s.rateDelay;
  if (s.maxCpl               !== undefined) maxCpl.value               = s.maxCpl;
  if (s.maxCps               !== undefined) maxCps.value               = s.maxCps;
  if (s.glossaryItems        !== undefined) glossaryItems.value        = s.glossaryItems;
}

function loadFromStorage() {
  const DEFAULT_KEYS: ApiKey[] = [
    {
      id: 'default_assemblyai_1',
      type: 'asr',
      name: 'AssemblyAI Default',
      provider: 'assemblyai',
      model: 'best',
      value: '',
      isPaid: false,
      enabled: false,
      status: 'active',
      usage: 0,
      limit: 1500,
      lastCheckStatus: null,
    },
    {
      id: 'default_groq_1',
      type: 'asr',
      name: 'Groq Whisper Default',
      provider: 'groq',
      model: 'whisper-large-v3-turbo',
      value: '',
      isPaid: false,
      enabled: false,
      status: 'active',
      usage: 0,
      limit: 1500,
      lastCheckStatus: null,
    },
  ];

  try {
    const raw = localStorage.getItem(LS_KEYS);
    if (raw) {
      allKeys.value = JSON.parse(raw) as ApiKey[];
    } else {
      allKeys.value = [...DEFAULT_KEYS];
      persistKeys();
    }
  } catch { allKeys.value = [...DEFAULT_KEYS]; }

  try {
    const raw = localStorage.getItem(LS_SETTINGS);
    if (raw) {
      applySettingsFromObject(JSON.parse(raw));
    }
  } catch { /* تجاهل وابدأ بالقيم الافتراضية */ }
}


// ── تحميل عند أول فتح للأداة ────────────────────────────────────
onMounted(async () => {
  loadFromStorage();
  try {
    const bKeys = await fetchKeys();
    if (bKeys && bKeys.length > 0) {
      for (const bk of bKeys) {
        if (!allKeys.value.some(k => k.id === bk.id || k.name === bk.name)) {
          allKeys.value.push({
            id: bk.id,
            type: (bk.provider.includes('groq') || bk.provider.includes('deepgram') || bk.provider.includes('whisper')) ? 'asr' : 'translate',
            name: bk.name,
            provider: bk.provider,
            model: 'default',
            value: bk.masked_key,
            isPaid: true,
            enabled: bk.status === 'active',
            status: bk.status === 'active' ? 'active' : 'fallback',
            usage: 0,
            limit: 10000,
            lastCheckStatus: 'ok'
          });
        }
      }
    }
    const bGlossary = await fetchGlossary();
    if (bGlossary) {
      for (const [en, ar] of Object.entries(bGlossary)) {
        if (!glossaryItems.value.some(g => g.en.toLowerCase() === en.toLowerCase())) {
          glossaryItems.value.push({ en, ar });
        }
      }
    }
  } catch (err) {
    console.error('Error syncing initial data from backend:', err);
  }
});

// ── حفظ تلقائي فور أي تغيير على المفاتيح ──────────────────────
watch(allKeys, persistKeys, { deep: true });

// ── حفظ تلقائي فور أي تغيير على الإعدادات ─────────────────────
watch(
  [selectedTone, slidingWindowContext, autoFallbackEnabled,
   antiHallucination, trimSilence, rateDelay, maxCpl, maxCps, glossaryItems],
  persistSettings,
  { deep: true }
);



async function addGlossaryTerm() {
  if (newTermEn.value.trim() && newTermAr.value.trim()) {
    const en = newTermEn.value.trim();
    const ar = newTermAr.value.trim();
    glossaryItems.value.push({ en, ar });
    newTermEn.value = '';
    newTermAr.value = '';

    try {
      await addGlossaryTermApi(en, ar);
    } catch (err) {
      console.error('Failed to sync glossary item to backend:', err);
    }
  }
}

function removeGlossaryTerm(i: number) {
  glossaryItems.value.splice(i, 1);
}

// ────────────────────────────────────────────────────────────────
// Config Export / Import (وظيفية حقيقية)
// ────────────────────────────────────────────────────────────────
function exportConfig() {
  const payload = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    apiKeys: allKeys.value,
    settings: {
      selectedTone:        selectedTone.value,
      slidingWindowContext: slidingWindowContext.value,
      autoFallbackEnabled: autoFallbackEnabled.value,
      antiHallucination:   antiHallucination.value,
      trimSilence:         trimSilence.value,
      rateDelay:           rateDelay.value,
      maxCpl:              maxCpl.value,
      maxCps:              maxCps.value,
      glossaryItems:       glossaryItems.value,
    },
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `sigma_config_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('✅ تم تصدير الإعدادات والمفاتيح بنجاح!');
}

async function handleImportFile(file: File) {
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    if (data.apiKeys) allKeys.value = data.apiKeys;
    applySettingsFromObject(data.settings);
    persistKeys();
    persistSettings();
    showToast('✅ تم استيراد الإعدادات والمفاتيح بنجاح!');
  } catch (err) {
    console.error('Error parsing imported settings JSON:', err);
    showToast('❌ الملف غير صالح أو تالف!', 'error');
  }
}

function importConfig() {
  const input = document.createElement('input');
  input.type  = 'file';
  input.accept = '.json';
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      await handleImportFile(file);
    }
  };
  input.click();
}

async function saveSettings() {
  persistKeys();
  persistSettings();

  // Sync to Backend Database
  try {
    for (const k of allKeys.value) {
      if (k.value && !k.value.includes('••••')) {
        await addKey(k.name, k.provider, k.value, k.isPaid ? 1 : 2);
      }
    }
    for (const item of glossaryItems.value) {
      await addGlossaryTermApi(item.en, item.ar);
    }
  } catch (err) {
    console.error('Backend sync during saveSettings error:', err);
  }

  showToast('💾 تم حفظ جميع الإعدادات والمفاتيح ومزامنتها بنجاح!');
}

function resetToDefaults() {
  selectedTone.value = 'balanced';
  rateDelay.value = '500';
  maxCpl.value = 42;
  maxCps.value = 20;
  slidingWindowContext.value = true;
  autoFallbackEnabled.value = true;
  antiHallucination.value = true;
  trimSilence.value = true;
  persistSettings();
  showToast('🔄 تم إعادة الضبط للإعدادات الذكية الافتراضية!', 'info');
}

// Formatting helpers
function formatKey(val: string) {
  if (!val) return '';
  if (val.length <= 8) return '••••••••••••';
  return val.slice(0, 5) + '••••••••••' + val.slice(-4);
}

function getProviderIcon(prov: string) {
  const map: Record<string, string> = {
    gemini: '✨', openai: '🧠', deepl: '🌍', claude: '🤖', microsoft: '🪟',
    whisper: '🎙️', groq: '⚡', deepgram: '🌊', assemblyai: '🧩', speechmatics: '🗣️', google_stt: '🌐'
  };
  return map[prov] || '☁️';
}

function getProviderLabel(prov: string) {
  const item = [...asrProviders, ...translateProviders].find(p => p.value === prov);
  return item ? item.label : prov;
}

function getModelLabel(prov: string, mod: string) {
  const list = providerModels[prov];
  if (!list) return mod || 'Standard Engine';
  const found = list.find(m => m.value === mod);
  return found ? found.label.replace(/\([^)]*\)/g, '').trim() : mod;
}

function getStatusLabel(st: string) {
  const labels: Record<string, string> = { active: 'نشط 🟢', fallback: 'احتياطي 🟡', exhausted: 'نَفَد 🔴', error: 'خطأ ❌' };
  return labels[st] || st;
}

function getUsageColor(use: number, limit: number) {
  const ratio = use / (limit || 1);
  if (ratio > 0.85) return '#FCA5A5';
  if (ratio > 0.60) return '#FDE047';
  return '#4ADE80';
}
</script>

<style scoped>
.settings-page {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: var(--text-main);
  background: var(--bg-dark);
}

/* ── Add Key Form Grid (2 columns fixed) ─ */
.add-key-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 4px;
}
@media (max-width: 640px) {
  .add-key-grid { grid-template-columns: 1fr; }
}

/* ── Master Settings Nav ────────────────── */
.main-settings-nav {
  display: flex;
  gap: 16px;
  background: rgba(10, 15, 27, 0.9);
  padding: 8px;
  border-radius: 16px;
  border: 1px solid var(--border-card);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}
.nav-tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  color: #94A3B8;
  cursor: pointer;
  text-align: right;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.nav-icon { font-size: 26px; transition: transform 0.3s ease; }
.nav-texts { display: flex; flex-direction: column; gap: 3px; }
.nav-texts strong { font-size: 14px; font-weight: bold; color: #E2E8F0; }
.nav-texts small { font-size: 11px; color: #94A3B8; opacity: 0.85; }
.nav-tab-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.1);
}
.nav-tab-btn:hover .nav-icon { transform: scale(1.15) rotate(5deg); }
.nav-tab-btn.active {
  color: #FFFFFF;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  transform: scale(1.01);
}
.nav-tab-btn.active .nav-texts strong { color: #FFFFFF; }
.nav-tab-btn.active .nav-texts small { color: #E2E8F0; opacity: 1; }
.nav-tab-btn.api-tab.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(79, 70, 229, 0.25));
  border: 1px solid #93C5FD;
}
.nav-tab-btn.engine-tab.active {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(5, 150, 105, 0.25));
  border: 1px solid #34D399;
}
.animated-view {
  animation: tabFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes tabFadeIn {
  0% { opacity: 0; transform: translateY(8px) scale(0.99); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Section Header ─────────────────────── */
.settings-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-icon { font-size: 20px; }
.section-header h4 { font-size: 16px; font-weight: bold; margin: 0; color: #FFFFFF; }
.badge-tag {
  background: #1E3A8A;
  color: #BFDBFE;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: bold;
}

/* ── Layout & Grid ──────────────────────── */
.settings-grid-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
  flex: 1;
}
.settings-secondary-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.settings-box-card {
  padding: 20px !important;
  border-radius: 16px !important;
  background: rgba(13, 20, 36, 0.85) !important;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-card) !important;
}

/* ── Sub Tabs (ASR & Translate) ─────────── */
.api-sub-tabs {
  display: flex;
  gap: 12px;
  background: rgba(8, 12, 22, 0.85);
  padding: 6px;
  border-radius: 12px;
  border: 1px solid var(--border-card);
}
.api-sub-tab {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: #CBD5E1;
  font-family: inherit;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
.api-sub-tab:hover {
  background: #1E293B;
  color: #FFFFFF;
  transform: translateY(-1px);
}
.api-sub-tab.active {
  color: #FFFFFF;
  transform: scale(1.01);
  box-shadow: 0 4px 15px rgba(0,0,0,0.4);
}
.api-sub-tab.asr.active {
  background: linear-gradient(135deg, #059669, #047857);
  border-color: #34D399;
}
.api-sub-tab.translate.active {
  background: linear-gradient(135deg, #2563EB, #4338CA);
  border-color: #93C5FD;
}

/* ── API Card & Stats ───────────────────── */
.api-card-box {
  padding: 16px !important;
  background: rgba(14, 21, 38, 0.95) !important;
}
.api-stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.api-stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(10, 16, 30, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 16px;
}
.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.stat-label { font-size: 11px; color: #CBD5E1; font-weight: bold; }
.stat-value { font-size: 17px; font-weight: bold; color: #FFFFFF; }

.add-key-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(10, 15, 28, 0.7);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 14px;
}
.btn-add-key { font-size: 13px; padding: 8px 16px; border-radius: 8px; font-weight: bold; }

.add-key-form {
  background: rgba(12, 19, 35, 0.95);
  border: 1px dashed #93C5FD;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  animation: fadeIn 0.2s ease;
}

/* ── Table Styling ──────────────────────── */
.api-table-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #1E293B;
  border-bottom: 1px solid var(--border-card);
  font-size: 12px;
  font-weight: bold;
  color: #F8FAFC;
}
.api-keys-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
  position: relative;
}
.api-key-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(10, 16, 29, 0.85);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  padding: 10px 16px;
  transition: all 0.2s;
}
.api-key-row:hover {
  background: rgba(15, 24, 45, 0.95);
  border-color: #93C5FD;
}
.styled-checkbox { width: 16px; height: 16px; accent-color: var(--primary); cursor: pointer; }
.provider-icon { width: 32px; height: 32px; border-radius: 8px; background: rgba(255, 255, 255, 0.1); display: flex; align-items: center; justify-content: center; font-size: 16px; }
.paid-badge { background: #064E3B; color: #86EFAC; border: 1px solid #10B981; font-size: 10px; padding: 2px 6px; border-radius: 6px; font-weight: bold; }
.status-tag { font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 6px; }
.status-tag.active { background: #064E3B; color: #86EFAC; }
.status-tag.fallback { background: #78350F; color: #FEF08A; }
.status-tag.error, .status-tag.exhausted { background: #7F1D1D; color: #FECACA; }
.key-masked { font-family: Consolas, monospace; font-size: 13px; color: #E2E8F0; background: rgba(0,0,0,0.4); padding: 4px 10px; border-radius: 6px; letter-spacing: 1px; font-weight: bold; }
.copy-btn { font-size: 15px; opacity: 0.8; transition: opacity 0.2s; background: none; border: none; cursor: pointer; color: #FFFFFF; }
.copy-btn:hover { opacity: 1; }
.usage-bar-bg { height: 6px; background: rgba(0,0,0,0.5); border-radius: 3px; overflow: hidden; }
.usage-bar-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }

.btn-action { background: transparent; border: none; font-family: inherit; font-size: 12px; font-weight: bold; cursor: pointer; padding: 5px 10px; border-radius: 6px; transition: background 0.2s; }
.btn-action.check { color: #93C5FD; } .btn-action.check:hover { background: rgba(59, 130, 246, 0.2); }
.btn-action.edit { color: #FDE047; } .btn-action.edit:hover { background: rgba(217, 119, 6, 0.2); }
.btn-action.delete { color: #FCA5A5; } .btn-action.delete:hover { background: rgba(220, 38, 38, 0.2); }

.empty-state {
  text-align: center;
  padding: 35px;
  color: #CBD5E1;
  background: rgba(0,0,0,0.3);
  border-radius: 12px;
  border: 1px dashed var(--border-card);
}

.api-bottom-area {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--border-card);
}
.api-legend { display: flex; gap: 16px; font-size: 12px; color: #E2E8F0; font-weight: bold; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.active { background: #4ADE80; }
.dot.fallback { background: #FDE047; }
.dot.error { background: #FCA5A5; }

/* ── AI Tone Selector ───────────────────── */
.section-label { font-size: 13px; font-weight: bold; color: #FFFFFF; margin-bottom: 8px; display: block; }
.tone-selector {
  display: flex;
  gap: 14px;
}
.tone-btn {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: rgba(10, 16, 28, 0.7);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  text-align: right;
  color: #CBD5E1;
  transition: all 0.25s ease;
}
.tone-btn span { font-size: 24px; }
.tone-info strong { display: block; color: #FFFFFF; font-size: 13px; margin-bottom: 4px; }
.tone-info p { font-size: 11px; margin: 0; line-height: 1.4; color: #CBD5E1; }
.tone-btn:hover { border-color: #93C5FD; transform: translateY(-2px); }
.tone-btn.active {
  background: rgba(37, 99, 235, 0.2);
  border-color: #93C5FD;
  box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
}

.divider-line { height: 1px; background: rgba(255,255,255,0.08); margin: 20px 0; }

/* ── Checkboxes Block ───────────────────── */
.checkbox-group-block { display: flex; flex-direction: column; gap: 14px; }
.premium-check {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  padding: 10px;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  transition: background 0.2s;
}
.premium-check:hover { background: rgba(255,255,255,0.07); }
.check-text strong { display: block; font-size: 13px; color: #FFFFFF; margin-bottom: 3px; }
.check-text span { font-size: 11px; color: #CBD5E1; }

/* ── Rate Limiter Box ───────────────────── */
.rate-limit-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

/* ── Subtitle Formatting & Glossary ─────── */
.formatting-grid { gap: 20px !important; }
.format-input-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(10, 16, 28, 0.7);
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
}
.format-input-card label { font-size: 12px; font-weight: bold; color: #FFFFFF; }
.slider-row { display: flex; align-items: center; gap: 12px; }
.range-slider { flex: 1; accent-color: var(--primary); cursor: pointer; }
.value-badge { background: #1E3A8A; color: #BFDBFE; font-size: 12px; font-weight: bold; padding: 4px 10px; border-radius: 6px; min-width: 85px; text-align: center; }
.format-input-card small { font-size: 10px; color: #94A3B8; }

.glossary-quick-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.glossary-inputs { display: flex; gap: 10px; align-items: center; }
.terms-chips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  max-height: 110px;
  overflow-y: auto;
}
.term-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #064E3B;
  border: 1px solid #10B981;
  color: #F8FAFC;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}
.term-chip button { background: none; border: none; color: #FCA5A5; cursor: pointer; font-weight: bold; }

/* ── Global Footer Actions ──────────────── */
.global-settings-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 22px;
  background: #0B1322;
  border: 1px solid var(--border-card);
  border-radius: 14px;
  margin-top: 10px;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.3);
  position: sticky;
  bottom: 0;
  z-index: 5;
}
.left-footer-actions, .right-footer-actions { display: flex; gap: 12px; align-items: center; }
.save-main-btn { padding: 10px 24px !important; font-size: 14px !important; font-weight: bold; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.45); }

/* ── Utilities ──────────────────────────── */
.compact-select {
  height: 34px !important;
  padding: 4px 10px !important;
  font-size: 12px !important;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.list-anim-enter-active, .list-anim-leave-active { transition: all 0.35s ease; }
.list-anim-enter-from, .list-anim-leave-to { opacity: 0; transform: translateX(20px); }

/* ── Toast Notification ─────────────────── */
.sigma-toast {
  position: fixed;
  bottom: 28px;
  left: 28px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 22px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: bold;
  color: #FFFFFF;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 380px;
  pointer-events: none;
}
.sigma-toast.success { background: linear-gradient(135deg, rgba(22, 163, 74, 0.9), rgba(5, 150, 105, 0.9)); border-color: #34D399; }
.sigma-toast.error   { background: linear-gradient(135deg, rgba(220, 38, 38, 0.9), rgba(185, 28, 28, 0.9));  border-color: #FCA5A5; }
.sigma-toast.info    { background: linear-gradient(135deg, rgba(37, 99, 235, 0.9), rgba(79, 70, 229, 0.9));  border-color: #93C5FD; }

/* Toast Animation */
.toast-slide-enter-active { transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1); }
.toast-slide-leave-active  { transition: all 0.25s ease-in; }
.toast-slide-enter-from    { opacity: 0; transform: translateY(20px) scale(0.95); }
.toast-slide-leave-to      { opacity: 0; transform: translateY(10px) scale(0.95); }

/* ── Edit / Delete Modal ────────────────── */
.edit-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(6px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.edit-modal-box {
  background: linear-gradient(145deg, #0D1424, #111827);
  border: 1px solid rgba(147, 197, 253, 0.25);
  border-radius: 18px;
  padding: 28px;
  width: 100%;
  max-width: 560px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  animation: modalPop 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes modalPop {
  from { opacity: 0; transform: scale(0.92) translateY(16px); }
  to   { opacity: 1; transform: scale(1)    translateY(0); }
}

/* ── Disabled Key Row ───────────────────── */
.api-key-row.disabled {
  opacity: 0.45;
  filter: grayscale(0.5);
}

/* ── Disabled Buttons ───────────────────── */
button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}
</style>


