from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)
