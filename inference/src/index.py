import json
import os
import boto3
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from botocore.exceptions import ClientError

bedrock = boto3.client("bedrock-runtime")


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
        return secret
    except ClientError as e:
        print(e)
        raise (e)


def get_connection_string():
    PGVECTOR_DRIVER = os.environ.get("PGVECTOR_DRIVER", "psycopg2")
    PGVECTOR_HOST = os.environ.get("PGVECTOR_HOST", "localhost")
    PGVECTOR_PORT = int(os.environ.get("PGVECTOR_PORT", 5432))
    PGVECTOR_DATABASE = os.environ.get("PGVECTOR_DATABASE", "postgres")
    PGVECTOR_USER = os.environ.get("PGVECTOR_USER", "postgres")
    PGVECTOR_PASSWORD = get_secret()
    CONNECTION_STRING = PGVector.connection_string_from_db_params(
        driver=PGVECTOR_DRIVER,
        host=PGVECTOR_HOST,
        port=PGVECTOR_PORT,
        database=PGVECTOR_DATABASE,
        user=PGVECTOR_USER,
        password=PGVECTOR_PASSWORD,
    )
    return CONNECTION_STRING


def get_vector_store(collection_name="main_collection"):
    bedrock = boto3.client('bedrock-runtime')
    return PGVector(connection_string=get_connection_string(),
                    collection_name=collection_name,
                    embedding_function=BedrockEmbeddings(client=bedrock))


def prepare_prompt(query, docs):
    separator = ".\n"
    context = separator.join(map(lambda x: x[0].page_content, docs))
    final_prompt = f"""\n\nHuman: Answer in french the following question : {query}, using the following context :{context}.
    \n\nAssistant:"""
    print(final_prompt)
    return final_prompt


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


def dummy_invoke_model():
    return "this is a dummy response"


def lambda_handler(event, context):
    try:
        vector_store = get_vector_store(collection_name="main_collection")
        print("vector store retrieved")
        print(event)
        query = event['query']
        max_tokens_to_sample = event['max_tokens']
        dev_mode = event.get('dev_mode', True)

        if not dev_mode:
            docs = vector_store.similarity_search_with_relevance_scores(
                query=query, k=5)
            response = invoke_model(query, docs, max_tokens_to_sample)
        else:
            response = dummy_invoke_model()

        return {
            "statusCode": 200,
            "body": json.dumps(response)
        }
    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "body": json.dumps(e)
        }

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
