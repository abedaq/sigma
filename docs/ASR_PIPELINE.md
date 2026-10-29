# SIGMA_ASR_VTT - ASR Pipeline Architecture

**Developer & Main Contributor:** أصيل السويدي

## ASR Processing Flow

```text
Input Video / Audio File
           ↓
Magic Byte & MIME Validation
           ↓
Safe FFmpeg Extraction (16kHz Mono MP3/M4A)
           ↓
Cloud ASR Provider Selection (Speechmatics / Gemini Audio API / Cloud ASR)
           ↓
API Quota & Rate Limit Circuit Breaker Check
           ↓
Cloud API Speech Recognition Request
           ↓
Timestamped Segments Parsing
           ↓
ASR Hallucination & Repetition Guard Filter
           ↓
Validated Subtitle Segment Sequence
```

## Cloud ASR Integration Rules
1. **100% Cloud API Driven:** Speech recognition executes via external cloud APIs. No local heavy PyTorch inference is used.
2. **Audio Optimization:** Media files are converted locally to 16kHz Mono MP3/M4A prior to API transmission to optimize network bandwidth and upload latency.
3. **Hallucination Guard:** Filtering engine removes repetitive phrases, loop hallucinations, or invalid artifacts emitted by cloud speech models.
