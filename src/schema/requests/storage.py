from pydantic import BaseModel, Field
from typing import Optional

class Bucket(BaseModel):
    name: str = Field(..., description="Bucket Name")
    public: bool = Field(default=False, description="Bucket Visibility")


class NewObject(BaseModel):
    bucke_name:str = Field(..., description="Bucket Name")
    file_path: Optional[str] = Field(default="", description="Bucket Name")