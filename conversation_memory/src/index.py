from boto3.dynamodb.conditions import Key
import boto3
from botocore.exceptions import ClientError
import os
import json

dynamodb = boto3.resource("dynamodb")
PROMPT_TEMPLATE = """\n\nHuman:{}\n\nAssistant:{}"""


def lambda_handler(event, context):
    table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))  # type: ignore
    print(event)
    payload = json.loads(event["body"])
    session_id = payload["session_id"]
    limit = payload["limit"]
    try:
        response = table.query(
            KeyConditionExpression=Key("SessionId").eq(session_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return {"statusCode": 200, "body": json.dumps(response["Items"])}
    except ClientError as e:
        return {"statusCode": 200, "body": e.response["Error"]["Message"]}
