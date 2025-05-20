from fastapi import APIRouter, FastAPI
from fastapi import Body, Path

from app.controllers.user_controller import register_user, login_user, get_all_users, get_user_by_name
from app.controllers.user_controller import update_password_by_id, delete_user_by_id, get_user_by_id
from app.entities.user_model import UserModel, LoginRequest, PasswordChangeRequest

app = FastAPI()
router = APIRouter()

# Route đăng ký người dùng
@router.post("/register")
async def register(user: UserModel):
    return await register_user(user.name, user.email, user.password)

# Route đăng nhập người dùng
@router.post("/login")
async def login(login_request: LoginRequest):
    return await login_user(login_request.email, login_request.password)

# Route lấy tất cả người dùng
@router.get("/users")
async def list_users():
    return await get_all_users()

# Route lấy người dùng theo tên
@router.get("/users/{name}")
async def get_user(name: str):
    return await get_user_by_name(name)

# Route cập nhật mật khẩu
@router.put("/users/update-password/{user_id}")
async def update_user_password(
    user_id: str = Path(...),
    data: PasswordChangeRequest = Body(...)
):
    return await update_password_by_id(user_id, data)

# Route xóa người dùng
@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    return await delete_user_by_id(user_id)

# Route tìm người dùng theo _id
@router.get("/{user_id}")
async def get_user_id(user_id: str):
    return await get_user_by_id(user_id)

# Thêm router vào FastAPI app
app.include_router(router)
