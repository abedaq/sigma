# SIGMA_ASR_VTT - Coding Standards

**Developer & Main Contributor:** أصيل السويدي

## Coding Guidelines

### Python (Backend)
- **Type Annotations:** All function signatures must include explicit type hints (`def process_job(job_id: str) -> JobStatus:`).
- **Validation:** Use Pydantic models for request validation, domain schemas, and serializations.
- **Asynchronous Architecture:** Use `async/await` for I/O operations, network requests, and WebSocket broadcasting.
- **SOLID Principles:**
  - **S**: Single Responsibility per service/module.
  - **O**: Open for extension via Provider Interfaces.
  - **L**: Liskov Substitution for Cloud Providers.
  - **I**: Interface Segregation.
  - **D**: Dependency Injection for Provider Managers.

### TypeScript / Vue 3 (Frontend)
- Use Vue 3 Composition API (`<script setup lang="ts">`).
- Enforce strict TypeScript types (no implicit `any`).
- Use Scoped Vanilla CSS with CSS custom properties (variables) for design tokens.
