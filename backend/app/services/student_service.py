from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def create_student(data: dict) -> dict:
    db = get_database()
    existing = await db.students.find_one({"roll_number": data["roll_number"]})
    if existing:
        raise ValueError("Roll number already exists")

    data["created_at"] = datetime.now(timezone.utc)
    data["is_active"] = True
    result = await db.students.insert_one(data)
    data["id"] = str(result.inserted_id)
    return serialize_id(data)


async def get_students(
    page: int = 1,
    limit: int = 20,
    class_id: Optional[str] = None,
    semester: Optional[int] = None,
    section: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple:
    db = get_database()
    query = {}
    if class_id:
        query["class_id"] = class_id
    if semester:
        query["semester"] = semester
    if section:
        query["section"] = section
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"roll_number": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * limit
    cursor = db.students.find(query).skip(skip).limit(limit)
    students = []
    async for student in cursor:
        students.append(serialize_id(student))
    total = await db.students.count_documents(query)
    return students, total


async def get_student_by_id(student_id: str) -> Optional[dict]:
    db = get_database()
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    return serialize_id(student) if student else None


async def update_student(student_id: str, data: dict) -> Optional[dict]:
    db = get_database()
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        return await get_student_by_id(student_id)

    result = await db.students.find_one_and_update(
        {"_id": ObjectId(student_id)},
        {"$set": update_data},
        return_document=True,
    )
    return serialize_id(result) if result else None


async def delete_student(student_id: str) -> bool:
    db = get_database()
    result = await db.students.delete_one({"_id": ObjectId(student_id)})
    return result.deleted_count > 0


async def get_students_by_class(class_id: str) -> list:
    db = get_database()
    cursor = db.students.find({"class_id": class_id, "is_active": True})
    students = []
    async for student in cursor:
        students.append(serialize_id(student))
    return students
