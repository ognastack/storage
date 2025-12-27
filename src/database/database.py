import logging
import uuid
import requests
from typing import Optional

from datetime import datetime, timezone
from config.settings import settings

from src.schema.requests.storage import Bucket as BaseBucket, FileObject
from src.core.exceptions import BucketNotFound

import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseEngine:

    def __init__(self, token):

        self.graphql_endpoint = f"{settings.GRAPHQL_HOST}/{settings.GRAPHQL_ENDPOINT}"

        self.session = requests.session()

        logger.error({
            "Authorization": f"Bearer {token}"
        })
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })

    def get_bucket_by_id(self, bucket_id: str) -> Optional[BaseBucket]:
        query = """
            query GetBucket($name: String!) {
              storage_bucket(where: {
                name: {_eq: $name}
              }, limit: 1) {
                id
                name
                owner
              }
            }
        """

        variables = {
            "name": bucket_id
        }

        response = self.session.post(
            self.graphql_endpoint,
            json={'query': query, 'variables': variables}
        )

        result = response.json()

        # It is good practice to check for the 'errors' key in the JSON
        if "errors" in result:
            logger.error(f"GraphQL Errors: {result['errors']}")
            return None

        data = result.get('data', {}).get('storage_bucket', [])

        return BaseBucket(**data[0]) if data else None

    def get_bucket_by_id_user(self, bucket_name: str, owner_id: uuid.UUID) -> Optional[BaseBucket]:
        query = """
            query GetBucket($name: String!, $owner: uuid!) {
              storage_bucket(where: {
                name: {_eq: $name}, 
                owner: {_eq: $owner}
              }, limit: 1) {
                id
                name
                owner
              }
            }
        """

        variables = {
            "name": bucket_name,
            "owner": str(owner_id)
        }

        response = self.session.post(
            self.graphql_endpoint,
            json={'query': query, 'variables': variables}
        )

        result = response.json()

        # It is good practice to check for the 'errors' key in the JSON
        if "errors" in result:
            logger.error(f"GraphQL Errors: {result['errors']}")
            return None

        data = result.get('data', {}).get('storage_bucket', [])

        return BaseBucket(**data[0]) if data else None

    def create_bucket(self, bucket_data: BaseBucket, user_id: uuid.UUID) -> Optional[BaseBucket]:
        mutation = """
        mutation CreateBucket($name: String!) {
          insert_storage_bucket_one(object: {
            name: $name
          }) {
            id
            name
            owner
          }
        }
        """

        variables = {
            "name": bucket_data.name
        }

        logger.warning(f"graph ql url {self.graphql_endpoint}")

        response = self.session.post(
            self.graphql_endpoint,
            json={'query': mutation, 'variables': variables}
        )

        logger.error(response.json())
        result = response.json()
        if "errors" in result:
            raise Exception(f"Mutation failed: {result['errors']}")

        data = result.get('data', {}).get('insert_storage_bucket_one')
        return BaseBucket(**data) if data else None

    def get_file(self, bucket_name: str, file_name: str, owner_id: uuid.UUID) -> Optional[FileObject]:
        query = """
            query GetFile($bucketName: String!, $fileName: String!) {
              storage_bucket(where: {
                name: {_eq: $bucketName}
              }, limit: 1) {
                objects(where: {name: {_eq: $fileName}}, limit: 1) {
                    bucket_id
                    id
                    last_modified
                    name
                }
              }
            }
        """

        variables = {
            "bucketName": bucket_name,
            "fileName": file_name
        }

        response = self.session.post(
            self.graphql_endpoint,
            json={'query': query, 'variables': variables}
        )

        result = response.json()
        logger.warning(result)
        if "errors" in result:
            logger.error(f"Hasura Error: {result['errors']}")
            return None

        # Navigate the nested data: bucket -> objects -> first item
        data = result.get('data', {}).get('storage_bucket', [])
        if data and data[0].get('objects'):
            file_data = data[0]['objects'][0]
            return FileObject(**file_data)

        return None

    def get_files(self, bucket_name: str, owner_id: uuid.UUID) -> list[FileObject]:
        query = """
            query GetFile($bucketName: String!) {
              storage_bucket(
                where: { name: { _eq: $bucketName } }
                limit: 1
              ) {
                objects {
                  id
                  name
                  bucket_id
                  last_modified
                }
              }
            }
        """

        variables = {
            "bucketName": bucket_name
        }

        response = self.session.post(
            self.graphql_endpoint,
            json={'query': query, 'variables': variables}
        )

        result = response.json()
        logger.warning(result)
        if "errors" in result:
            logger.error(f"Hasura Error: {result['errors']}")
            raise Exception(str(result['errors']))

        # Navigate the nested data: bucket -> objects -> first item
        results: list[FileObject] = []
        data = result.get('data', {}).get('storage_bucket', [])
        if data and data[0].get('objects'):
            for fdata in data[0]['objects']:
                results.append(FileObject(**fdata))
        return results

    def get_buckets(self, owner_id: uuid.UUID) -> list[BaseBucket]:
        query = """
            query GetFile {
              storage_bucket {
                owner
                name
                id
              }
            }
        """
        response = self.session.post(
            self.graphql_endpoint,
            json={'query': query}
        )

        result = response.json()
        logger.warning(result)
        if "errors" in result:
            logger.error(f"Hasura Error: {result['errors']}")
            raise Exception(str(result['errors']))

        # Navigate the nested data: bucket -> objects -> first item
        results: list[BaseBucket] = []
        all_buckets = result.get('data', {}).get('storage_bucket', [])

        for bucket in all_buckets:
            results.append(BaseBucket(**bucket))
        return results

    def create_file(self, bucket_name: str, file_name: str, owner_id: uuid.UUID):
        bucket_data = self.get_bucket_by_id_user(bucket_name, owner_id)
        if not bucket_data:
            raise BucketNotFound(bucket_name)

        # Note the singular 'object' in the mutation name
        mutation = """
            mutation UpsertFile($bucketId: uuid!, $name: String!, $now: timestamptz!) {
              insert_storage_object_one(
                object: {
                  bucket_id: $bucketId,
                  name: $name,
                  last_modified: $now
                },
                on_conflict: {
                  constraint: object_bucket_id_name_key, 
                  update_columns: [last_modified]
                }
              ) {
                id
                name
                last_modified
              }
            }
        """

        variables = {
            "bucketId": str(bucket_data.id),
            "name": file_name,
            "now": datetime.now(timezone.utc).isoformat()
        }

        response = self.session.post(
            self.graphql_endpoint,
            json={'query': mutation, 'variables': variables}
        )

        result = response.json()
        if "errors" in result:
            # If it still fails, check the constraint name in Postgres
            raise Exception(f"Upsert failed: {result['errors']}")

        return result.get('data', {}).get('insert_storage_object_one')

    def delete_file(self, bucket_name: str, file_name: str, owner_id: uuid.UUID):
        mutation = """
            mutation DeleteFile($fileName: String!, $bucketName: String!) {
              delete_storage_object(where: {
                name: {_eq: $fileName},
                bucket: {
                  name: {_eq: $bucketName}
                }
              }) {
                affected_rows
              }
            }
        """

        variables = {
            "fileName": file_name,
            "bucketName": bucket_name
        }

        response = self.session.post(
            self.graphql_endpoint,
            json={'query': mutation, 'variables': variables},
        )

        result = response.json()
        if "errors" in result:
            raise Exception(f"Delete failed: {result['errors']}")

        # Check if anything was actually deleted
        affected_rows = result.get('data', {}).get('delete_storage_object', {}).get('affected_rows', 0)

        if affected_rows == 0:
            raise FileNotFoundError(f"File {file_name} not found or unauthorized")

        return True
