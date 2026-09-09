from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def create_subject(data: dict, teacher_id: str) -> dict:
    db = get_database()
    existing = await db.subjects.find_one(
        {"teacher_id": teacher_id, "code": data["code"]}
    )
    if existing:
        raise ValueError("Subject code already exists")

    data["teacher_id"] = teacher_id
    data["created_at"] = datetime.now(timezone.utc)
    data["is_active"] = True
    result = await db.subjects.insert_one(data)
    data["id"] = str(result.inserted_id)
    return serialize_id(data)


async def get_subjects(
    teacher_id: str, page: int = 1, limit: int = 20, class_id: Optional[str] = None
) -> tuple:
    db = get_database()
    query = {"teacher_id": teacher_id}
    if class_id:
        query["class_id"] = class_id

    skip = (page - 1) * limit
    cursor = db.subjects.find(query).skip(skip).limit(limit)
    subjects = []
    async for subject in cursor:
        subjects.append(serialize_id(subject))
    total = await db.subjects.count_documents(query)
    return subjects, total


async def get_subject_by_id(subject_id: str, teacher_id: str) -> Optional[dict]:
    db = get_database()
    try:
        subject = await db.subjects.find_one(
            {"_id": ObjectId(subject_id), "teacher_id": teacher_id}
        )
    except Exception:
        return None
    return serialize_id(subject) if subject else None


async def update_subject(subject_id: str, data: dict, teacher_id: str) -> Optional[dict]:
    db = get_database()
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        return await get_subject_by_id(subject_id, teacher_id)

    if "code" in update_data and update_data.get("code"):
        existing = await db.subjects.find_one(
            {"teacher_id": teacher_id, "code": update_data["code"], "_id": {"$ne": ObjectId(subject_id)}}
        )
        if existing:
            raise ValueError("Subject code already exists")

    try:
        result = await db.subjects.find_one_and_update(
            {"_id": ObjectId(subject_id), "teacher_id": teacher_id},
            {"$set": update_data},
            return_document=True,
        )
    except Exception:
        return None
    return serialize_id(result) if result else None


async def delete_subject(subject_id: str, teacher_id: str) -> bool:
    db = get_database()
    try:
        result = await db.subjects.delete_one(
            {"_id": ObjectId(subject_id), "teacher_id": teacher_id}
        )
    except Exception:
        return False
    return result.deleted_count > 0