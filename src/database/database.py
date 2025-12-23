import logging
import uuid
from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine, select
from config.settings import settings
from sqlalchemy import text
from contextlib import contextmanager

from src.database.storage.bucket import Bucket
from src.database.storage.objects import Objects
from src.schema.requests.storage import Bucket as BaseBucket

from src.core.exceptions import BucketNotFound

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Build PostgreSQL connection URL
DATABASE_URL = f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_URL}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)


def create_db_and_tables():
    # Create schemas FIRST, before creating tables
    with engine.connect() as conn:
        logger.info("Creating schemas")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS storage"))
        # Add any other schemas you need
        # conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        conn.commit()

    # Then create tables
    logger.info("Creating tables")
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


class DatabaseEngine:

    def get_bucket_by_id(self, bucket_id: str):
        with get_session() as session:
            statement = select(Bucket).where(Bucket.id == bucket_id)
            return session.exec(statement).first()

    def get_bucket_by_id_user(self, bucket_name: str, owner_id: uuid.UUID) -> Bucket:
        with get_session() as session:
            statement = select(Bucket).where(
                Bucket.name == bucket_name,
                Bucket.owner == owner_id
            )
            return session.exec(statement).first()

    def create_bucket(cls, bucket_data: BaseBucket, user_id: uuid.UUID) -> Bucket:
        with get_session() as session:
            bucket = Bucket(
                name=bucket_data.name,
                owner=user_id
            )
            session.add(bucket)
            session.commit()
            session.refresh(bucket)
            return bucket

    def get_file(self, bucket_name: str, file_name: str, owner_id: uuid.UUID):
        with get_session() as session:
            statement = select(Bucket, Objects).where(
                Bucket.id == Objects.bucket_id,
                Bucket.name == bucket_name,
                Objects.name == file_name,
                Bucket.owner == owner_id
            )
            return session.exec(statement).first()

    def create_file(self, bucket_name: str, file_name: str, owner_id: uuid.UUID) -> Objects:
        bucket_data = self.get_bucket_by_id_user(
            bucket_name=bucket_name,
            owner_id=owner_id
        )

        if bucket_data is None:
            raise BucketNotFound(bucket_name)

        search_file = self.get_file(
            bucket_name=bucket_data.name,
            file_name=file_name,
            owner_id=owner_id
        )

        if search_file is None:

            with get_session() as session:
                new_objects = Objects(
                    name=file_name,
                    bucket_id=bucket_data.id
                )
                session.add(new_objects)
                session.commit()
                session.refresh(new_objects)
                return new_objects
        else:
            with get_session() as session:
                _, object_data_file = search_file
                object_data_file.last_modified = datetime.now(timezone.utc)
                session.add(object_data_file)
                session.commit()
                session.refresh(object_data_file)

    def delete_file(self, bucket_name: str, file_name: str, owner_id: uuid.UUID):

        search_file = self.get_file(
            bucket_name=bucket_name,
            file_name=file_name,
            owner_id=owner_id
        )

        if search_file is None:
            raise FileNotFoundError(f"File {file_name} not found")

        _, file_obj = search_file
        with get_session() as session:
            session.delete(file_obj)
            session.commit()