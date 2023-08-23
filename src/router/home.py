from fastapi import APIRouter, Cookie
from fastapi.responses import RedirectResponse


router = APIRouter()


@router.get("/")
async def homepage() -> RedirectResponse:
    return RedirectResponse(url="/notebook/publish/t/t.tt/index.html")
