import uuid

from pydantic import BaseModel, Field
from typing import Optional


class Bucket(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=63,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,61}[a-zA-Z0-9]$",
        description="Unique bucket name (3-63 alphanumeric, dot, underscore, or hyphen characters)",
        examples=["my-assets-bucket"]
    )
    public: bool = Field(default=False, description="Whether the bucket is publicly accessible", examples=[False])
    id: Optional[uuid.UUID] = Field(default=None, description="UUID of the bucket")
    owner: Optional[uuid.UUID] = Field(default=None, description="UUID of the bucket owner")


class FileObject(BaseModel):
    bucket_id: Optional[uuid.UUID] = Field(default=None, description="UUID of the bucket containing the file")
    id: Optional[uuid.UUID] = Field(default=None, description="UUID of the file record")
    last_modified: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp when the file was last modified",
        examples=["2026-11-07T10:00:00+00:00"]
    )
    name: Optional[str] = Field(default=None, description="File name / object key in the bucket", examples=["report.pdf"])


class NewObject(BaseModel):
    bucke_name: str = Field(..., description="Bucket Name")
    file_path: Optional[str] = Field(default="", description="Path to the file within the bucket")
