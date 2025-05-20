from fastapi import APIRouter, FastAPI
from fastapi import Body, Path

from app.controllers.staff_controller import register_staff, login_staff, update_password_by_staff_id
from app.entities.staff_model import StaffModel, StaffLoginRequest, StaffPasswordChangeRequest

app = FastAPI()
router = APIRouter()

# Route đăng ký staff
@router.post("/register")
async def register(staff: StaffModel):
    return await register_staff(staff.name, staff.email, staff.position, staff.password)

# Route đăng nhập staff
@router.post("/login")
async def login(login_request: StaffLoginRequest):
    return await login_staff(login_request.email, login_request.password)

# Route đổi mật khẩu staff
@router.put("/update-password/{staff_id}")
async def update_staff_password(
    staff_id: str = Path(...),
    data: StaffPasswordChangeRequest = Body(...)
):
    return await update_password_by_staff_id(staff_id, data)

# Đăng ký router vào FastAPI app
app.include_router(router)