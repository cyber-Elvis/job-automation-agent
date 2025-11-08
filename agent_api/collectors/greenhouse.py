from fastapi import APIRouter

router = APIRouter(prefix="/collectors/greenhouse", tags=["collectors: greenhouse"])

@router.get("/health")
def health():
    return {"ok": True, "source": "greenhouse"}