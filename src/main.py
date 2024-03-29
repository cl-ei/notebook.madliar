from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from src.framework.midddleware import ErrorCatchMiddleware
from src.router import notebook, home
from src.framework.config import DEBUG, BLOG_ROOT

PROJECT_NAME = "notebook.madliar"
VERSION = "1.0"


def get_application() -> FastAPI:
    application = FastAPI(
        title=PROJECT_NAME,
        debug=DEBUG,
        version=VERSION,
        openapi_url="",
        docs_url="",
        redoc_url="",
        swagger_ui_oauth2_redirect_url="",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(ErrorCatchMiddleware)
    application.mount("/notebook/static", StaticFiles(directory="src/static"), name="static")
    application.mount("/notebook/publish", StaticFiles(directory=BLOG_ROOT), name="blog")
    application.include_router(notebook.router, prefix="/notebook", tags=["notebook"])
    application.include_router(home.router, prefix="", tags=["home"])

    return application


app = get_application()
