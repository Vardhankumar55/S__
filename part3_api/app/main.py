# Suppress warnings before any imports
import warnings
warnings.filterwarnings("ignore")
import os
os.environ["PYTHONWARNINGS"] = "ignore"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog
from prometheus_client import make_asgi_app
import traceback

from .config import settings
from .routes import router
from .errors import AppError

# Simple Structlog Config
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Spectral Lie Voice Detection API",
    debug=settings.DEBUG
)

# (Snippet of the current main.py on your machine)
@app.on_event("startup")
async def startup_event():
    import time
    startup_start = time.time()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] API Starting up...")
    
    try:
        from . import rate_limiter
        from . import orchestrator
        
        # 1. Initialize Redis (Optional - for caching only)
        # If Redis fails, app continues without caching
        try:
            await rate_limiter.init_redis()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Redis initialized (caching enabled)")
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Redis unavailable - continuing without caching: {e}")
        
        # 2. Preload Models (CRITICAL - must succeed)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Preloading ML models...")
        preload_start = time.time()
        
        orchestrator.preload_models()
        
        preload_duration = time.time() - preload_start
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Models preloaded in {preload_duration:.2f}s")
        
        # Verify models are ready
        if not orchestrator.is_model_loaded():
            raise RuntimeError("Model loading failed - API cannot serve requests")
        
        total_startup = time.time() - startup_start
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✓ Startup complete in {total_startup:.2f}s - Ready to serve requests")
        
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✗ STARTUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        # Re-raise to prevent unhealthy container from accepting traffic
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        from . import rate_limiter
        await rate_limiter.close_redis()
    except:
        pass

# Prometheus Metrics
app.mount("/metrics", make_asgi_app())

# Mount Static Files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure static directory exists
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_ui():
        return FileResponse(os.path.join(static_dir, "index.html"))


# App Routes
app.include_router(router)

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Flatten errors to a single message string
    error_messages = []
    for error in exc.errors():
        field = error.get("loc", ["unknown"])[-1]
        msg = error.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}")
        
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Malformed request: " + "; ".join(error_messages)
        }
    )

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message}
    )

# Robust Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException
    
    # Detailed logging for Render
    structlog.get_logger().error(
        "unhandled_exception", 
        error=str(exc), 
        traceback=traceback.format_exc()
    )
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "message": exc.detail}
        )
        
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error"
        }
    )
