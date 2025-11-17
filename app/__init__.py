from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from . import routes
from .state import load_datasets, warm_cache_background, reset_company_cache


def _static_dir():
    # static 폴더는 프로젝트 루트 기준
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    reset_company_cache()
    load_datasets()
    warm_cache_background()
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes.router)

    static_dir = _static_dir()
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    return app
