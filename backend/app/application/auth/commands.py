from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=1, max_length=255)
