from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from api.auth.middleware import AuthMiddleware
from api.games.router import router as games_router
from api.pci.router import router as pci_router
from api.common.exceptions import ChessCoachError
import os

app = FastAPI(title="Chess-in-One AI Coach")
print("BACKEND VERSION 2.0 STARTING")

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

# Resolve path to web/build
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
pci_static_path = os.path.join(base_dir, "web", "build")

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
