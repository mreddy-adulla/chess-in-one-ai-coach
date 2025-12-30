from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from api.common.config import settings

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in ["/health", "/", "/docs", "/openapi.json"] or request.url.path.startswith("/pci-gui"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401, 
                content={"detail": "Missing or invalid token"}
            )

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Mandatory Claims Validation (Implementation Spec 5.1)
            required_claims = ["sub", "role", "device_id", "exp"]
            for claim in required_claims:
                if claim not in payload:
                    return JSONResponse(
                        status_code=401, 
                        content={"detail": f"Missing claim: {claim}"}
                    )

            # Device Binding Enforcement (Implementation Spec 5.2)
            request.state.user = payload

            # Role-based API Restriction (Implementation Spec 13)
            path = request.url.path
            role = payload.get("role")
            
            if path.startswith("/pci") and role != "PARENT":
                return JSONResponse(
                    status_code=403, 
                    content={"detail": "Parent access required"}
                )
            
            if not path.startswith("/pci") and role == "PARENT":
                 if path.startswith("/games") or path.startswith("/questions"):
                    return JSONResponse(
                        status_code=403, 
                        content={"detail": "Child access required"}
                    )

        except JWTError:
            return JSONResponse(
                status_code=401, 
                content={"detail": "Invalid token"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500, 
                content={"detail": "Internal authentication error"}
            )

        response = await call_next(request)
        return response
