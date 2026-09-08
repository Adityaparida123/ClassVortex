from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DATABASE]
    await create_indexes()


async def close_mongo_connection():
    global client
    if client:
        client.close()


async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.students.create_index("roll_number", unique=True)
    await db.students.create_index("class_id")
    await db.classes.create_index("name")
    await db.subjects.create_index("name")
    await db.attendance_sessions.create_index("date")
    await db.attendance_sessions.create_index("class_id")
    await db.attendance_sessions.create_index("subject_id")
    await db.attendance_records.create_index("session_id")
    await db.attendance_records.create_index("student_id")


def get_database() -> AsyncIOMotorDatabase:
    return db


def set_database(test_db: AsyncIOMotorDatabase):
    global db
    db = test_db
