from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=25)


class UserLogin(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class UserInDB(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None