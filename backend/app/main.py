from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import auth, cases, evidence, audit_logs

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Investigation Platform API",
    description="MVP backend: auth, case management, evidence chain-of-custody, audit log.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(audit_logs.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
