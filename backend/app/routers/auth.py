from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest):
    try:
        user = await auth_service.register_user(
            name=request.name,
            email=request.email,
            password=request.password,
            role=request.role,
        )
        return {"success": True, "data": user}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=dict)
async def login(request: LoginRequest):
    user = await auth_service.authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = await auth_service.create_user_token(user)
    return {"success": True, "data": token}


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    current_user.pop("password_hash", None)
    if "_id" in current_user:
        current_user["id"] = str(current_user.pop("_id"))
    return {"success": True, "data": current_user}
