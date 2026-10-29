# SIGMA_ASR_VTT - Development Rules

**Developer & Main Contributor:** أصيل السويدي

## Strictly Prohibited Behaviors

1. **NO Placeholder Functions:** All functions must be fully implemented. No empty function bodies or `pass` placeholders.
2. **NO Fake Code or Mock Data in Production:** All components, metrics, and hardware reports must reflect actual runtime states.
3. **NO API Keys in Source Code:** API keys must never be hardcoded, logged, or committed to Git repository.
4. **NO Shell Insecurity:** Never use `os.system()` or `shell=True` in subprocess calls. Pass arguments as explicit lists.
5. **NO Ignored Errors:** Silent exception swallowing (`except Exception: pass`) is strictly forbidden.
6. **NO God Files or God Classes:** Each class and file must adhere strictly to the Single Responsibility Principle (SRP).
7. **NO Mixing Layer Responsibilities:** Presentation components must never perform media processing or direct API calls.
8. **NO Hardcoded Paths:** Use environment configuration or relative workspace resolution.
