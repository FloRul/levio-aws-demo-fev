import json
import os
import boto3
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores.pgvector import PGVector
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError, BotoCoreError


def test_connectivity():
    region_name = "us-west-2"
    session = boto3.Session()

    # Test connectivity to Secrets Manager
    try:
        print("Connecting to Secrets Manager...")
        get_secret()
    except (NoCredentialsError, BotoCoreError) as e:
        print("Failed to connect to Secrets Manager.")
        raise e

    # Test connectivity to RDS
    try:
        print("Connecting to RDS...")
        rds_client = session.client(
            service_name="rds", region_name=region_name)
        rds_client.describe_db_instances(MaxRecords=1)
        print("Connected to RDS successfully.")
    except (NoCredentialsError, BotoCoreError) as e:
        print("Failed to connect to RDS.")
        raise e


def get_secret():
    secret_name = os.environ.get("PGVECTOR_PASSWORD_SECRET_NAME")
    region_name = "us-west-2"
    session = boto3.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response["SecretString"]
        print("Got secret successfully.")
        return secret
    except ClientError as e:
        print(e)
        raise (e)


bedrock = boto3.client("bedrock-runtime")

PGVECTOR_DRIVER = os.environ.get("PGVECTOR_DRIVER", "psycopg2")
PGVECTOR_HOST = os.environ.get("PGVECTOR_HOST", "localhost")
PGVECTOR_PORT = int(os.environ.get("PGVECTOR_PORT", 3306))
PGVECTOR_DATABASE = os.environ.get("PGVECTOR_DATABASE", "postgres")
PGVECTOR_USER = os.environ.get("PGVECTOR_USER", "postgres")
DEV_MODE = os.environ["DEV_MODE"].lower() == "true"
PGVECTOR_PASSWORD = get_secret()

PGVECTOR_COLLECTION_NAME = os.environ.get(
    "COLLECTION_NAME", "emails-embeddings")


CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver=PGVECTOR_DRIVER,
    host=PGVECTOR_HOST,
    port=PGVECTOR_PORT,
    database=PGVECTOR_DATABASE,
    user=os.environ.get("PGVECTOR_USER", "postgres"),
    password=PGVECTOR_PASSWORD,
)

vectorstore = PGVector(connection_string=CONNECTION_STRING,
                       collection_name=PGVECTOR_COLLECTION_NAME,
                       embedding_function=BedrockEmbeddings(client=bedrock))


def prepare_prompt(query, docs):
    separator = ".\n"
    context = separator.join(map(lambda x: x[0].page_content, docs))
    final_prompt = f"""\n\nHuman: You are an agent answering queries related to mailboxes content. 
    Answer in french the following question : {query}, using the following context :{context}.
    \n\nAssistant:"""
    print(final_prompt)
    return final_prompt


def dummy_invoke_model():
    return "this is a dummy response"


def invoke_model(query, docs, max_tokens=512):
    prompt = prepare_prompt(query, docs)
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": 0.3,
    })

    modelId = "anthropic.claude-instant-v1"
    accept = "application/json"
    contentType = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType)
    body = response["body"].read().decode("utf-8")
    json_body = json.loads(body)
    return json_body['completion']


headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


def lambda_handler(event, context):
    test_connectivity()
    # try:
    #     if event['httpMethod'] == 'OPTIONS':
    #         # Respond to preflight request
    #         return {
    #             "statusCode": 200,
    #             "headers": headers,
    #             "isBase64Encoded": False,
    #         }

    #     print(event)
    #     body = json.loads(event['body'])
    #     query = body['query']
    #     max_tokens_to_sample = body['max_tokens']
    #     filter = body.get('filter', '')
    #     docs = vectorstore.similarity_search_with_relevance_scores(
    #         query=query, k=5)

    #     print(f"dev mode:{DEV_MODE}")

    #     if DEV_MODE:
    #         response = dummy_invoke_model()
    #     else:
    #         response = invoke_model(query, docs, max_tokens_to_sample)

    #     result = {
    #         "completion": response,
    #         "docs": json.dumps(list(map(lambda x: {"content": x[0].page_content,
    #                                                "metadata": x[0].metadata,
    #                                                "score": x[1]},
    #                                     docs)))
    #     }
    #     print(result)

    #     return {
    #         "statusCode": 200,
    #         "body": json.dumps(result),
    #         "headers": headers,
    #         "isBase64Encoded": False,
    #     }
    # except Exception as e:
    #     print(f"Error: {str(e)}")
    #     return {
    #         "statusCode": 500,
    #         "Access-Control-Allow-Origin": "*",
    #         "body": json.dumps(str(e)),
    #         "headers": headers
    #     }

# # Retrieve more documents with higher diversity
# # Useful if your dataset has many similar documents
# vectorstore.as_retriever(
#     search_type="mmr",
#     search_kwargs={"k": 6, "lambda_mult": 0.25}
# )

# # Fetch more documents for the MMR algorithm to consider
# # But only return the top 5
# vectorstore.as_retriever(
#     search_type="mmr",
#     search_kwargs={"k": 5, "fetch_k": 50}
# )

# # Only retrieve documents that have a relevance score
# # Above a certain threshold
# vectorstore.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={"score_threshold": 0.8}
# )

# # Only get the single most similar document from the dataset
# vectorstore.as_retriever(search_kwargs={"k": 1})

# # Use a filter to only retrieve documents from a specific paper
# docsearch.as_retriever(
#     search_kwargs={"filter": {"paper_title": "GPT-4 Technical Report"}}
# )
