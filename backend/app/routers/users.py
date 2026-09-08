from fastapi import APIRouter, Depends
from app.services import auth_service
from app.core.dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("", response_model=dict)
async def list_users(
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_admin_user),
):
    users, total = await auth_service.get_all_users(page=page, limit=limit)
    return {
        "success": True,
        "data": users,
        "pagination": {"page": page, "limit": limit, "total": total},
    }
