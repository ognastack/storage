import logging
import uuid

from sqlmodel import Session, SQLModel, create_engine, select
from config.settings import settings
from sqlalchemy import text
from contextlib import contextmanager

from src.database.storage.bucket import Bucket
from src.schema.requests.storage import Bucket as BaseBucket

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

    def get_bucket_by_id_user(self, bucket_name: str, owner_id: uuid.UUID)->Bucket:
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
