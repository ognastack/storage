from pydantic import BaseModel, Field


class MainResponse(BaseModel):
    accepted: bool = Field(default=True, description="Request has been accepted")


class FileAccepted(MainResponse):
    url: str = Field(..., description="File direct url")


class NewBucket(MainResponse):
    pass
