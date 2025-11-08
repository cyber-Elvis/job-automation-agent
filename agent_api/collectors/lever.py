from fastapi import APIRouter

router = APIRouter(prefix="/collectors/lever", tags=["collectors: lever"])

@router.get("/health")
def health():
    return {"ok": True, "source": "lever"}