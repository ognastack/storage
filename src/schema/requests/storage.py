import uuid

from pydantic import BaseModel, Field
from typing import Optional


class Bucket(BaseModel):
    name: Optional[str] = Field(..., description="Bucket Name")
    public: bool = Field(default=False, description="Bucket Visibility")
    id: Optional[uuid.UUID] = Field(default=None, description="UID of the bucket")
    owner: Optional[uuid.UUID] = Field(default=None, description="UID of the bucket ownder")


class FileObject(BaseModel):
    bucket_id: Optional[uuid.UUID] = Field(default=None, description="UID of the bucket")
    id: Optional[uuid.UUID] = Field(default=None, description="UID of the file")
    last_modified: Optional[str] = Field(default=None, description="Last modified string")
    name: Optional[str] = Field(default=None, description="UID of the bucket")


class NewObject(BaseModel):
    bucke_name: str = Field(..., description="Bucket Name")
    file_path: Optional[str] = Field(default="", description="Bucket Name")
