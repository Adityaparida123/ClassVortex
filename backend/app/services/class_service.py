from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def create_class(data: dict) -> dict:
    db = get_database()
    data["created_at"] = datetime.now(timezone.utc)
    data["is_active"] = True
    result = await db.classes.insert_one(data)
    data["id"] = str(result.inserted_id)
    return serialize_id(data)


async def get_classes(page: int = 1, limit: int = 20) -> tuple:
    db = get_database()
    skip = (page - 1) * limit
    cursor = db.classes.find().skip(skip).limit(limit)
    classes = []
    async for cls in cursor:
        classes.append(serialize_id(cls))
    total = await db.classes.count_documents({})
    return classes, total


async def get_class_by_id(class_id: str) -> Optional[dict]:
    db = get_database()
    cls = await db.classes.find_one({"_id": ObjectId(class_id)})
    return serialize_id(cls) if cls else None


async def update_class(class_id: str, data: dict) -> Optional[dict]:
    db = get_database()
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        return await get_class_by_id(class_id)

    result = await db.classes.find_one_and_update(
        {"_id": ObjectId(class_id)},
        {"$set": update_data},
        return_document=True,
    )
    return serialize_id(result) if result else None


async def delete_class(class_id: str) -> bool:
    db = get_database()
    result = await db.classes.delete_one({"_id": ObjectId(class_id)})
    return result.deleted_count > 0
