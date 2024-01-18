from boto3.dynamodb.conditions import Key
import boto3
from botocore.exceptions import ClientError
import os
import json

dynamodb = boto3.resource('dynamodb')
PROMPT_TEMPLATE = """\n\nHuman:{}\n\nAssistant:{}"""


def lambda_handler(event, context):
    table = dynamodb.Table(os.getenv('DYNAMO_TABLE'))
    session_id = event['session_id']
    human_message = event['human_message']
    assistant_message = event['assistant_message']
    sk = event['sk']
    try:
        item = {
            'SessionId': session_id,
            'SK': sk,
            'HumanMessage': human_message,
            'AssistantMessage': assistant_message
        }
        print(item)
        table.put_item(Item=item)

        # Query the last 10 items for the same sessionId
        response = table.query(
            KeyConditionExpression=Key('SessionId').eq(session_id),
            ScanIndexForward=False,
            Limit=10
        )
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }
    except ClientError as e:
        return {
            'statusCode': 200,
            'body': e.response['Error']['Message']
        }
