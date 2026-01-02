from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from api.auth.middleware import AuthMiddleware
from api.games.router import router as games_router
from api.pci.router import router as pci_router
from api.questions.router import router as questions_router
from api.common.exceptions import ChessCoachError
from api.common.config import settings
from api.common.database import engine
from api.common.models import Base
from jose import jwt
import datetime
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(title="Chess-in-One AI Coach")
print("BACKEND VERSION 2.0 STARTING")

# Initialize database tables on startup
@app.on_event("startup")
async def init_database():
    """Ensure all database tables exist on startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"WARNING: Failed to initialize database tables: {e}")
        print("You may need to run: python backend/scripts/init_db.py")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"DEBUG: Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"DEBUG: Response status: {response.status_code}")
    return response

# Add CORS Middleware (MUST BE BEFORE AuthMiddleware to handle preflights correctly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Authentication Middleware
app.add_middleware(AuthMiddleware)

# Global exception handler
@app.exception_handler(ChessCoachError)
async def chess_coach_exception_handler(request: Request, exc: ChessCoachError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "type": exc.__class__.__name__}
    )

# Include Routers
app.include_router(games_router)
app.include_router(pci_router)
app.include_router(questions_router)

# Resolve path to web/build
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
pci_static_path = os.path.join(base_dir, "web", "build")
print("DEBUG: PCI static path:", pci_static_path)

if os.path.exists(pci_static_path):
    # Mount the entire build directory with SPA support
    app.mount("/pci-gui", StaticFiles(directory=pci_static_path, html=True), name="pci-gui")
    app.mount("/pci-ui", StaticFiles(directory=pci_static_path, html=True), name="pci-ui")

    # Redirect root to PCI route in HashRouter
    @app.get("/pci-gui")
    async def serve_pci_gui_root():
        return RedirectResponse(url="/pci-gui/#/pci")

    @app.get("/pci-ui")
    async def serve_pci_ui_root():
        return RedirectResponse(url="/pci-ui/#/pci")
else:
    print("WARNING: PCI static path not found at", pci_static_path)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Chess-in-One AI Coach API"}

@app.get("/dev/token")
async def get_dev_token(request: Request, role: str = "CHILD"):
    """
    Development-only endpoint to generate a JWT token.
    Enabled when either:
    - JWT_SECRET is still the placeholder secret (skeleton/dev), OR
    - ALLOW_DEV_TOKEN_ENDPOINT=1 is set AND the request comes from loopback.
    """
    client_host = getattr(getattr(request, "client", None), "host", None)
    is_loopback = client_host in ("127.0.0.1", "::1", "localhost")

    allow_dev = settings.JWT_SECRET == "placeholder_secret_for_skeleton" or (
        settings.ALLOW_DEV_TOKEN_ENDPOINT and is_loopback
    )

    if not allow_dev:
        raise HTTPException(
            status_code=403,
            detail="Dev token endpoint disabled. Set ALLOW_DEV_TOKEN_ENDPOINT=1 for loopback dev access.",
        )
    
    # Validate role
    if role not in ["CHILD", "PARENT"]:
        raise HTTPException(status_code=400, detail="Role must be CHILD or PARENT")
    
    payload = {
        "sub": "dev-user",
        "role": role,
        "device_id": "dev-device",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=365)
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return {"token": token, "role": role}
