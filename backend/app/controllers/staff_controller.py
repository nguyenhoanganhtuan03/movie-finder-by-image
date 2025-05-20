import hashlib
from fastapi import HTTPException
from pymongo import ReturnDocument

from app.database import db
from app.entities.staff_model import StaffModel, StaffPasswordChangeRequest

# Hàm hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def get_next_staff_id():
    result = await db["counters"].find_one_and_update(
        {"_id": "staff_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.BEFORE
    )
    if result is None:
        return "staff_1"
    else:
        return f"staff_{result['seq'] + 1}"
    
async def register_staff(name: str, email: str, position: str, password: str):
    existing_staff = await db["staffs"].find_one({"email": email})
    if existing_staff:
        raise HTTPException(status_code=400, detail="Email already registered")

    staff_id = await get_next_staff_id()
    hashed_password = hash_password(password)

    staff = StaffModel(
        _id=staff_id,
        name=name,
        email=email,
        position=position,
        password=hashed_password
    )

    staff_dict = staff.dict()
    staff_dict['_id'] = staff_id

    await db["staffs"].insert_one(staff_dict)

    return {"message": "Staff registered successfully", "staff_id": staff_id}

async def login_staff(email: str, password: str):
    staff = await db["staffs"].find_one({"email": email})
    if not staff:
        raise HTTPException(status_code=400, detail="Staff not found")

    hashed_password = hash_password(password)
    if staff["password"] != hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {
        "status": "success",
        "message": "Login successful",
        "staff": {
            "id": str(staff["_id"]),
            "name": str(staff["name"]),
            "email": staff["email"],
            "position": staff["position"]
        }
    }

# Cập nhật mật khẩu staff
async def update_password_by_staff_id(staff_id: str, data: StaffPasswordChangeRequest):
    hashed_old_password = hash_password(data.old_password)
    hashed_new_password = hash_password(data.new_password)

    # Tìm staff theo _id và old_password đã hash
    staff = await db["staffs"].find_one({"_id": staff_id, "password": hashed_old_password})
    if not staff:
        raise HTTPException(status_code=401, detail="Invalid staff ID or old password")

    result = await db["staffs"].update_one(
        {"_id": staff_id},
        {"$set": {"password": hashed_new_password}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update password")

    return {"message": "Password updated successfully"}