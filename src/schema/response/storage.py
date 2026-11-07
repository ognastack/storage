from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MainResponse(BaseModel):
    accepted: bool = Field(default=True, description="Indicates whether the request was accepted and processed")


class FileAccepted(MainResponse):
    url: str = Field(
        ...,
        description="Presigned URL to access or download the uploaded file",
        examples=["https://s3.example.com/bucket-id/report.pdf?X-Amz-Signature=..."]
    )
    file_id: str = Field(
        ...,
        description="Unique identifier of the stored file record",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )


class NewBucket(MainResponse):
    pass


class ErrorResponse(BaseModel):
    error: bool = Field(default=True, description="Always true when an error occurs")
    message: str = Field(..., description="Human-readable error message", examples=["Resource not found"])
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional additional error context")
    request_id: Optional[str] = Field(default=None, description="Request correlation ID")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Current health status of the service", examples=["healthy"])
    service: Optional[str] = Field(default=None, description="Service name", examples=["Ogna Storage"])
    version: Optional[str] = Field(default=None, description="Service version", examples=["1.0.0"])
    environment: Optional[str] = Field(default=None, description="Deployment environment", examples=["development"])
