import uuid
from sqlmodel import Field, SQLModel

from datetime import datetime
import uuid
from sqlmodel import Field, SQLModel, func, Column, DateTime


class Objects(SQLModel, table=True):
    __tablename__ = "object"
    __table_args__ = (
        {"schema": "storage"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, nullable=False)
    bucket_id: uuid.UUID = Field(foreign_key="storage.bucket.id", nullable=False)
    last_modified: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now()
        )
    )
