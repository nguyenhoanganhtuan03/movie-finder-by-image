from pydantic import BaseModel, EmailStr

class UserModel(BaseModel):
    _id: str
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str