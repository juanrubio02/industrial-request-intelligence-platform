from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateDocumentCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    request_id: UUID
    organization_id: UUID
    uploaded_by_membership_id: UUID
    original_filename: str = Field(min_length=1, max_length=255)
    storage_key: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class UploadDocumentCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    request_id: UUID
    organization_id: UUID
    uploaded_by_membership_id: UUID
    original_filename: str = Field(max_length=255)
    content_type: str | None = Field(default=None, max_length=255)
    content: bytes


class EnqueueDocumentProcessingCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: UUID
    organization_id: UUID


class UpdateDocumentVerifiedDataCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: UUID
    organization_id: UUID
    membership_id: UUID
    verified_structured_data: dict[str, str]
