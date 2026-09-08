from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
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
from app.routers import attendance, reports, exports, ai

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(classes.router)
app.include_router(subjects.router)
app.include_router(attendance.router)
app.include_router(reports.router)
app.include_router(exports.router)
app.include_router(ai.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}
