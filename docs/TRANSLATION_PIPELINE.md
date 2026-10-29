# SIGMA_ASR_VTT - Translation Pipeline Architecture

**Developer & Main Contributor:** أصيل السويدي

## Context-Aware Subtitle Translation

```text
Input Subtitle Segments / File (.srt, .vtt, .ass)
                        ↓
             Metadata & Time Separation
                        ↓
     Sliding Window Context Chunking (10-25 Segments)
                        ↓
 Dynamic System Prompt Injection (Glossary & Profile Terms)
                        ↓
      Cloud Translation Provider (Gemini / Google)
                        ↓
  Structural Validator (Timestamp & Line Alignment Check)
                        ↓
             Final Export & Subtitle Embedding
```

## Core Features
1. **Context-Aware Sliding Window:** Translates subtitle blocks in coherent chunks to maintain narrative context and tone.
2. **Terminology Glossary & Profiles:** Injects custom terminology dictionaries and translation profiles directly into API system prompts.
3. **Timestamp Integrity:** Guarantees that subtitle line numbers and start/end timestamps are preserved without drift.
