# SIGMA_ASR_VTT --- تعليمات إنشاء المشروع من الصفر

## الدور

أنت AI Agent مسؤول عن إنشاء مشروع برمجي حقيقي باسم:

``` text
SIGMA_ASR_VTT
```

ابدأ من الصفر. لا تعتمد على أي مشروع سابق، ولا تنسخ بنية قديمة، ولا تنشئ
كوداً وهمياً.

المطور والمساهم الأساسي:

``` text
أصيل السويدي
```

------------------------------------------------------------------------

# 1. الهدف

إنشاء تطبيق احترافي لمعالجة الفيديو والصوت وملفات الترجمة، مع التركيز
الأول على:

1.  جودة التفريغ الصوتي ASR.
2.  جودة الترجمة.
3.  دقة التوقيت.
4.  استقرار مسار المعالجة.
5.  قابلية إضافة مزودين ومحركات جديدة.
6.  الأمان.
7.  جودة الكود.
8.  أناقة الواجهة.
9.  سهولة الصيانة والتوسع.

التطبيق يجب أن يكون منتجاً حقيقياً قابلاً للاستخدام، وليس Prototype أو
Demo.

------------------------------------------------------------------------

# 2. القاعدة الأساسية

قبل كتابة أي كود:

1.  حلل المتطلبات.
2.  اختر أفضل التقنيات المناسبة للمشروع.
3.  افحص الأدوات والمكتبات الحديثة والموثوقة.
4.  صمم Architecture واضحة.
5.  حدد حدود كل طبقة.
6.  أنشئ البنية الأساسية.
7.  وثق قراراتك.
8.  بعد ذلك فقط ابدأ التنفيذ.

لا تختار تقنية لمجرد أنها شائعة.

اختيار التقنية يجب أن يعتمد على:

-   الأداء.
-   الاستقرار.
-   الأمان.
-   قابلية التوسع.
-   جودة المكتبات.
-   دعم Desktop UI.
-   دعم معالجة الفيديو والصوت.
-   دعم ASR.
-   دعم APIs.
-   سهولة الاختبار.
-   سهولة الصيانة.

------------------------------------------------------------------------

# 3. اختيار التقنية

اختر أفضل Stack مناسب للتطبيق، مع فصل واضح بين:

``` text
Frontend
    ↓
Application Layer
    ↓
Core / Domain
    ↓
Services
    ↓
Infrastructure
```

يجب أن تكون الواجهة والعمليات الداخلية منفصلة منطقياً.

لا تجعل الواجهة تحتوي على:

-   منطق ASR.
-   منطق الترجمة.
-   منطق FFmpeg.
-   API Keys.
-   عمليات معالجة ضخمة.

ولا تجعل الباك إند مسؤولاً عن تصميم الواجهة.

------------------------------------------------------------------------

# 4. البنية المعمارية

استخدم Architecture واضحة وقابلة للتوسع.

يجب فصل:

## Presentation

مسؤولة عن:

-   الواجهة.
-   إدخال المستخدم.
-   عرض الحالة.
-   عرض النتائج.

## Application

مسؤولة عن:

-   Use Cases.
-   تنسيق العمليات.
-   إدارة سير العمل.

## Core / Domain

مسؤولة عن:

-   قواعد المشروع.
-   Models.
-   Interfaces.
-   Contracts.

## Services

مسؤولة عن:

-   ASR.
-   Translation.
-   Subtitle Processing.
-   Video Processing.
-   Audio Processing.

## Integrations

مسؤولة عن:

-   Google Translation.
-   Gemini.
-   Cloud ASR.
-   Local ASR.
-   أي Provider خارجي.

## Infrastructure

مسؤولة عن:

-   Configuration.
-   Logging.
-   Storage.
-   HTTP.
-   Cache.
-   Process Management.

لا تخلط هذه المسؤوليات.

------------------------------------------------------------------------

# 5. قواعد صارمة للكود

## ممنوع تماماً

-   كود وهمي.
-   Placeholder Functions غير منفذة.
-   دوال غير مستخدمة.
-   ملفات غير مستخدمة.
-   Imports غير مستخدمة.
-   تكرار نفس المنطق.
-   Copy/Paste Logic.
-   God Files.
-   God Classes.
-   Global State غير ضروري.
-   API Keys داخل الكود.
-   أسرار داخل Git.
-   `except Exception: pass`.
-   إخفاء الأخطاء.
-   تنفيذ Shell غير آمن.
-   تجاهل Exit Codes.
-   إضافة مكتبات بدون حاجة.
-   بناء حلول مخصصة عندما توجد مكتبة موثوقة أفضل.
-   إنشاء Abstractions معقدة بلا سبب.
-   تغيير ملفات عشوائياً.
-   إصلاح مشكلة بإنشاء طبقة إضافية غير ضرورية.

------------------------------------------------------------------------

# 6. قاعدة المسؤولية الواحدة

كل ملف وكل Class وكل Function يجب أن يملك مسؤولية واضحة.

لا تضع:

``` text
ASR + Translation + FFmpeg + UI
```

داخل ملف واحد.

يجب أن يكون الفصل منطقياً:

``` text
ASR
├── Provider Interface
├── Provider Implementations
└── Service

Translation
├── Provider Interface
├── Provider Implementations
└── Service

Subtitles
├── Parser
├── Validator
├── Translator
└── Exporter
```

------------------------------------------------------------------------

# 7. نظام ASR

يجب تصميم ASR كنظام قابل للتوسع.

المسار:

``` text
Video / Audio
        ↓
Input Validation
        ↓
Audio Extraction
        ↓
ASR Provider
        ↓
Timestamped Segments
        ↓
Segment Validation
        ↓
Subtitle Generation
```

يجب دعم إمكانية إضافة:

-   Local ASR.
-   Cloud ASR.
-   API ASR.

إضافة Provider جديد يجب ألا تتطلب إعادة كتابة النظام.

يجب أن تكون التوقيتات دقيقة قدر الإمكان.

يجب عدم اختلاق Progress.

أي تقدم يظهر للمستخدم يجب أن يعتمد على حالة حقيقية.

------------------------------------------------------------------------

# 8. نظام الترجمة

جودة الترجمة أولوية أساسية.

يجب أن يكون النظام Provider-Based.

مثال:

``` text
TranslationService
        ↓
TranslationProvider
        ├── Google
        ├── Gemini
        ├── External API
        └── Future Providers
```

يجب دعم:

-   أكثر من محرك.
-   أكثر من API Key.
-   Rate Limits.
-   Retry.
-   Failover.
-   Provider Switching.
-   Context.
-   Chunking.
-   حفظ ترتيب المقاطع.
-   الحفاظ على التوقيت.
-   التحقق من النتيجة.

يجب عدم ترجمة كل Segment بشكل معزول إذا كان ذلك يضر بالسياق.

صمم نظاماً يسمح باستخدام Context مناسب مع الحفاظ على:

``` text
Subtitle ID
Timestamp
Text
```

------------------------------------------------------------------------

# 9. ترجمة ملفات الترجمة

يجب دعم:

``` text
.srt
.vtt
.ass
```

عند الحاجة.

يجب:

-   قراءة الملف.
-   تحليل البنية.
-   فصل Metadata عن النص.
-   ترجمة النص فقط.
-   الحفاظ على التوقيت.
-   الحفاظ على الترتيب.
-   التحقق من الناتج.
-   التصدير الصحيح.

ممنوع تغيير:

``` text
Subtitle Number
Timestamp
```

إلا إذا كانت هناك عملية صريحة لمعالجة التوقيت.

------------------------------------------------------------------------

# 10. معالجة الفيديو

المسار الأساسي:

``` text
Input Video
        ↓
Validation
        ↓
Metadata
        ↓
Audio Extraction
        ↓
ASR
        ↓
Subtitle Generation
        ↓
Translation
        ↓
Subtitle Validation
        ↓
Optional Embedding
        ↓
Output
```

يجب فصل كل مرحلة.

لا تكتب Pipeline كاملة داخل Function ضخمة.

يجب دعم:

-   إلغاء العملية.
-   الأخطاء.
-   إعادة المحاولة عند الحاجة.
-   تنظيف الملفات المؤقتة.
-   حفظ حالة العملية.

------------------------------------------------------------------------

# 11. واجهة المستخدم

صمم الواجهة اعتماداً على الصور المرفقة.

عند وجود صور تصميم:

1.  احفظ الصور داخل المشروع.
2.  أنشئ:

``` text
docs/design-reference/
```

أو:

``` text
screenshots/
```

3.  لا تحذف الصور.
4.  استخدمها كمرجع تصميم دائم.
5.  حافظ على الهوية البصرية.

يجب أن تكون الواجهة:

-   حديثة.
-   احترافية.
-   أنيقة.
-   منظمة.
-   واضحة.
-   غير مزدحمة.
-   متناسقة.
-   قابلة للتوسع.

يجب الاهتمام بـ:

-   Typography.
-   Spacing.
-   Cards.
-   Navigation.
-   Icons.
-   Empty States.
-   Loading States.
-   Error States.
-   Success States.
-   Progress UI.

------------------------------------------------------------------------

# 12. التبويبات الرئيسية

## التبويب الأول: ترجمة الفيديو

يجب أن يسمح بـ:

-   اختيار فيديو.
-   عرض معلومات الملف.
-   اختيار اللغة الأصلية.
-   اختيار اللغة المستهدفة.
-   اختيار ASR Provider.
-   اختيار Translation Provider.
-   اختيار نوع الإخراج.
-   استخراج الترجمة.
-   ترجمة الترجمة.
-   دمج الترجمة في الفيديو.

يجب عرض مراحل المعالجة الحقيقية:

``` text
تحميل الملف
    ↓
تحليل الفيديو
    ↓
استخراج الصوت
    ↓
التفريغ الصوتي
    ↓
معالجة النص
    ↓
الترجمة
    ↓
إنشاء الترجمة
    ↓
دمج الترجمة
    ↓
اكتملت العملية
```

------------------------------------------------------------------------

## التبويب الثاني: ترجمة ملفات الترجمة

يدعم:

``` text
SRT
VTT
ASS
```

الوظائف:

-   Import.
-   اختيار المصدر.
-   اختيار الهدف.
-   اختيار Provider.
-   ترجمة.
-   Preview.
-   Export.

------------------------------------------------------------------------

## التبويب الثالث: الإعدادات

يجب تقسيم الإعدادات إلى أقسام واضحة.

### Translation

-   Providers.
-   API Keys.
-   Models.
-   Languages.
-   Chunking.
-   Context.
-   Retry.
-   Rate Limits.
-   Failover.

### ASR

-   Provider.
-   Model.
-   Language.
-   Device.
-   CPU/GPU.
-   Compute Type.
-   VAD.
-   Timestamp Settings.

### Video

-   Output Format.
-   Subtitle Format.
-   Codec.
-   Output Directory.
-   Temporary Directory.

### General

-   Theme.
-   Language.
-   Notifications.
-   Logging Level.

------------------------------------------------------------------------

## التبويب الرابع: معلومات الجهاز

اعرض معلومات حقيقية فقط:

-   Operating System.
-   CPU.
-   CPU Cores.
-   RAM.
-   GPU.
-   VRAM.
-   Storage.
-   Python/Runtime Version.
-   FFmpeg Version.
-   Application Version.

لا تختلق معلومات.

اجعل النظام قابلاً لإضافة:

-   CUDA Status.
-   GPU Detection.
-   Benchmark.
-   Available Memory.

------------------------------------------------------------------------

## التبويب الخامس: About / Contributors

اعرض:

``` text
SIGMA_ASR_VTT
```

المطور:

``` text
أصيل السويدي
```

يجب أن تكون قائمة المساهمين قابلة للإضافة.

لا تضف أسماء وهمية.

------------------------------------------------------------------------

# 13. API Keys والأمان

ممنوع:

``` python
API_KEY = "secret"
```

يجب استخدام:

-   Environment Variables.
-   Secure Storage عند الحاجة.
-   Configuration Layer.

يجب:

-   إخفاء المفاتيح في الواجهة.
-   عدم طباعتها في Logs.
-   عدم إرسالها للواجهة بلا حاجة.
-   تنظيفها من Error Messages.

------------------------------------------------------------------------

# 14. أمان الملفات

كل ملف يرفعه المستخدم يعتبر Input غير موثوق.

يجب التحقق من:

-   Extension.
-   MIME Type.
-   File Signature.
-   File Size.
-   Path.
-   المحتوى عند الحاجة.

يجب الحماية من:

-   Path Traversal.
-   Malicious Files.
-   Arbitrary File Access.

لا تثق في اسم الملف أو امتداده فقط.

------------------------------------------------------------------------

# 15. FFmpeg و Subprocess

ممنوع:

``` python
os.system(user_input)
```

يجب:

-   استخدام Subprocess آمن.
-   تمرير Arguments بشكل منفصل.
-   عدم بناء Shell Command من Input غير موثوق.
-   التحقق من Exit Code.
-   تسجيل الأخطاء.
-   دعم Cancellation.

------------------------------------------------------------------------

# 16. الملفات المؤقتة

يجب إدارة Temporary Files بشكل واضح.

يجب:

-   إنشاء Temporary Directory آمن.
-   أسماء ملفات آمنة.
-   تنظيف الملفات بعد النجاح.
-   تنظيف الملفات بعد الفشل.
-   عدم حذف ملفات المستخدم الأصلية.
-   عدم الكتابة فوق الملفات الأصلية بدون إجراء واضح.

------------------------------------------------------------------------

# 17. Logging

استخدم مستويات:

``` text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

سجل:

-   بداية العملية.
-   مراحل Pipeline.
-   Provider المستخدم.
-   الأخطاء.
-   مدة العملية.

لا تسجل:

-   API Keys.
-   Tokens.
-   Passwords.
-   Secrets.

------------------------------------------------------------------------

# 18. Error Handling

استخدم أخطاء واضحة مثل:

``` text
ValidationError
ASRError
TranslationError
ProviderError
RateLimitError
FileProcessingError
ConfigurationError
```

يجب:

-   إظهار رسالة مفهومة للمستخدم.
-   تسجيل التفاصيل للمطور.
-   عدم عرض معلومات حساسة.
-   عدم ابتلاع الأخطاء.

------------------------------------------------------------------------

# 19. التوثيق الإلزامي

أنشئ ملفات Markdown حقيقية:

``` text
docs/
├── ARCHITECTURE.md
├── PROJECT_STRUCTURE.md
├── DEVELOPMENT_RULES.md
├── CODING_STANDARDS.md
├── SECURITY_RULES.md
├── ASR_PIPELINE.md
├── TRANSLATION_PIPELINE.md
├── API_INTEGRATION.md
└── ERROR_HANDLING.md
```

كل ملف يجب أن يعكس الحالة الحقيقية للمشروع.

لا تكتب Documentation منفصلة عن الواقع.

عند تغيير البنية، حدّث التوثيق.

------------------------------------------------------------------------

# 20. الاختبارات

أنشئ Tests حقيقية.

اختبر:

-   File Validation.
-   Subtitle Parsing.
-   Timestamp Preservation.
-   Subtitle Export.
-   ASR Providers.
-   Translation Providers.
-   Retry.
-   Rate Limits.
-   Failover.
-   Error Handling.
-   Video Processing.

لا تنشئ Tests وهمية تمر دائماً بدون اختبار حقيقي.

------------------------------------------------------------------------

# 21. طريقة تنفيذ المشروع

نفذ المشروع على مراحل:

## المرحلة 1 --- التحليل

-   تحليل المتطلبات.
-   اختيار Stack.
-   تصميم Architecture.
-   تحديد Structure.

## المرحلة 2 --- الأساس

-   Configuration.
-   Logging.
-   Error Handling.
-   Core Models.
-   Interfaces.

## المرحلة 3 --- ASR

-   Provider System.
-   Processing.
-   Timestamped Segments.

## المرحلة 4 --- Translation

-   Provider System.
-   API Management.
-   Retry.
-   Rate Limit.
-   Failover.

## المرحلة 5 --- Subtitles

-   SRT.
-   VTT.
-   ASS.
-   Validation.
-   Export.

## المرحلة 6 --- Video

-   Metadata.
-   Audio Extraction.
-   Subtitle Embedding.

## المرحلة 7 --- Backend

-   APIs.
-   Task Management.
-   Status.
-   Cancellation.

## المرحلة 8 --- Frontend

-   Main Layout.
-   Tabs.
-   Forms.
-   Progress.
-   Settings.
-   Device Info.
-   About.

## المرحلة 9 --- Integration

اختبر النظام كاملاً من:

``` text
Input
→ ASR
→ Translation
→ Subtitle
→ Output
```

## المرحلة 10 --- Audit

نفذ:

-   Code Review.
-   Security Review.
-   Dependency Review.
-   Test Review.
-   UI Review.
-   Cleanup.

------------------------------------------------------------------------

# 22. قاعدة AI Agent أثناء العمل

قبل تعديل أي ملف:

1.  اقرأ الملف.
2.  اقرأ الملفات المرتبطة.
3.  افهم Dependency Graph.
4.  افهم تدفق البيانات.
5.  حدد تأثير التعديل.
6.  نفذ أقل تعديل صحيح.
7.  اختبر.
8.  راجع الأمان.
9.  حدّث Documentation عند الحاجة.

لا تنشئ ملفات أو كوداً لمجرد ملء المشروع.

لا تعتبر المهمة مكتملة بمجرد أن التطبيق يفتح.

المعيار هو:

``` text
Works
+
Clean
+
Secure
+
Tested
+
Documented
+
Maintainable
```

------------------------------------------------------------------------

# 23. قاعدة نهائية

الجودة أهم من سرعة التنفيذ.

لا تكتب كوداً كثيراً بسرعة.

اكتب أقل قدر من الكود الذي يحقق التصميم الصحيح.

كل Function يجب أن يكون لها سبب.

كل Class يجب أن يكون له مسؤولية.

كل File يجب أن يكون له مكان.

كل Dependency يجب أن يكون لها مبرر.

كل API يجب أن يكون له Error Handling.

كل Input يجب أن يخضع للتحقق.

كل Secret يجب أن يكون محمياً.

كل Feature يجب أن تكون قابلة للاختبار.

لا تستخدم حلولاً مؤقتة ثم تنساها.

لا تترك TODOs فارغة.

لا تترك كوداً وهمياً.

لا تكرر المنطق.

لا تضخم المشروع بلا سبب.

أنشئ نظاماً احترافياً منظماً من البداية.

ابدأ أولاً بتحليل المشروع وإنشاء Architecture وProject Structure، ثم نفذ
المشروع تدريجياً مع اختبار كل مرحلة قبل الانتقال إلى المرحلة التالية.

------------------------------------------------------------------------

# 12. قواعد مكافحة استنزاف التوكن للوكيل الذكي (Token Conservation Protocols)

1. **القراءة الذكية المحددة (Targeted Reading):**
   - يمنع قراءة أي ملف بالكامل إذا تجاوز 80 سطراً دون استخدام `StartLine` و `EndLine`.
   - استخدام أدوات البحث (`Select-String` / `grep`) أولاً لتحديد أرقام الأسطر.

2. **ضبط مخرجات الأوامر (Quiet & Filtered Outputs):**
   - استخدام أوامر البناء الصامتة وتصفية مخرجات السجلات والأوامر (`-First 20` أو `-Tail 20`).

3. **التعديل الدقيق (Surgical Code Edits):**
   - استخدام `replace_file_content` بأصغر نطاق مستهدف بدلاً من إعادة كتابة ملفات بأكملها.

4. **كاش التوكن للترجمة (`_translation_cache`):**
   - تخزين الترجمات السابقة لمنع تكرار طلبات الـ LLM لنفس النصوص.

5. **الأرقام الإنجليزية الصارمة (English Numerals Only):**
   - استخدام الأرقام الإنجليزية (0, 1, 2, 3...) دائماً في كافة الأكواد والواجهات والسجلات.

