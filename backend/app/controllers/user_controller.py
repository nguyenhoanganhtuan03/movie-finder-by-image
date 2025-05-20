from fastapi import HTTPException

import hashlib
from app.entities.user_model import UserModel, PasswordChangeRequest
from app.database import db

from pymongo import ReturnDocument

# Hàm mã hóa mật khẩu đơn giản
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Hàm đăng ký người dùng
async def get_next_user_id():
    result = await db["counters"].find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.BEFORE
    )
    if result is None:
        return "user_1"
    else:
        return f"user_{result['seq'] + 1}"

async def register_user(name: str, email: str, password: str):
    existing_user = await db["users"].find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = await get_next_user_id()

    hashed_password = hash_password(password)

    user = UserModel(
        _id=user_id,
        name=name,
        email=email,
        password=hashed_password
    )

    user_dict = user.dict()
    user_dict['_id'] = user_id

    await db["users"].insert_one(user_dict)

    return {"message": "User registered successfully", "user_id": user_id}

# Hàm đăng nhập người dùng
async def login_user(email: str, password: str):
    # Kiểm tra xem người dùng có tồn tại với email không
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Kiểm tra mật khẩu
    hashed_password = hash_password(password)
    if user["password"] != hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect password")

    # Trả về thông báo thành công và thông tin người dùng
    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "id": str(user["_id"]),
            "name": str(user["name"]),
            "email": user["email"],
        }
    }

# Hiển thị danh sách tất cả người dùng
async def get_all_users():
    users_cursor = db["users"].find({}, {"password": 0})
    users = await users_cursor.to_list(length=None)

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users

# Tìm kiếm người dùng bằng tên (không phân biệt hoa thường)
async def get_user_by_name(name: str):
    # Tìm user có tên chứa chuỗi name (không phân biệt hoa thường), ẩn mật khẩu
    users_cursor = db["users"].find(
        {"name": {"$regex": name, "$options": "i"}},  # "$options": "i" để không phân biệt hoa thường
        {"password": 0}
    )
    users = await users_cursor.to_list(length=None)

    if not users:
        raise HTTPException(status_code=404, detail="No matching users found")

    return users

# Cập nhật mật khẩu người dùng
async def update_password_by_id(user_id: str, data: PasswordChangeRequest):
    hashed_old_password = hash_password(data.old_password)
    hashed_new_password = hash_password(data.new_password)

    # Tìm user theo _id và old_password đã hash
    user = await db["users"].find_one({"_id": user_id, "password": hashed_old_password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user ID or old password")

    result = await db["users"].update_one(
        {"_id": user_id},
        {"$set": {"password": hashed_new_password}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update password")

    return {"message": "Password updated successfully"}

# Xóa người dùng theo _id
async def delete_user_by_id(user_id: str):
    result = await db["users"].delete_one({"_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User '{user_id}' deleted successfully"}

# Tìm kiếm user theo _id
async def get_user_by_id(user_id: str):
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"]) 
    return user