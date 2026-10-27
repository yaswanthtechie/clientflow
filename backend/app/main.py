import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routes.auth import router as auth_router
from app.routes.clients import router as clients_router
from app.routes.projects import router as projects_router
from app.security import get_current_user_id

logger = logging.getLogger(__name__)

app = FastAPI(title="ClientFlow API", version="0.1.0")

app.include_router(auth_router)
app.include_router(clients_router)

app.include_router(projects_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "clientflow-api"}


@app.get("/health/ready", tags=["system"])
def readiness_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        logger.exception("Database readiness check failed")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from None


@app.get("/auth/me", tags=["authentication"])
def get_current_user(
    user_id: int = Depends(get_current_user_id),
) -> dict[str, int]:
    return {"user_id": user_id}
