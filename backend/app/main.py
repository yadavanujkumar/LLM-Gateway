import structlog
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.routers import auth, chat, embeddings, usage, models, billing

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.DEBUG if settings.DEBUG else logging.INFO
    ),
    logger_factory=structlog.PrintLoggerFactory(),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: close Redis
    from app.services.cache import close_redis
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A production-ready LLM-as-a-Service platform supporting OpenAI, Llama, and Mistral models.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
app.add_middleware(LoggingMiddleware)

# Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(embeddings.router)
app.include_router(usage.router)
app.include_router(models.router)
app.include_router(billing.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
