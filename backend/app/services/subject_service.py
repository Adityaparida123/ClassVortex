from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def create_subject(data: dict) -> dict:
    db = get_database()
    existing = await db.subjects.find_one({"code": data["code"]})
    if existing:
        raise ValueError("Subject code already exists")

    data["created_at"] = datetime.now(timezone.utc)
    data["is_active"] = True
    result = await db.subjects.insert_one(data)
    data["id"] = str(result.inserted_id)
    return serialize_id(data)


async def get_subjects(
    page: int = 1, limit: int = 20, class_id: Optional[str] = None
) -> tuple:
    db = get_database()
    query = {}
    if class_id:
        query["class_id"] = class_id

    skip = (page - 1) * limit
    cursor = db.subjects.find(query).skip(skip).limit(limit)
    subjects = []
    async for subject in cursor:
        subjects.append(serialize_id(subject))
    total = await db.subjects.count_documents(query)
    return subjects, total


async def get_subject_by_id(subject_id: str) -> Optional[dict]:
    db = get_database()
    subject = await db.subjects.find_one({"_id": ObjectId(subject_id)})
    return serialize_id(subject) if subject else None


async def update_subject(subject_id: str, data: dict) -> Optional[dict]:
    db = get_database()
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        return await get_subject_by_id(subject_id)

    result = await db.subjects.find_one_and_update(
        {"_id": ObjectId(subject_id)},
        {"$set": update_data},
        return_document=True,
    )
    return serialize_id(result) if result else None


async def delete_subject(subject_id: str) -> bool:
    db = get_database()
    result = await db.subjects.delete_one({"_id": ObjectId(subject_id)})
    return result.deleted_count > 0
