from fastapi import APIRouter
from fastapi.responses import RedirectResponse, Response


router = APIRouter()


@router.get("/")
async def homepage() -> RedirectResponse:
    return RedirectResponse(url="/notebook/publish/t/t.tt/index.html")


@router.get("/favicon.ico")
async def favicon() -> Response:
    with open("src/static/favicon.ico", "rb") as f:
        content = f.read()
    return Response(content=content)
