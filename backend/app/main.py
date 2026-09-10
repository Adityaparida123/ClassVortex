import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection

logger = logging.getLogger("attendvortex.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do not crash the app if MongoDB is unreachable at startup (e.g. missing
    # or wrong MONGODB_URI on Render). Boot anyway so /health can report the
    # service is up; DB-dependent routes will surface clear errors instead of
    # the process crash-looping and the platform returning 404.
    try:
        await connect_to_mongo()
    except Exception as e:
        logger.error(
            "MongoDB connection failed at startup: %s: %s", e.__class__.__name__, e
        )
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https:\/\/.*\.vercel\.app|https:\/\/.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.routers import auth, users, students, classes, subjects
from app.routers import attendance, reports, exports, ai, sheets_import

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(classes.router)
app.include_router(subjects.router)
app.include_router(attendance.router)
app.include_router(reports.router)
app.include_router(exports.router)
app.include_router(ai.router)
app.include_router(sheets_import.router)


@app.get("/", tags=["Root"])
async def read_root():
    return {
        "app": settings.APP_NAME,
        "message": "AttendVortex API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from app.database import get_database

    db_status = "disconnected"
    db = get_database()
    if db is not None:
        try:
            await db.command("ping")
            db_status = "connected"
        except Exception:
            db_status = "error"
    return {"status": "ok", "app": settings.APP_NAME, "database": db_status}
