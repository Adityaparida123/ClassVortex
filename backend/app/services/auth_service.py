from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_database
from app.core.security import hash_password, verify_password, create_access_token
from app.utils.helpers import serialize_id


async def register_user(name: str, email: str, password: str, role: str = "teacher") -> dict:
    db = get_database()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise ValueError("Email already registered")

    user_data = {
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_data)
    user_data["id"] = str(result.inserted_id)
    return serialize_id(user_data)


async def authenticate_user(email: str, password: str) -> dict:
    db = get_database()
    user = await db.users.find_one({"email": email})
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


async def create_user_token(user: dict) -> dict:
    token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"], "role": user["role"]}
    )
    return {"access_token": token, "token_type": "bearer"}


async def get_user_by_id(user_id: str) -> dict:
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return serialize_id(user) if user else None


async def get_all_users(page: int = 1, limit: int = 20) -> tuple:
    db = get_database()
    skip = (page - 1) * limit
    cursor = db.users.find().skip(skip).limit(limit)
    users = []
    async for user in cursor:
        user.pop("password_hash", None)
        users.append(serialize_id(user))
    total = await db.users.count_documents({})
    return users, total
