from pydantic import BaseModel, Field


class MainResponse(BaseModel):
    accepted: bool = Field(default=True, description="Request has been accepted")


class FileAccepted(MainResponse):
    url: str = Field(..., description="File direct url")
    file_id: str = Field(..., description="File storage id")


class NewBucket(MainResponse):
    pass
