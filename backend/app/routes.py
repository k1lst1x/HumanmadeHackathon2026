from fastapi import APIRouter

router = APIRouter()


@router.get("/status", tags=["system"])
def status() -> dict[str, str]:
    return {"backend": "ready"}
