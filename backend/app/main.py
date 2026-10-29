"""
SIGMA_ASR_VTT - FastAPI ASGI Backend Entrypoint
Developer: أصيل السويدي
"""

import asyncio
import sys

# Fix: asyncio subprocess support on Windows requires ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


import secrets
import traceback
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.models import SystemHardwareInfo
from app.infrastructure.logger import logger, record_error_event, get_recent_errors, clear_error_logs
import psutil
import platform

from contextlib import asynccontextmanager
from app.services.garbage_collector import garbage_collector_task
from app.api.router import router as api_router
from app.api.websocket import router as ws_router
from app.api.batch_router import router as batch_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start garbage collector background task
    gc_task = asyncio.create_task(garbage_collector_task())
    yield
    # Stop garbage collector on shutdown
    gc_task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=f"Backend Services Engine for {settings.PROJECT_NAME} by {settings.DEVELOPER}",
    lifespan=lifespan
)

app.include_router(api_router)
app.include_router(ws_router)
app.include_router(batch_router)
settings.SESSION_TOKEN = secrets.token_hex(16)
logger.info(f"Generated Session Security Token for Local Bridge: {settings.SESSION_TOKEN[:4]}...****")

ALLOWED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:54321",
    "http://localhost:54321",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def license_gatekeeper_middleware(request: Request, call_next):
    """Enforces active hardware-bound Ed25519 license across all protected API routes."""
    if request.method == "OPTIONS":
        return await call_next(request)
        
    path = request.url.path
    # Public routes that must be accessible before license activation
    public_prefixes = [
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/license/",
        "/api/v1/system/session-token",
        "/api/v1/system/info"
    ]
    if path == "/" or any(path.startswith(p) for p in public_prefixes) or not path.startswith("/api/v1"):
        return await call_next(request)

    from app.core.licensing import HWIDGenerator, LicenseValidator
    hwid = HWIDGenerator.generate()
    validator = LicenseValidator()
    result = validator.validate_cached(hwid)
    if not result.is_authorized():
        return JSONResponse(
            status_code=403,
            content={
                "detail": "LICENSE_REQUIRED",
                "message": result.message,
                "hwid": hwid
            }
        )

    return await call_next(request)

from fastapi.responses import FileResponse

@app.get("/api/v1/status")
async def api_status():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "developer": settings.DEVELOPER,
        "session_token_active": bool(settings.SESSION_TOKEN)
    }

@app.get("/")
async def root():
    frontend_dist = settings.FRONTEND_DIR
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Frontend not built yet. Run npm run build in frontend directory."}

@app.get("/admin/keygen", response_class=HTMLResponse)
async def admin_keygen_page():
    """Serves Developer Master KeyGen Web Dashboard (Only in DEBUG mode)."""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Page not found")
    keygen_file = Path(__file__).resolve().parent / "static" / "admin_keygen.html"
    if keygen_file.exists():
        return HTMLResponse(content=keygen_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>404 - Keygen Dashboard Not Found</h1>", status_code=404)

@app.get("/api/v1/system/info", response_model=SystemHardwareInfo)
async def get_system_hardware_info():
    """Returns real hardware & OS metrics for Tab 4."""
    ram = psutil.virtual_memory()
    return SystemHardwareInfo(
        os_name=f"{platform.system()} {platform.release()} ({platform.machine()})",
        cpu_name=platform.processor() or "AMD/Intel x86_64 Processor",
        cpu_cores_physical=psutil.cpu_count(logical=False) or 4,
        cpu_cores_logical=psutil.cpu_count(logical=True) or 8,
        ram_total_gb=round(ram.total / (1024**3), 2),
        ram_available_gb=round(ram.available / (1024**3), 2),
        python_version=platform.python_version(),
        app_version=settings.VERSION
    )

@app.get("/api/v1/system/session-token")
async def get_system_session_token():
    """Returns the local session token required for WebSocket authentication."""
    return {"session_token": settings.SESSION_TOKEN}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions, records diagnostic info, and returns clean structured error response."""
    tb = traceback.extract_tb(exc.__traceback__)
    last_frame = tb[-1] if tb else None

    event = record_error_event(
        error_type=exc.__class__.__name__,
        message=str(exc),
        module=last_frame.filename if last_frame else "unknown",
        function=last_frame.name if last_frame else "unknown",
        line_no=last_frame.lineno if last_frame else 0,
        traceback_str="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        context={
            "url": str(request.url),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    logger.error(f"Global Exception: {exc.__class__.__name__} at {event['module']}:{event['line_number']} - {str(exc)}")
    
    error_message = str(exc) if settings.DEBUG else "حدث خطأ داخلي غير متوقع أثناء معالجة العملية."
    location_info = f"{event['function']}:{event['line_number']}" if settings.DEBUG else "hidden"
    error_type_info = exc.__class__.__name__ if settings.DEBUG else "InternalServerError"

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": error_type_info,
            "message": error_message,
            "location": location_info,
            "timestamp": event["timestamp"]
        }
    )

@app.get("/api/v1/system/debug-logs")
async def get_system_debug_logs(limit: int = 20):
    """Returns real-time captured errors with exact file, function, line number, and stack traces (Debug only)."""
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Debug logs are only accessible in DEBUG mode.")
    errors = get_recent_errors(limit=limit)
    return {
        "count": len(errors),
        "errors": errors
    }

@app.delete("/api/v1/system/debug-logs")
async def clear_system_debug_logs():
    """Clears the live error buffer."""
    clear_error_logs()
    return {"status": "cleared", "message": "Error buffer reset successfully."}

# ── Serve Built Frontend (Production Mode) ──
frontend_dist = settings.FRONTEND_DIR
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
