from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import DiscoverRequest, DiscoverResponse, PrefillRequest, PrefillResponse
from .services.discovery import discover_jobs
from .services.prefill import prefill_application
from .config import settings


app = FastAPI(title=settings.APP_NAME)


# CORS
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(',') if o.strip()]
app.add_middleware(
CORSMiddleware,
allow_origins=origins or ["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)


@app.get("/health")
async def health():
return {"status": "ok", "env": settings.APP_ENV}


@app.post("/discover", response_model=DiscoverResponse)
async def discover(payload: DiscoverRequest):
items = discover_jobs(payload)
return DiscoverResponse(items=items, count=len(items))


@app.post("/prefill", response_model=PrefillResponse)
async def prefill(payload: PrefillRequest):
return prefill_application(payload)