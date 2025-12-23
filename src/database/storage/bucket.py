import uuid
from sqlmodel import Field, SQLModel, UniqueConstraint


class Bucket(SQLModel, table=True):
    __tablename__ = "bucket"
    __table_args__ = (
        UniqueConstraint("owner", "name", name="unique_owner_bucket_name"),
        {"schema": "storage"},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, nullable=False)
    owner: uuid.UUID = Field(
        nullable=False,
        index=True
    )
