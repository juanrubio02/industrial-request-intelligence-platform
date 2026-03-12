from pydantic import BaseModel, ConfigDict, Field


class CreateDocumentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    original_filename: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class UpdateDocumentVerifiedDataRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    verified_structured_data: dict[str, str]
