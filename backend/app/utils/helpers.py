from bson import ObjectId


def serialize_mongo_doc(doc: dict) -> dict:
    if doc is None:
        return None
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_mongo_doc(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_mongo_doc(item) if isinstance(item, dict) else
                str(item) if isinstance(item, ObjectId) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def serialize_id(doc: dict) -> dict:
    if doc is None:
        return None
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise ValueError(f"Invalid ObjectId: {id_str}")


def prepare_for_mongo(data: dict) -> dict:
    result = {}
    for key, value in data.items():
        if key == "id":
            continue
        result[key] = value
    return result
