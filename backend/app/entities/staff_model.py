from pydantic import BaseModel, EmailStr

class StaffModel(BaseModel):
    _id: str
    name: str
    email: EmailStr
    position: str
    password: str

class StaffLoginRequest(BaseModel):
    email: str
    password: str

class StaffPasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str