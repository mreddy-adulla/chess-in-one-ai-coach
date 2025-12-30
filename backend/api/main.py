from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from api.auth.middleware import AuthMiddleware
from api.games.router import router as games_router
from api.pci.router import router as pci_router
import os

app = FastAPI(title="Chess-in-One AI Coach")
print("BACKEND VERSION 2.0 STARTING")

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

# Include Routers
app.include_router(games_router)
app.include_router(pci_router)

# Resolve path to web/build
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
pci_static_path = os.path.join(base_dir, "web", "build")
pci_static_assets_path = os.path.join(pci_static_path, "static")

if os.path.exists(pci_static_assets_path):
    # Mount static files
    app.mount("/pci-gui/static", StaticFiles(directory=pci_static_assets_path), name="static")
    
if os.path.exists(os.path.join(pci_static_path, "index.html")):
    @app.get("/pci-gui/{path:path}")
    async def serve_pci_gui(path: str):
        # Serve index.html for any path under /pci-gui/ (SPA support)
        index_path = os.path.join(pci_static_path, "index.html")
        return FileResponse(index_path)
    
    @app.get("/pci-gui")
    async def serve_pci_gui_root():
        # Redirect to the PCI route in the HashRouter
        return RedirectResponse(url="/pci-gui/#/pci")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Chess-in-One AI Coach API"}
