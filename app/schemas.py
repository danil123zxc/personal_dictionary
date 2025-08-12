from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str
    confirm_password: str
    
    @field_validator('confirm_password')
    def passwords_match(cls, v: str, *, info: Optional[ValidationInfo] = None):
        if info:
            password = info.data.get('password')

            if password != v:
                raise ValueError("Passwords do not match")
            
        if not v or len(v) < 8:
            raise ValueError("Length of your password must be at least 8 characters")
    
        return v
    

    
class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True