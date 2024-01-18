import time
import json
import os
import boto3
from botocore.exceptions import ClientError


class History:
    _session_id = None

    def __init__(self, session_id: str):
        self._session_id = session_id

    def get(self, limit: int = 10, offset: int = 0):
        try:
            payload = {
                "session_id": self._session_id,
                "limit": limit,
                "offset": offset,
            }
            response = boto3.client("lambda").invoke(
                FunctionName=os.environ.get("MEMORY_LAMBDA_NAME"),
                InvocationType="RequestResponse",
                Payload=json.dumps(payload),
            )
            return response
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return e.response["Error"]["Message"]

    def add(self, human_message: str, assistant_message: str):
        try:
            table = boto3.resource("dynamodb").Table(os.environ.get("DYNAMO_TABLE"))  # type: ignore
            item = {
                "SessionId": self._session_id,
                "HumanMessage": human_message,
                "AssistantMessage": assistant_message,
                "SK": int(time.time()),
            }
            table.put_item(Item=item)
            return item
        except ClientError as e:
            print(e.response["Error"]["Message"])
            return e.response["Error"]["Message"]