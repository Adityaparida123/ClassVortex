import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger("attendvortex.database")
logging.basicConfig(level=logging.INFO)

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


def get_client_kwargs() -> dict:
    kwargs = {
        "serverSelectionTimeoutMS": 10000,
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 45000,
    }
    uri = settings.MONGODB_URI
    if uri.startswith("mongodb+srv://") or "tls=true" in uri.lower() or "ssl=true" in uri.lower():
        kwargs["tlsCAFile"] = certifi.where()
    return kwargs


async def connect_to_mongo():
    global client, db
    logger.info("Connecting to MongoDB...")

    try:
        kwargs = get_client_kwargs()
        client = AsyncIOMotorClient(settings.MONGODB_URI, **kwargs)
        db = client[settings.MONGODB_DATABASE]

        # Explicit ping check before creating indexes
        await client.admin.command("ping")
        logger.info("MongoDB connection successful")

        await create_indexes()
        logger.info("MongoDB index initialization successful")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e.__class__.__name__}: {e}")
        raise


async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    if db is None:
        return
    try:
        await db.users.create_index("email", unique=True)
        await db.students.create_index(
            [("teacher_id", 1), ("roll_number", 1)], unique=True
        )
        await db.students.create_index("class_id")
        await db.students.create_index("teacher_id")
        await db.classes.create_index("name")
        await db.classes.create_index("teacher_id")
        await db.subjects.create_index("name")
        await db.subjects.create_index("teacher_id")
        await db.attendance_sessions.create_index("date")
        await db.attendance_sessions.create_index("class_id")
        await db.attendance_sessions.create_index("subject_id")
        await db.attendance_sessions.create_index("teacher_id")
        await db.attendance_records.create_index("session_id")
        await db.attendance_records.create_index("student_id")
        await db.attendance_records.create_index("teacher_id")
    except Exception as e:
        logger.error(f"Failed to create MongoDB indexes: {e.__class__.__name__}: {e}")
        raise


def get_database() -> AsyncIOMotorDatabase:
    return db


def set_database(test_db: AsyncIOMotorDatabase):
    global db
    db = test_db
